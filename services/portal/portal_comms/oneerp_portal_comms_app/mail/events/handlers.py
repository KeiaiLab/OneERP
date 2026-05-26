"""사내 메일 이벤트 핸들러 -- 외부 이벤트 구독 처리.

결재 승인/거부 시 관련 사용자에게 알림 메일을 자동 발송한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_portal_comms_app.mail.services.mail_send_service import MailSendService

logger = logging.getLogger(__name__)

_SYSTEM_SENDER = "system@oneerp"
_DEFAULT_TENANT = "T1"


def handle_approval_approved(event_data: dict[str, Any]) -> None:
    """결재 승인 이벤트 처리 -- 요청자에게 승인 알림 메일 발송."""
    requester = event_data.get("requester_id", "")
    doc_id = event_data.get("doc_id", "")
    if not requester:
        logger.warning("결재 승인 이벤트에 requester_id가 없습니다: %s", doc_id)
        return

    tenant_id = event_data.get("tenant_id", _DEFAULT_TENANT)
    svc = MailSendService(tenant_id)
    svc.send_message(
        sender_id=_SYSTEM_SENDER,
        subject=f"[결재 승인] 문서 {doc_id}이(가) 승인되었습니다",
        body=f"문서 {doc_id}에 대한 결재가 승인되었습니다.",
        recipients=[{"user_id": requester, "recipient_type": "to"}],
        priority="normal",
    )
    logger.info("결재 승인 알림 메일 발송: %s → %s", doc_id, requester)


def handle_approval_rejected(event_data: dict[str, Any]) -> None:
    """결재 거부 이벤트 처리 -- 요청자에게 거부 알림 메일 발송."""
    requester = event_data.get("requester_id", "")
    doc_id = event_data.get("doc_id", "")
    if not requester:
        logger.warning("결재 거부 이벤트에 requester_id가 없습니다: %s", doc_id)
        return

    tenant_id = event_data.get("tenant_id", _DEFAULT_TENANT)
    svc = MailSendService(tenant_id)
    svc.send_message(
        sender_id=_SYSTEM_SENDER,
        subject=f"[결재 거부] 문서 {doc_id}이(가) 거부되었습니다",
        body=f"문서 {doc_id}에 대한 결재가 거부되었습니다. 사유를 확인해주세요.",
        recipients=[{"user_id": requester, "recipient_type": "to"}],
        priority="high",
    )
    logger.info("결재 거부 알림 메일 발송: %s → %s", doc_id, requester)
