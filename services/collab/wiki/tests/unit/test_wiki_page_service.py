"""위키 페이지 서비스(WikiPageService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """WikiPageService와 mock Repository를 생성한다."""
    with patch("oneerp_wiki_app.services.wiki_page_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_wiki_app.services.wiki_page_service import WikiPageService

        service = WikiPageService(tenant_id="test-tenant")
    return service, repos


class Test페이지발행:
    """위키 페이지 발행 테스트."""

    def test_초안_발행_성공(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]
        revision_repo = repos["wiki_page_revisions"]

        page_repo.find_by_id.return_value = {
            "_id": "WP-001",
            "title": "테스트 페이지",
            "content": "# 내용",
            "status": "draft",
            "version": 1,
        }

        result = service.publish_page("WP-001", editor_id="USER-001")

        assert result["page_id"] == "WP-001"
        assert result["status"] == "published"
        assert result["version"] == 1
        revision_repo.insert.assert_called_once()
        page_repo.update_by_id.assert_called_once_with(
            "WP-001",
            {"status": "published", "updated_by": "USER-001"},
        )

    def test_이미_발행된_페이지_발행_실패(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_by_id.return_value = {
            "_id": "WP-001",
            "status": "published",
        }

        with pytest.raises(ValueError, match="초안 상태"):
            service.publish_page("WP-001")

    def test_존재하지_않는_페이지_발행_실패(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]
        page_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.publish_page("WP-999")


class Test페이지보관:
    """위키 페이지 보관 테스트."""

    def test_발행된_페이지_보관_성공(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_by_id.return_value = {
            "_id": "WP-001",
            "status": "published",
        }

        result = service.archive_page("WP-001", editor_id="USER-001")

        assert result["page_id"] == "WP-001"
        assert result["status"] == "archived"
        page_repo.update_by_id.assert_called_once_with(
            "WP-001",
            {"status": "archived", "updated_by": "USER-001"},
        )

    def test_초안_페이지_보관_실패(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_by_id.return_value = {
            "_id": "WP-001",
            "status": "draft",
        }

        with pytest.raises(ValueError, match="발행된 페이지만"):
            service.archive_page("WP-001")


class Test리비전생성:
    """위키 페이지 리비전 생성 테스트."""

    def test_새_리비전_생성(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]
        revision_repo = repos["wiki_page_revisions"]

        page_repo.find_by_id.return_value = {
            "_id": "WP-001",
            "title": "기존 제목",
            "content": "기존 내용",
            "version": 2,
        }

        result = service.create_revision(
            "WP-001",
            title="새 제목",
            content="새 내용",
            editor_id="USER-001",
            change_summary="제목 수정",
        )

        assert result["old_version"] == 2
        assert result["new_version"] == 3
        revision_repo.insert.assert_called_once()
        page_repo.update_by_id.assert_called_once_with(
            "WP-001",
            {
                "title": "새 제목",
                "content": "새 내용",
                "version": 3,
                "updated_by": "USER-001",
            },
        )

    def test_존재하지_않는_페이지_리비전_실패(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]
        page_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            service.create_revision("WP-999", title="t", content="c")


class Test페이지트리:
    """위키 페이지 트리 조회 테스트."""

    def test_계층_구조_트리_반환(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = [
            {"_id": "WP-001", "title": "루트1", "parent_page_id": "", "status": "published"},
            {"_id": "WP-002", "title": "하위1", "parent_page_id": "WP-001", "status": "draft"},
            {"_id": "WP-003", "title": "루트2", "parent_page_id": "", "status": "published"},
        ]

        tree = service.get_page_tree("WS-001")

        assert len(tree) == 2  # 루트 노드 2개
        assert tree[0]["title"] == "루트1"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["title"] == "하위1"
        assert tree[1]["title"] == "루트2"
        assert len(tree[1]["children"]) == 0
