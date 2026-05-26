"""위키 검색 서비스(WikiSearchService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """WikiSearchService와 mock Repository를 생성한다."""
    with patch("oneerp_wiki_app.services.wiki_search_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_wiki_app.services.wiki_search_service import WikiSearchService

        service = WikiSearchService(tenant_id="test-tenant")
    return service, repos


class Test페이지검색:
    """위키 페이지 검색 테스트."""

    def test_제목_검색(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = [
            {"_id": "WP-001", "title": "개발 가이드", "tags": ["개발"]},
        ]

        result = service.search_pages("개발")

        assert result["query"] == "개발"
        assert result["total"] == 1
        assert len(result["results"]) == 1
        page_repo.find_many.assert_called_once()

    def test_공간_필터_검색(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = []

        result = service.search_pages("설계", space_id="WS-001")

        assert result["total"] == 0
        # find_many에 space_id 필터가 포함되어야 한다
        call_args = page_repo.find_many.call_args
        assert call_args[0][0]["space_id"] == "WS-001"

    def test_빈_검색어(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = [
            {"_id": "WP-001", "title": "페이지1"},
            {"_id": "WP-002", "title": "페이지2"},
        ]

        result = service.search_pages("")

        assert result["total"] == 2


class Test태그검색:
    """태그 기반 위키 검색 테스트."""

    def test_태그로_페이지_검색(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = [
            {"_id": "WP-001", "title": "API 문서", "tags": ["api", "개발"]},
        ]

        result = service.search_by_tag("api")

        assert len(result) == 1
        call_args = page_repo.find_many.call_args
        assert call_args[0][0]["tags"] == "api"

    def test_태그_없는_결과(self) -> None:
        service, repos = _make_service()
        page_repo = repos["wiki_pages"]

        page_repo.find_many.return_value = []

        result = service.search_by_tag("존재하지않는태그")

        assert len(result) == 0
