"""바로가기 서비스 — 사용자별 바로가기 관리.

BR-PTL-003: 사용자당 최대 20개 바로가기 제한.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MAX_SHORTCUTS_PER_USER = 20


class ShortcutService:
    """바로가기 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._repo = Repository("shortcuts", tenant_id=tenant_id)

    def create_shortcut(
        self,
        *,
        user_id: str,
        shortcut_name: str,
        url: str,
        icon: str = "link",
        color: str = "#1976D2",
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """바로가기를 생성한다.

        BR-PTL-003: 사용자당 최대 20개 제한 검증.

        Raises:
            OneERPError: 바로가기 수가 20개를 초과할 때 (ERR-PTL-003).
        """
        current_count = self._repo.count({"user_id": user_id})
        if current_count >= _MAX_SHORTCUTS_PER_USER:
            raise_bad_request(
                f"바로가기는 최대 {_MAX_SHORTCUTS_PER_USER}개까지 등록할 수 있습니다 "
                f"(현재: {current_count}개) [ERR-PTL-003]"
            )

        shortcut_id = generate_name("SCUT", tenant_id=self._tenant_id)
        doc: dict[str, Any] = {
            "_id": shortcut_id,
            "user_id": user_id,
            "shortcut_name": shortcut_name,
            "url": url,
            "icon": icon,
            "color": color,
            "sort_order": sort_order,
            "click_count": 0,
            "tenant_id": self._tenant_id,
        }
        self._repo.insert(doc)
        logger.info("바로가기 생성: %s (사용자: %s)", shortcut_id, user_id)
        return doc

    def get_user_shortcuts(self, user_id: str) -> list[dict[str, Any]]:
        """사용자의 바로가기 목록을 정렬 순서대로 반환한다."""
        return self._repo.find_many(
            {"user_id": user_id},
            sort=[("sort_order", 1)],
            limit=_MAX_SHORTCUTS_PER_USER,
        )

    def track_click(self, shortcut_id: str, user_id: str) -> dict[str, Any]:
        """바로가기 클릭을 추적한다 — 클릭 수 증가."""
        shortcut = self._repo.find_by_id(shortcut_id)
        if shortcut is None:
            raise_not_found("바로가기를 찾을 수 없습니다 [ERR-PTL-008]")

        if shortcut.get("user_id") != user_id:
            raise_bad_request("다른 사용자의 바로가기에 접근할 수 없습니다 [ERR-PTL-009]")

        new_count = shortcut.get("click_count", 0) + 1
        self._repo.update_by_id(shortcut_id, {"click_count": new_count})
        return {
            "shortcut_id": shortcut_id,
            "click_count": new_count,
            "url": shortcut.get("url", ""),
        }

    def delete_shortcut(self, shortcut_id: str, user_id: str) -> None:
        """바로가기를 삭제한다 — 소유자만 가능."""
        shortcut = self._repo.find_by_id(shortcut_id)
        if shortcut is None:
            raise_not_found("바로가기를 찾을 수 없습니다 [ERR-PTL-008]")

        if shortcut.get("user_id") != user_id:
            raise_bad_request("다른 사용자의 바로가기를 삭제할 수 없습니다 [ERR-PTL-009]")

        self._repo.delete_by_id(shortcut_id)
        logger.info("바로가기 삭제: %s (사용자: %s)", shortcut_id, user_id)
