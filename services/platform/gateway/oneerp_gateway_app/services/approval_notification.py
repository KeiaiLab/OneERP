"""결재 알림 서비스 — 결재자 알림 레코드 생성 (SSE/WebSocket 연동 대비)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_NOTIFICATION_PREFIX = "NOTIF"

# 알림 액션 유형
_ACTION_LABELS: dict[str, str] = {
    "request": "결재 요청",
    "approve": "결재 승인",
    "reject": "결재 반려",
    "delegate": "결재 위임",
    "pre_approve": "전결 처리",
}


class ApprovalNotificationService:
    """결재 알림 생성 서비스.

    notifications 컬렉션에 알림 레코드를 insert하고
    알림 ID를 반환한다. 향후 SSE/WebSocket 연동 시
    이 ID로 실시간 푸시가 가능하다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._notification_repo = Repository("notifications", tenant_id=tenant_id)

    def notify_approver(
        self,
        request_id: str,
        approver_id: str,
        action_type: str,
    ) -> str:
        """BR-APPR-011: 결재자에게 알림 레코드를 생성한다.

        Args:
            request_id: 결재 요청 ID
            approver_id: 수신 대상 결재자 ID
            action_type: 알림 유형 ("request"|"approve"|"reject"|"delegate"|"pre_approve")

        Returns:
            생성된 알림 ID
        """
        notif_id = generate_name(_NOTIFICATION_PREFIX, tenant_id=self._tenant_id)
        action_label = _ACTION_LABELS.get(action_type, action_type)

        notification: dict[str, Any] = {
            "_id": notif_id,
            "tenant_id": self._tenant_id,
            "recipient": approver_id,
            "approval_request_id": request_id,
            "action_type": action_type,
            "title": f"[결재] {action_label}",
            "message": f"결재 요청 '{request_id}'에 대한 {action_label}이 있습니다.",
            "is_read": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._notification_repo.insert(notification)

        logger.info(
            "결재 알림 생성: notif=%s, 수신=%s, 유형=%s",
            notif_id,
            approver_id,
            action_type,
        )
        return notif_id
