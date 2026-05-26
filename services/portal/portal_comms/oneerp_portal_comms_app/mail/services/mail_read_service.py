"""메일 조회 서비스 -- 메일 읽기, 검색, 스레드 조회 비즈니스 로직.

BR-MAIL-030: 수신자별로 읽음/안읽음 상태를 독립적으로 관리한다.
BR-MAIL-031: 수신자가 삭제해도 발신자의 메시지는 유지된다.
BR-MAIL-032: 읽음 표시 시 read_at 타임스탬프를 기록한다.
BR-MAIL-033: 검색은 제목/본문/발신자를 대상으로 한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class MailReadService:
    """메일 조회 비즈니스 로직.

    SC-MAIL-030: 메일 읽기 정상 시나리오
    SC-MAIL-031: 스레드 조회 정상 시나리오
    SC-MAIL-032: 메일 검색 정상 시나리오
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._msg_repo = Repository("mail_messages", tenant_id=tenant_id)
        self._recipient_repo = Repository("mail_recipient_statuses", tenant_id=tenant_id)

    def read_message(
        self,
        *,
        message_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """메일을 읽음으로 표시하고 메시지를 반환한다.

        BR-MAIL-030: 수신자별 읽음 상태 관리.
        BR-MAIL-032: read_at 타임스탬프 기록.

        EX-MAIL-030: 메시지가 존재하지 않으면 에러.
        """
        message = self._msg_repo.find_by_id(message_id)
        if not message:
            raise_not_found(f"메시지 '{message_id}'를 찾을 수 없습니다 [ERR-MAIL-030]")
        message = cast("dict[str, Any]", message)

        # 수신자 상태 업데이트
        statuses = self._recipient_repo.find_many(
            {"message_id": message_id, "user_id": user_id},
            limit=1,
        )
        if statuses:
            status = statuses[0]
            if status.get("status") == "unread":
                now = datetime.now(tz=UTC).isoformat()
                self._recipient_repo.update_by_id(
                    status["_id"],
                    {"status": "read", "read_at": now},
                )
                logger.info("메일 읽음 표시: %s (사용자: %s)", message_id, user_id)

        return message

    def mark_as_unread(
        self,
        *,
        message_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """메일을 안읽음으로 표시한다."""
        statuses = self._recipient_repo.find_many(
            {"message_id": message_id, "user_id": user_id},
            limit=1,
        )
        if not statuses:
            raise_not_found(f"메시지 '{message_id}'의 수신 상태를 찾을 수 없습니다 [ERR-MAIL-030]")

        self._recipient_repo.update_by_id(
            statuses[0]["_id"],
            {"status": "unread", "read_at": None},
        )
        logger.info("메일 안읽음 표시: %s (사용자: %s)", message_id, user_id)
        return {"message_id": message_id, "status": "unread"}

    def get_thread(self, *, thread_id: str) -> list[dict[str, Any]]:
        """스레드에 속한 모든 메시지를 시간순으로 반환한다.

        SC-MAIL-031: 스레드 조회 정상 시나리오.
        """
        return self._msg_repo.find_many(
            {"thread_id": thread_id},
            sort=[("created_at", 1)],
            limit=100,
        )

    def search_messages(
        self,
        *,
        user_id: str,
        query: str,
        folder: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """메일을 검색한다.

        BR-MAIL-033: 제목/본문/발신자를 대상으로 검색한다.
        """
        search_filter: dict[str, Any] = {
            "$or": [
                {"subject": {"$regex": query, "$options": "i"}},
                {"body": {"$regex": query, "$options": "i"}},
                {"sender_id": {"$regex": query, "$options": "i"}},
            ],
        }

        # 수신자가 볼 수 있는 메시지만 필터링
        user_statuses = self._recipient_repo.find_many(
            {"user_id": user_id, "is_deleted": False},
            limit=500,
        )
        message_ids = [s.get("message_id", "") for s in user_statuses]

        # 발신자이거나 수신자인 메시지만
        search_filter = {
            "$and": [
                search_filter,
                {
                    "$or": [
                        {"sender_id": user_id},
                        {"_id": {"$in": message_ids}},
                    ],
                },
            ],
        }

        if folder:
            # 폴더 필터는 발신자 관점에서만
            search_filter["$and"].append({"folder": folder})

        return self._msg_repo.find_many(
            search_filter,
            sort=[("created_at", -1)],
            limit=limit,
        )

    def get_inbox(
        self,
        *,
        user_id: str,
        folder: str = "inbox",
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """사용자의 받은편지함(또는 특정 폴더) 메시지를 조회한다."""
        statuses = self._recipient_repo.find_many(
            {"user_id": user_id, "folder": folder, "is_deleted": False},
            sort=[("created_at", -1)],
            skip=skip,
            limit=limit,
        )

        messages: list[dict[str, Any]] = []
        for s in statuses:
            msg = self._msg_repo.find_by_id(s.get("message_id", ""))
            if msg:
                msg["_recipient_status"] = s.get("status", "unread")
                msg["_is_starred"] = s.get("is_starred", False)
                messages.append(msg)

        return messages

    def toggle_star(
        self,
        *,
        message_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """메일 즐겨찾기를 토글한다."""
        statuses = self._recipient_repo.find_many(
            {"message_id": message_id, "user_id": user_id},
            limit=1,
        )
        if not statuses:
            raise_not_found(f"메시지 '{message_id}'의 수신 상태를 찾을 수 없습니다 [ERR-MAIL-030]")

        current = statuses[0].get("is_starred", False)
        new_starred = not current
        self._recipient_repo.update_by_id(
            statuses[0]["_id"],
            {"is_starred": new_starred},
        )
        logger.info(
            "메일 즐겨찾기 %s: %s (사용자: %s)",
            "설정" if new_starred else "해제",
            message_id,
            user_id,
        )
        return {"message_id": message_id, "is_starred": new_starred}

    def delete_message(
        self,
        *,
        message_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """수신자의 메일을 삭제(소프트 삭제)한다.

        BR-MAIL-031: 수신자가 삭제해도 발신자의 메시지는 유지된다.
        """
        statuses = self._recipient_repo.find_many(
            {"message_id": message_id, "user_id": user_id},
            limit=1,
        )
        if not statuses:
            raise_not_found(f"메시지 '{message_id}'의 수신 상태를 찾을 수 없습니다 [ERR-MAIL-031]")

        now = datetime.now(tz=UTC).isoformat()
        self._recipient_repo.update_by_id(
            statuses[0]["_id"],
            {"is_deleted": True, "status": "deleted", "deleted_at": now, "folder": "trash"},
        )
        logger.info("메일 삭제: %s (사용자: %s)", message_id, user_id)
        return {"message_id": message_id, "deleted": True}
