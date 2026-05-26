"""위키 페이지 관리 서비스 — 발행/보관 워크플로, 버전 관리 비즈니스 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class WikiPageService:
    """위키 페이지 비즈니스 로직.

    페이지 발행, 보관, 버전 생성, 페이지 트리 조회를 담당한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._page_repo = Repository("wiki_pages", tenant_id=tenant_id)
        self._revision_repo = Repository("wiki_page_revisions", tenant_id=tenant_id)
        self._space_repo = Repository("wiki_spaces", tenant_id=tenant_id)

    def publish_page(self, page_id: str, editor_id: str = "") -> dict[str, Any]:
        """위키 페이지를 발행한다.

        draft 상태의 페이지만 발행 가능하며,
        발행 시 현재 콘텐츠를 리비전으로 저장한다.

        Args:
            page_id: 위키 페이지 ID
            editor_id: 편집자 ID

        Returns:
            발행 결과

        Raises:
            ValueError: 페이지가 없거나 draft 상태가 아닐 때
        """
        page = self._page_repo.find_by_id(page_id)
        if not page:
            msg = f"위키 페이지 '{page_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        if page.get("status") != "draft":
            msg = "초안 상태의 페이지만 발행할 수 있습니다"
            raise ValueError(msg)

        # 리비전 생성
        version = int(page.get("version", 1))
        self._revision_repo.insert(
            {
                "page_id": page_id,
                "version": version,
                "title": page.get("title", ""),
                "content": page.get("content", ""),
                "editor_id": editor_id,
                "change_summary": "페이지 발행",
                "tenant_id": self._tenant_id,
            }
        )

        # 페이지 상태 업데이트
        self._page_repo.update_by_id(
            page_id,
            {"status": "published", "updated_by": editor_id},
        )

        logger.info("위키 페이지 발행: %s (v%d)", page_id, version)
        return {"page_id": page_id, "status": "published", "version": version}

    def get_page(self, page_id: str) -> dict[str, Any]:
        """페이지를 조회하고 없으면 404를 발생시킨다."""
        page = self._page_repo.find_by_id(page_id)
        if not page:
            raise_not_found("위키 페이지를 찾을 수 없습니다")
        return page

    def archive_page(self, page_id: str, editor_id: str = "") -> dict[str, Any]:
        """위키 페이지를 보관 처리한다.

        published 상태의 페이지만 보관 가능하다.

        Args:
            page_id: 위키 페이지 ID
            editor_id: 편집자 ID

        Returns:
            보관 결과

        Raises:
            ValueError: 페이지가 없거나 published 상태가 아닐 때
        """
        page = self._page_repo.find_by_id(page_id)
        if not page:
            msg = f"위키 페이지 '{page_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        if page.get("status") != "published":
            msg = "발행된 페이지만 보관할 수 있습니다"
            raise ValueError(msg)

        self._page_repo.update_by_id(
            page_id,
            {"status": "archived", "updated_by": editor_id},
        )

        logger.info("위키 페이지 보관: %s", page_id)
        return {"page_id": page_id, "status": "archived"}

    def create_revision(
        self,
        page_id: str,
        title: str,
        content: str,
        editor_id: str = "",
        change_summary: str = "",
    ) -> dict[str, Any]:
        """위키 페이지의 새 리비전을 생성한다.

        페이지 본문을 업데이트하고 이전 버전을 리비전에 보관한다.

        Args:
            page_id: 위키 페이지 ID
            title: 새 제목
            content: 새 본문
            editor_id: 편집자 ID
            change_summary: 변경 요약

        Returns:
            새 리비전 정보
        """
        page = self._page_repo.find_by_id(page_id)
        if not page:
            msg = f"위키 페이지 '{page_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        current_version = int(page.get("version", 1))
        new_version = current_version + 1

        # 현재 버전을 리비전으로 저장
        self._revision_repo.insert(
            {
                "page_id": page_id,
                "version": current_version,
                "title": page.get("title", ""),
                "content": page.get("content", ""),
                "editor_id": editor_id,
                "change_summary": change_summary,
                "tenant_id": self._tenant_id,
            }
        )

        # 페이지 본문 및 버전 업데이트
        self._page_repo.update_by_id(
            page_id,
            {
                "title": title,
                "content": content,
                "version": new_version,
                "updated_by": editor_id,
            },
        )

        logger.info(
            "위키 페이지 리비전 생성: %s (v%d → v%d)", page_id, current_version, new_version
        )
        return {
            "page_id": page_id,
            "old_version": current_version,
            "new_version": new_version,
        }

    def get_page_tree(self, space_id: str) -> list[dict[str, Any]]:
        """위키 공간의 페이지 트리를 조회한다.

        최상위 페이지(parent_page_id가 빈 문자열)와 하위 페이지를
        계층 구조로 반환한다.

        Args:
            space_id: 위키 공간 ID

        Returns:
            페이지 트리 목록
        """
        pages = self._page_repo.find_many(
            {"space_id": space_id},
            limit=1000,
        )

        # parent_page_id 별 그룹핑
        children_map: dict[str, list[dict[str, Any]]] = {}
        for page in pages:
            parent_id = page.get("parent_page_id", "")
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(page)

        def _build_tree(parent_id: str) -> list[dict[str, Any]]:
            nodes = children_map.get(parent_id, [])
            result: list[dict[str, Any]] = []
            for node in nodes:
                node_id = node.get("_id", "")
                result.append(
                    {
                        "id": node_id,
                        "title": node.get("title", ""),
                        "status": node.get("status", "draft"),
                        "children": _build_tree(node_id),
                    }
                )
            return result

        return _build_tree("")
