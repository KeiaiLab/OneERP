"""프레즌스 서비스 — 사용자 온라인 상태 관리 비즈니스 로직.

BR-MSG-040: 프레즌스 상태는 online/offline/away/dnd 중 하나.
BR-MSG-041: 상태 메시지는 200자 이내.
BR-MSG-042: 오프라인 전환 시 last_seen_at이 자동 기록된다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, ClassVar

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PresenceService:
    """프레즌스 비즈니스 로직."""

    VALID_STATUSES: ClassVar[set[str]] = {"online", "offline", "away", "dnd"}

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._presence_repo = Repository("user_presences", tenant_id=tenant_id)

    def update_presence(
        self,
        user_id: str,
        status: str,
        status_message: str = "",
    ) -> dict[str, Any]:
        """사용자 프레즌스를 업데이트한다.

        BR-MSG-040: 유효한 상태 검증.
        BR-MSG-041: 상태 메시지 길이 검증.
        BR-MSG-042: 오프라인 전환 시 last_seen_at 기록.

        Raises:
            ValueError: 유효하지 않은 상태 또는 메시지 초과 (ERR-MSG-040, ERR-MSG-041)
        """
        # BR-MSG-040: 상태 검증
        if status not in self.VALID_STATUSES:
            msg = f"ERR-MSG-040: 유효하지 않은 프레즌스 상태입니다: {status}"
            raise ValueError(msg)

        # BR-MSG-041: 상태 메시지 길이 검증
        if len(status_message) > 200:
            msg = "ERR-MSG-041: 상태 메시지는 200자 이내여야 합니다"
            raise ValueError(msg)

        # 기존 프레즌스 조회
        existing = self._presence_repo.find_many(
            {"user_id": user_id},
            limit=1,
        )

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": status,
            "status_message": status_message,
        }

        # BR-MSG-042: 오프라인 전환 시 last_seen_at 기록
        if status == "offline":
            update_data["last_seen_at"] = now

        if existing:
            presence_id = existing[0].get("_id", "")
            self._presence_repo.update_by_id(presence_id, update_data)
        else:
            presence_id = generate_name("PRS", tenant_id=self._tenant_id)
            self._presence_repo.insert(
                {
                    "_id": presence_id,
                    "user_id": user_id,
                    **update_data,
                    "last_seen_at": now if status == "offline" else None,
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info("프레즌스 업데이트: %s → %s", user_id, status)
        return {
            "user_id": user_id,
            "status": status,
            "status_message": status_message,
        }

    def get_presence(self, user_id: str) -> dict[str, Any]:
        """사용자 프레즌스를 조회한다.

        Returns:
            프레즌스 정보 (미존재 시 offline 기본값)
        """
        existing = self._presence_repo.find_many(
            {"user_id": user_id},
            limit=1,
        )

        if existing:
            presence = existing[0]
            return {
                "user_id": user_id,
                "status": presence.get("status", "offline"),
                "status_message": presence.get("status_message", ""),
                "last_seen_at": presence.get("last_seen_at"),
            }

        return {
            "user_id": user_id,
            "status": "offline",
            "status_message": "",
            "last_seen_at": None,
        }

    def get_bulk_presence(self, user_ids: list[str]) -> dict[str, Any]:
        """여러 사용자의 프레즌스를 일괄 조회한다.

        Returns:
            사용자별 프레즌스 목록
        """
        results = [self.get_presence(uid) for uid in user_ids]
        return {"presences": results, "total": len(results)}
