"""알림 서비스 — 알림 생성, 읽음 처리, 일괄 읽음 비즈니스 로직.

BR-MSG-020: 알림 유형은 mention/reply/channel_invite/system 중 하나.
BR-MSG-021: 읽음 처리된 알림은 다시 미읽음으로 변경 불가.
BR-MSG-022: 알림은 해당 사용자만 읽음 처리 가능.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._notification_repo = Repository("notifications", tenant_id=tenant_id)

    def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str = "",
        reference_id: str = "",
        channel_id: str = "",
    ) -> dict[str, Any]:
        """알림을 생성한다.

        BR-MSG-020: 알림 유형 검증.

        Raises:
            ValueError: 유효하지 않은 알림 유형 (ERR-MSG-020)
        """
        valid_types = {"mention", "reply", "channel_invite", "system"}
        if notification_type not in valid_types:
            msg = f"ERR-MSG-020: 유효하지 않은 알림 유형입니다: {notification_type}"
            raise ValueError(msg)

        notification_id = generate_name("NTF", tenant_id=self._tenant_id)
        self._notification_repo.insert(
            {
                "_id": notification_id,
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "body": body,
                "reference_id": reference_id,
                "channel_id": channel_id,
                "is_read": False,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "알림 생성: %s (유형: %s, 대상: %s)", notification_id, notification_type, user_id
        )
        return {
            "notification_id": notification_id,
            "user_id": user_id,
            "notification_type": notification_type,
            "is_read": False,
        }

    def mark_as_read(
        self,
        notification_id: str,
        requester_id: str,
    ) -> dict[str, Any]:
        """알림을 읽음 처리한다.

        BR-MSG-021: 이미 읽은 알림은 다시 미읽음 불가.
        BR-MSG-022: 해당 사용자만 읽음 처리 가능.

        Raises:
            ValueError: 알림 미존재 또는 권한 없음 (ERR-MSG-021, ERR-MSG-022)
        """
        notification = self._notification_repo.find_by_id(notification_id)
        if not notification:
            msg = f"ERR-MSG-030: 알림 '{notification_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        if notification.get("user_id") != requester_id:
            msg = "ERR-MSG-022: 본인의 알림만 읽음 처리할 수 있습니다"
            raise ValueError(msg)

        if notification.get("is_read"):
            return {"notification_id": notification_id, "already_read": True}

        self._notification_repo.update_by_id(notification_id, {"is_read": True})

        logger.info("알림 읽음 처리: %s", notification_id)
        return {"notification_id": notification_id, "already_read": False, "is_read": True}

    def mark_all_as_read(self, user_id: str) -> dict[str, Any]:
        """사용자의 모든 미읽은 알림을 읽음 처리한다.

        Returns:
            읽음 처리된 알림 수
        """
        unread = self._notification_repo.find_many(
            {"user_id": user_id, "is_read": False},
            limit=10000,
        )

        count = 0
        for notification in unread:
            nid = notification.get("_id")
            if nid:
                self._notification_repo.update_by_id(nid, {"is_read": True})
                count += 1

        logger.info("일괄 읽음 처리: 사용자 %s, %d건", user_id, count)
        return {"user_id": user_id, "marked_count": count}

    def get_unread_count(self, user_id: str) -> dict[str, Any]:
        """사용자의 미읽은 알림 수를 반환한다."""
        unread = self._notification_repo.find_many(
            {"user_id": user_id, "is_read": False},
            limit=10000,
        )
        return {"user_id": user_id, "unread_count": len(unread)}
