"""위키 검색 서비스 — 위키 페이지 전문 검색 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class WikiSearchService:
    """위키 검색 비즈니스 로직.

    제목/본문/태그 기반 위키 페이지 검색을 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._page_repo = Repository("wiki_pages", tenant_id=tenant_id)

    def search_pages(
        self,
        query: str,
        space_id: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        """위키 페이지를 검색한다.

        제목과 태그를 기준으로 필터링한다.

        Args:
            query: 검색어
            space_id: 특정 위키 공간 필터 (선택)
            limit: 최대 결과 수

        Returns:
            검색 결과 목록
        """
        filter_query: dict[str, Any] = {}
        if space_id:
            filter_query["space_id"] = space_id

        # 제목 기반 정규식 검색
        if query:
            filter_query["title"] = {"$regex": query, "$options": "i"}

        results = self._page_repo.find_many(filter_query, limit=limit)

        logger.info("위키 검색: '%s' → %d건", query, len(results))
        return {
            "query": query,
            "total": len(results),
            "results": results,
        }

    def search_by_tag(
        self,
        tag: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """태그로 위키 페이지를 검색한다.

        Args:
            tag: 검색할 태그
            limit: 최대 결과 수

        Returns:
            페이지 목록
        """
        results = self._page_repo.find_many(
            {"tags": tag},
            limit=limit,
        )

        logger.info("위키 태그 검색: '%s' → %d건", tag, len(results))
        return results
