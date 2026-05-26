"""문서 분류 서비스 — 계층형 카테고리 관리.

BR-DOC-018: 소속 문서 존재 시 삭제 제한.
BR-DOC-019: 최대 10단계 계층 깊이 제한.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MAX_CATEGORY_DEPTH = 10


class CategoryService:
    """문서 분류 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._cat_repo = Repository("document_categories", tenant_id=tenant_id)
        self._doc_repo = Repository("documents", tenant_id=tenant_id)

    def calculate_depth_and_path(self, parent_category_id: str | None) -> tuple[int, str]:
        """상위 카테고리를 기반으로 깊이와 경로를 계산한다.

        BR-DOC-019: 최대 10단계 계층 깊이 제한.
        """
        if not parent_category_id:
            return 0, "/"

        parent = self._cat_repo.find_by_id(parent_category_id)
        if not parent:
            raise_not_found("상위 문서 분류를 찾을 수 없습니다")

        parent_depth = parent.get("depth", 0)
        new_depth = parent_depth + 1

        if new_depth >= _MAX_CATEGORY_DEPTH:
            raise_unprocessable(
                "ERR-DOC-019",
                f"문서 분류는 최대 {_MAX_CATEGORY_DEPTH}단계까지 지원합니다",
            )

        parent_path = parent.get("path", "/")
        parent_name = parent.get("name", "")
        new_path = f"{parent_path}{parent_name}/"

        return new_depth, new_path

    def validate_delete(self, category_id: str) -> None:
        """카테고리 삭제 전 소속 문서 존재 여부를 확인한다 (BR-DOC-018)."""
        doc_count = self._doc_repo.count({"category": category_id, "is_deleted": False})
        if doc_count > 0:
            raise_bad_request(
                f"{doc_count}건의 소속 문서가 존재하여 삭제할 수 없습니다 [ERR-DOC-018]"
            )

        # 하위 카테고리 확인
        child_count = self._cat_repo.count({"parent_category": category_id, "is_deleted": False})
        if child_count > 0:
            raise_bad_request(f"{child_count}건의 하위 분류가 존재하여 삭제할 수 없습니다")

    def get_category_tree(self, root_id: str | None = None) -> list[dict[str, Any]]:
        """카테고리 트리를 조회한다."""
        query: dict[str, Any] = {"is_deleted": False, "is_active": True}
        if root_id:
            query["parent_category"] = root_id
        else:
            query["parent_category"] = None

        return self._cat_repo.find_many(query, limit=200)
