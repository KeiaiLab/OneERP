"""프로젝트 원가 서비스(ProjectCostService) 단위 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch("oneerp_projects_app.services.project_cost_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_projects_app.services.project_cost_service import ProjectCostService

        service = ProjectCostService(tenant_id="test-tenant")
    return (
        service,
        repos["projects"],
        repos["timesheets"],
        repos["resource_allocations"],
        repos["project_billings"],
    )


class Test프로젝트원가:
    def test_인건비_계산(self) -> None:
        service, proj_repo, _ts, alloc_repo, _billing = _make_service()
        proj_repo.find_by_id.return_value = {"_id": "PRJ-001", "project_name": "ERP 구축"}
        alloc_repo.find_many.return_value = [
            {"hours": 160, "hourly_rate": 100_000},
            {"hours": 80, "hourly_rate": 80_000},
        ]

        result = service.calculate_project_cost("PRJ-001")

        assert result["labor_cost"] == 22_400_000  # 160*100k + 80*80k
        assert result["total_cost"] == 22_400_000

    def test_인건비_자재비_경비_합산(self) -> None:
        service, proj_repo, _ts, alloc_repo, _billing = _make_service()
        proj_repo.find_by_id.return_value = {"_id": "PRJ-001"}
        alloc_repo.find_many.return_value = [
            {"hours": 100, "hourly_rate": 50_000},  # 인건비 5M
            {"type": "material", "amount": 2_000_000},  # 자재비
            {"type": "expense", "amount": 500_000},  # 경비
        ]

        result = service.calculate_project_cost("PRJ-001")

        assert result["labor_cost"] == 5_000_000
        assert result["material_cost"] == 2_000_000
        assert result["expense_cost"] == 500_000
        assert result["total_cost"] == 7_500_000

    def test_프로젝트_미존재(self) -> None:
        service, proj_repo, _ts, _alloc, _billing = _make_service()
        proj_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.calculate_project_cost("PRJ-999")


class Test수익성분석:
    def test_수익률_계산(self) -> None:
        service, proj_repo, _ts, alloc_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {"_id": "PRJ-001"}
        billing_repo.find_many.return_value = [
            {"total": 30_000_000},  # 매출 30M
        ]
        alloc_repo.find_many.return_value = [
            {"hours": 160, "hourly_rate": 100_000},  # 원가 16M
        ]

        result = service.get_profitability("PRJ-001")

        assert result["revenue"] == 30_000_000
        assert result["total_cost"] == 16_000_000
        assert result["profit"] == 14_000_000
        # (30M - 16M) / 30M * 100 = 46.67%
        assert result["margin_percent"] == Decimal("46.67")

    def test_매출_0원이면_수익률_0(self) -> None:
        service, proj_repo, _ts, alloc_repo, billing_repo = _make_service()
        proj_repo.find_by_id.return_value = {"_id": "PRJ-001"}
        billing_repo.find_many.return_value = []
        alloc_repo.find_many.return_value = []

        result = service.get_profitability("PRJ-001")

        assert result["margin_percent"] == 0

    def test_프로젝트_미존재(self) -> None:
        service, proj_repo, _ts, _alloc, _billing = _make_service()
        proj_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.get_profitability("PRJ-999")
