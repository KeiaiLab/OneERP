"""프로젝트 빌링 서비스(ProjectBillingService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_projects_app.services.project_billing_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_projects_app.services.project_billing_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_projects_app.services.project_billing_service import ProjectBillingService

        service = ProjectBillingService(tenant_id="test-tenant")
    return service, repos["projects"], repos["project_billings"], repos["resource_allocations"]


class Test프로젝트청구:
    def test_정상_청구서_생성(self) -> None:
        service, project_repo, billing_repo, alloc_repo = _make_service()
        project_repo.find_by_id.return_value = {"_id": "PRJ-001", "project_name": "ERP 구축"}
        alloc_repo.find_many.return_value = [
            {"resource": "개발자A", "hours": 160, "hourly_rate": 100000, "project": "PRJ-001"},
            {"resource": "개발자B", "hours": 80, "hourly_rate": 80000, "project": "PRJ-001"},
        ]

        result = service.generate_billing("PRJ-001", "2026-03")

        assert result["billing_id"] == "PBL-001"
        assert result["total"] == 22400000  # 160*100000 + 80*80000
        assert result["line_item_count"] == 2
        billing_repo.insert.assert_called_once()

    def test_프로젝트_미존재_에러(self) -> None:
        service, project_repo, _billing, _alloc = _make_service()
        project_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.generate_billing("PRJ-999", "2026-03")

    def test_배정없으면_0원(self) -> None:
        service, project_repo, _billing, alloc_repo = _make_service()
        project_repo.find_by_id.return_value = {"_id": "PRJ-001"}
        alloc_repo.find_many.return_value = []

        result = service.generate_billing("PRJ-001", "2026-03")

        assert result["total"] == 0
        assert result["line_item_count"] == 0
