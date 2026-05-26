"""검색 서비스 — 통합 검색, 권한 필터링, 자동완성.

BR-PTL-009: 검색 결과 권한 필터링.
BR-PTL-015: 2자 이상 자동완성.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MIN_AUTOCOMPLETE_LENGTH = 2
_MAX_SEARCH_RESULTS = 50
_MAX_AUTOCOMPLETE_RESULTS = 10


class SearchService:
    """통합 검색 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._index_repo = Repository("search_indices", tenant_id=tenant_id)

    def search(
        self,
        query: str,
        *,
        user_permissions: list[str] | None = None,
        module: str = "",
        limit: int = _MAX_SEARCH_RESULTS,
    ) -> list[dict[str, Any]]:
        """통합 검색을 수행한다.

        BR-PTL-009: 사용자 권한에 따라 결과를 필터링한다.

        Args:
            query: 검색 쿼리 문자열.
            user_permissions: 사용자 보유 권한 목록.
            module: 특정 모듈 필터 (빈 문자열이면 전체).
            limit: 최대 결과 수.

        Returns:
            권한 필터링된 검색 결과 목록.
        """
        if not query or len(query.strip()) < 1:
            raise_bad_request("검색어를 입력해주세요 [ERR-PTL-013]")

        query = query.strip()

        # 검색 조건 구성 (제목/내용/키워드에서 검색)
        filter_query: dict[str, Any] = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"keywords": {"$elemMatch": {"$regex": query, "$options": "i"}}},
            ],
        }

        if module:
            filter_query["module"] = module

        results = self._index_repo.find_many(filter_query, limit=limit)

        # BR-PTL-009: 권한 필터링
        filtered = self._filter_by_permission(results, user_permissions)

        logger.info(
            "검색 수행: query='%s', 결과=%d/%d",
            query,
            len(filtered),
            len(results),
        )
        return filtered

    def autocomplete(
        self,
        query: str,
        *,
        user_permissions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """BR-PTL-015: 자동완성을 수행한다 — 2자 이상 필요.

        Args:
            query: 입력 문자열.
            user_permissions: 사용자 보유 권한 목록.

        Returns:
            자동완성 제안 목록 (제목, URL).

        Raises:
            OneERPError: 입력이 2자 미만일 때 (ERR-PTL-014).
        """
        if not query or len(query.strip()) < _MIN_AUTOCOMPLETE_LENGTH:
            raise_bad_request(
                f"자동완성은 {_MIN_AUTOCOMPLETE_LENGTH}자 이상 입력해야 합니다 [ERR-PTL-014]"
            )

        query = query.strip()
        filter_query: dict[str, Any] = {
            "title": {"$regex": f"^{query}", "$options": "i"},
        }

        results = self._index_repo.find_many(
            filter_query,
            limit=_MAX_AUTOCOMPLETE_RESULTS,
        )

        # 권한 필터링
        filtered = self._filter_by_permission(results, user_permissions)

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "doc_type": r.get("doc_type", ""),
                "module": r.get("module", ""),
            }
            for r in filtered
        ]

    @staticmethod
    def _filter_by_permission(
        results: list[dict[str, Any]],
        user_permissions: list[str] | None,
    ) -> list[dict[str, Any]]:
        """BR-PTL-009: 검색 결과를 사용자 권한으로 필터링한다."""
        if user_permissions is None:
            return results

        # 와일드카드 권한이 있으면 모든 결과 통과
        if "*:*" in user_permissions:
            return results

        filtered: list[dict[str, Any]] = []
        for result in results:
            required = result.get("required_permission", "")
            if not required or required in user_permissions:
                filtered.append(result)
        return filtered
