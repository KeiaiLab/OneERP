"""뉴스/이벤트 서비스 — 상태 머신, 게시 관리.

뉴스/이벤트 상태 전이: draft → published → archived.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 상태 전이 규칙
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["published"],
    "published": ["archived"],
    "archived": [],
}


class NewsService:
    """뉴스/이벤트 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._repo = Repository("news_events", tenant_id=tenant_id)

    def publish(self, news_id: str, *, published_by: str = "") -> dict[str, Any]:
        """뉴스/이벤트를 게시한다 (draft → published)."""
        news = self._get_or_404(news_id)
        self._validate_transition(news, "published")

        now = datetime.now(tz=UTC)
        update_data: dict[str, Any] = {
            "status": "published",
            "published_at": now,
            "published_by": published_by,
        }
        self._repo.update_by_id(news_id, update_data)

        logger.info("뉴스/이벤트 게시: %s", news_id)
        return {**news, **update_data}

    def archive(self, news_id: str) -> dict[str, Any]:
        """뉴스/이벤트를 보관 처리한다 (published → archived)."""
        news = self._get_or_404(news_id)
        self._validate_transition(news, "archived")

        self._repo.update_by_id(news_id, {"status": "archived"})
        logger.info("뉴스/이벤트 보관: %s", news_id)
        return {**news, "status": "archived"}

    def get_published_news(
        self,
        *,
        department: str = "",
        event_type: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """게시된 뉴스/이벤트 목록을 반환한다."""
        filter_query: dict[str, Any] = {"status": "published"}

        if event_type:
            filter_query["event_type"] = event_type

        results = self._repo.find_many(
            filter_query,
            sort=[("published_at", -1)],
            limit=limit,
        )

        # 부서 필터링
        if department:
            results = [
                r
                for r in results
                if not r.get("target_departments") or department in r.get("target_departments", [])
            ]

        return results

    def increment_view_count(self, news_id: str) -> dict[str, Any]:
        """조회 수를 증가시킨다."""
        news = self._get_or_404(news_id)
        new_count = news.get("view_count", 0) + 1
        self._repo.update_by_id(news_id, {"view_count": new_count})
        return {"news_id": news_id, "view_count": new_count}

    def _validate_transition(self, news: dict[str, Any], target_status: str) -> None:
        """상태 전이 유효성을 검증한다."""
        current = news.get("status", "draft")
        allowed = _VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise_bad_request(
                f"'{current}' 상태에서 '{target_status}'로 전이할 수 없습니다 [ERR-PTL-015]"
            )

    def _get_or_404(self, news_id: str) -> dict[str, Any]:
        """뉴스/이벤트를 조회하고 없으면 404를 발생시킨다."""
        news = self._repo.find_by_id(news_id)
        if news is None:
            raise_not_found("뉴스/이벤트를 찾을 수 없습니다 [ERR-PTL-016]")
        return cast("dict[str, Any]", news)
