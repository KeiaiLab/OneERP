"""위키 페이지 커스텀 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oneerp_core.errors import OneERPError


class Test발행라우트:
    """위키 페이지 발행 엔드포인트 테스트."""

    def test_초안_페이지_발행_성공(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.routes.wiki_pages._get_service") as mock_service_factory:
            mock_service = MagicMock()
            mock_service.get_page.return_value = {
                "_id": "WP-001",
                "title": "테스트",
                "content": "# 내용",
                "status": "draft",
                "version": 1,
            }
            mock_service.publish_page.return_value = {
                "page_id": "WP-001",
                "status": "published",
                "version": 1,
            }
            mock_service_factory.return_value = mock_service
            resp = test_client.post("/api/v1/wiki-pages/WP-001/publish")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "published"

    def test_발행된_페이지_재발행_실패(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.routes.wiki_pages._get_service") as mock_service_factory:
            mock_service = MagicMock()
            mock_service.get_page.return_value = {
                "_id": "WP-001",
                "status": "published",
                "tenant_id": "default",
            }
            mock_service_factory.return_value = mock_service

            resp = test_client.post("/api/v1/wiki-pages/WP-001/publish")

        assert resp.status_code == 400

    def test_존재하지_않는_페이지_발행_404(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.routes.wiki_pages._get_service") as mock_service_factory:
            mock_service = MagicMock()
            mock_service.get_page.side_effect = OneERPError(
                status_code=404, error="not_found", detail="위키 페이지를 찾을 수 없습니다"
            )
            mock_service_factory.return_value = mock_service
            resp = test_client.post("/api/v1/wiki-pages/WP-999/publish")

        assert resp.status_code == 404


class Test보관라우트:
    """위키 페이지 보관 엔드포인트 테스트."""

    def test_발행_페이지_보관_성공(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.routes.wiki_pages._get_service") as mock_service_factory:
            mock_service = MagicMock()
            mock_service.get_page.return_value = {
                "_id": "WP-001",
                "status": "published",
                "tenant_id": "default",
            }
            mock_service.archive_page.return_value = {"page_id": "WP-001", "status": "archived"}
            mock_service_factory.return_value = mock_service
            resp = test_client.post("/api/v1/wiki-pages/WP-001/archive")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "archived"

    def test_초안_페이지_보관_실패(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.routes.wiki_pages._get_service") as mock_service_factory:
            mock_service = MagicMock()
            mock_service.get_page.return_value = {
                "_id": "WP-001",
                "status": "draft",
                "tenant_id": "default",
            }
            mock_service_factory.return_value = mock_service

            resp = test_client.post("/api/v1/wiki-pages/WP-001/archive")

        assert resp.status_code == 400


class Test페이지트리라우트:
    """위키 페이지 트리 엔드포인트 테스트."""

    def test_트리_조회(self, mock_collection, test_client) -> None:
        with patch("oneerp_wiki_app.services.wiki_page_service.Repository") as mock_repo_cls:
            mock_svc_repo = MagicMock()
            mock_svc_repo.find_many.return_value = [
                {
                    "_id": "WP-001",
                    "title": "루트",
                    "parent_page_id": "",
                    "status": "published",
                },
            ]

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                return mock_svc_repo

            mock_repo_cls.side_effect = _repo_factory

            resp = test_client.get("/api/v1/wiki-pages/tree/WS-001")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "루트"
