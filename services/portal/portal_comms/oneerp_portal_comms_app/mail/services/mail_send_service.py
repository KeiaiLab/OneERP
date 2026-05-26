"""메일 전송 서비스 -- 메시지 전송, 회신, 전달 비즈니스 로직.

BR-MAIL-001: 메시지는 반드시 발신자와 하나 이상의 수신자를 가져야 한다.
BR-MAIL-002: 제목은 비어있을 수 없다.
BR-MAIL-003: 전송 후 발신자는 내용을 수정할 수 없다.
BR-MAIL-005: 전송 시 수신자별 상태 레코드를 자동 생성한다.
BR-MAIL-006: 회신 시 원본 메시지의 thread_id를 유지한다.
BR-MAIL-007: 전달 시 원본 첨부파일을 복사한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class MailSendService:
    """메일 전송 비즈니스 로직.

    SC-MAIL-001: 메일 전송 정상 시나리오
    SC-MAIL-002: 회신 정상 시나리오
    SC-MAIL-003: 전달 정상 시나리오
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._msg_repo = Repository("mail_messages", tenant_id=tenant_id)
        self._recipient_repo = Repository("mail_recipient_statuses", tenant_id=tenant_id)

    def send_message(
        self,
        *,
        sender_id: str,
        subject: str,
        body: str = "",
        body_html: str = "",
        recipients: list[dict[str, str]],
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        priority: str = "normal",
        attachments: list[dict[str, Any]] | None = None,
        parent_message_id: str | None = None,
        thread_id: str | None = None,
        is_reply: bool = False,
        is_forward: bool = False,
    ) -> dict[str, Any]:
        """메일을 전송한다.

        BR-MAIL-001: 수신자 1명 이상 필수.
        BR-MAIL-002: 제목 필수.
        BR-MAIL-005: 수신자별 상태 레코드 자동 생성.

        Returns:
            전송된 메시지 정보.
        """
        # BR-MAIL-001: 수신자 검증
        if not recipients:
            raise_bad_request("수신자가 최소 1명 이상 필요합니다 [ERR-MAIL-001]")

        # BR-MAIL-002: 제목 검증
        if not subject or not subject.strip():
            raise_bad_request("메일 제목은 비어있을 수 없습니다 [ERR-MAIL-002]")

        now = datetime.now(tz=UTC).isoformat()
        message_id = generate_name("MAIL", tenant_id=self._tenant_id)

        # BR-MAIL-006: 회신 시 thread_id 유지
        resolved_thread_id = thread_id or message_id

        doc = {
            "_id": message_id,
            "subject": subject,
            "body": body,
            "body_html": body_html,
            "sender_id": sender_id,
            "recipients": recipients,
            "cc": cc or [],
            "bcc": bcc or [],
            "priority": priority,
            "status": "sent",
            "attachments": attachments or [],
            "parent_message_id": parent_message_id,
            "thread_id": resolved_thread_id,
            "is_reply": is_reply,
            "is_forward": is_forward,
            "is_read": False,
            "sent_at": now,
            "folder": "sent",
            "tags": [],
            "is_starred": False,
            "is_archived": False,
            "is_deleted": False,
            "docstatus": 1,
        }
        self._msg_repo.insert(doc)

        # BR-MAIL-005: 수신자별 상태 레코드 생성
        all_recipients = [r["user_id"] for r in recipients]
        all_recipients.extend(cc or [])
        all_recipients.extend(bcc or [])

        for user_id in all_recipients:
            status_id = generate_name("MRST", tenant_id=self._tenant_id)
            self._recipient_repo.insert(
                {
                    "_id": status_id,
                    "message_id": message_id,
                    "user_id": user_id,
                    "status": "unread",
                    "folder": "inbox",
                    "is_starred": False,
                    "is_deleted": False,
                }
            )

        logger.info(
            "메일 전송: %s (발신: %s, 수신: %d명)",
            message_id,
            sender_id,
            len(all_recipients),
        )
        return {
            "message_id": message_id,
            "thread_id": resolved_thread_id,
            "recipient_count": len(all_recipients),
            "status": "sent",
        }

    def reply_message(
        self,
        *,
        original_message_id: str,
        sender_id: str,
        body: str = "",
        body_html: str = "",
        reply_all: bool = False,
    ) -> dict[str, Any]:
        """메일에 회신한다.

        BR-MAIL-006: 원본 메시지의 thread_id를 유지한다.

        EX-MAIL-001: 원본 메시지가 존재하지 않으면 에러.
        """
        original = self._msg_repo.find_by_id(original_message_id)
        if not original:
            raise_not_found(
                f"원본 메시지 '{original_message_id}'를 찾을 수 없습니다 [ERR-MAIL-010]"
            )
        original = cast("dict[str, Any]", original)

        # 회신 수신자 결정
        recipients = [{"user_id": original["sender_id"], "recipient_type": "to"}]
        cc: list[str] = []
        if reply_all:
            recipients.extend(
                r for r in original.get("recipients", []) if r.get("user_id") != sender_id
            )
            cc = [c for c in original.get("cc", []) if c != sender_id]

        subject = f"Re: {original.get('subject', '')}"
        thread_id = original.get("thread_id") or original_message_id

        return self.send_message(
            sender_id=sender_id,
            subject=subject,
            body=body,
            body_html=body_html,
            recipients=recipients,
            cc=cc,
            parent_message_id=original_message_id,
            thread_id=thread_id,
            is_reply=True,
        )

    def forward_message(
        self,
        *,
        original_message_id: str,
        sender_id: str,
        forward_to: list[dict[str, str]],
        body: str = "",
        body_html: str = "",
    ) -> dict[str, Any]:
        """메일을 전달한다.

        BR-MAIL-007: 원본 첨부파일을 복사한다.

        EX-MAIL-001: 원본 메시지가 존재하지 않으면 에러.
        """
        original = self._msg_repo.find_by_id(original_message_id)
        if not original:
            raise_not_found(
                f"원본 메시지 '{original_message_id}'를 찾을 수 없습니다 [ERR-MAIL-010]"
            )

        if not forward_to:
            raise_bad_request("전달 대상 수신자가 필요합니다 [ERR-MAIL-001]")

        subject = f"Fwd: {original.get('subject', '')}"
        # BR-MAIL-007: 원본 첨부파일 복사
        attachments = original.get("attachments", [])

        return self.send_message(
            sender_id=sender_id,
            subject=subject,
            body=body,
            body_html=body_html,
            recipients=forward_to,
            attachments=attachments,
            parent_message_id=original_message_id,
            thread_id=original.get("thread_id"),
            is_forward=True,
        )
