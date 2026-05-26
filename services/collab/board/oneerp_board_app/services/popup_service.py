"""팝업 공지 서비스 — 팝업 CRUD, 기간/동시 활성 제한 검증.

BR-BRD-005: 팝업 공지 생성 권한
BR-BRD-012: 팝업 공지 기간 검증
BR-BRD-018: 팝업 공지 동시 활성 제한
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 테넌트당 최대 활성 팝업 수
MAX_ACTIVE_POPUPS = 5
# 팝업 최대 기간(일)
MAX_POPUP_DAYS = 90


class PopupService:
    """팝업 공지 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._popup_repo = Repository("popup_notices", tenant_id=tenant_id)
        self._confirm_repo = Repository("popup_confirm_logs", tenant_id=tenant_id)

    def create_popup(self, data: dict[str, Any]) -> dict[str, Any]:
        """팝업 공지를 생성한다.

        BR-BRD-012: end_at > start_at, 최대 90일.
        BR-BRD-018: 동시 활성 팝업 최대 5개.
        """
        start_at = data.get("start_at")
        end_at = data.get("end_at")

        self._validate_period(start_at, end_at)

        # BR-BRD-018: 동시 활성 팝업 수 확인
        if data.get("is_active", True):
            active_count = self._count_active_popups()
            if active_count >= MAX_ACTIVE_POPUPS:
                raise_unprocessable(
                    "ERR-BRD-040",
                    f"동시에 활성화할 수 있는 팝업 공지는 최대 {MAX_ACTIVE_POPUPS}개입니다",
                )

        popup_id = generate_name("POP", tenant_id=self._tenant_id)
        data["_id"] = popup_id
        data["tenant_id"] = self._tenant_id
        data.setdefault("confirmed_count", 0)
        data.setdefault("total_target_count", 0)

        self._popup_repo.insert(data)
        logger.info("팝업 공지 생성: %s", popup_id)
        return {"_id": popup_id}

    def get_active_popups(self, user_id: str) -> list[dict[str, Any]]:
        """현재 사용자에게 표시할 활성 팝업 목록을 조회한다."""
        now = datetime.now(tz=UTC).isoformat()
        popups = self._popup_repo.find_many(
            {
                "is_active": True,
                "start_at": {"$lte": now},
                "end_at": {"$gte": now},
            },
            sort=[("display_order", 1)],
            limit=MAX_ACTIVE_POPUPS,
        )

        # once 빈도인 팝업 중 이미 확인한 것은 제외
        result: list[dict[str, Any]] = []
        for popup in popups:
            popup_id = popup.get("_id", "")
            show_frequency = popup.get("show_frequency", "once")

            if show_frequency == "once":
                confirmed = self._confirm_repo.find_many(
                    {"popup_id": popup_id, "user_id": user_id},
                    limit=1,
                )
                if confirmed:
                    continue

            result.append(popup)

        return result

    def confirm_popup(self, popup_id: str, user_id: str) -> dict[str, Any]:
        """팝업 공지를 확인 처리한다."""
        popup = self._popup_repo.find_by_id(popup_id)
        if not popup:
            raise_not_found("팝업 공지를 찾을 수 없습니다")

        # 중복 확인 방지
        existing = self._confirm_repo.find_many(
            {"popup_id": popup_id, "user_id": user_id},
            limit=1,
        )
        if not existing:
            self._confirm_repo.insert(
                {
                    "popup_id": popup_id,
                    "user_id": user_id,
                    "confirmed_at": datetime.now(tz=UTC).isoformat(),
                    "tenant_id": self._tenant_id,
                }
            )
            # confirmed_count 증가
            self._popup_repo.update_by_id(
                popup_id,
                {
                    "confirmed_count": popup.get("confirmed_count", 0) + 1,
                },
            )

        logger.info("팝업 확인: %s (사용자: %s)", popup_id, user_id)
        return {"popup_id": popup_id, "user_id": user_id, "status": "confirmed"}

    def _validate_period(self, start_at: Any, end_at: Any) -> None:
        """팝업 기간을 검증한다.

        BR-BRD-012: end_at > start_at, 최대 90일.
        """
        if isinstance(start_at, str):
            start_at = datetime.fromisoformat(start_at)
        if isinstance(end_at, str):
            end_at = datetime.fromisoformat(end_at)

        if not start_at or not end_at:
            return

        if end_at <= start_at:
            raise_unprocessable(
                "ERR-BRD-035",
                "팝업 종료 시각은 시작 시각 이후여야 합니다",
            )

        duration = (end_at - start_at).days
        if duration > MAX_POPUP_DAYS:
            raise_unprocessable(
                "ERR-BRD-036",
                f"팝업 공지 기간은 최대 {MAX_POPUP_DAYS}일입니다",
            )

    def _count_active_popups(self) -> int:
        """활성 팝업 수를 조회한다."""
        now = datetime.now(tz=UTC).isoformat()
        return self._popup_repo.count(
            {
                "is_active": True,
                "start_at": {"$lte": now},
                "end_at": {"$gte": now},
            }
        )
