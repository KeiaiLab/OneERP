"""PlanningOptimizerService 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_advanced_planning_app.services.planning_optimizer_service import (
    PlanningOptimizerService,
)


@pytest.fixture
def mock_repos():
    """Mock Repository 인스턴스를 반환한다."""
    with patch(
        "oneerp_advanced_planning_app.services.planning_optimizer_service.Repository"
    ) as mock_repo_cls:
        demand_repo = MagicMock()
        supply_repo = MagicMock()
        capacity_repo = MagicMock()
        scenario_repo = MagicMock()

        mock_repo_cls.side_effect = [demand_repo, supply_repo, capacity_repo, scenario_repo]

        yield {
            "demand_repo": demand_repo,
            "supply_repo": supply_repo,
            "capacity_repo": capacity_repo,
            "scenario_repo": scenario_repo,
        }


@pytest.fixture
def service(mock_repos):
    """PlanningOptimizerService 인스턴스를 반환한다."""
    return PlanningOptimizerService(tenant_id="test-tenant")


class TestBalanceDemandSupply:
    """수요-공급 밸런싱 테스트."""

    def test_밸런싱_균형(self, service, mock_repos) -> None:
        """수요와 공급이 균형이면 gap=0이다."""
        mock_repos["demand_repo"].find_many.return_value = [
            {"forecast_qty": 100},
            {"forecast_qty": 200},
        ]
        mock_repos["supply_repo"].find_many.return_value = [
            {"planned_qty": 150},
            {"planned_qty": 150},
        ]

        result = service.balance_demand_supply("ITEM-001")

        assert result["total_demand"] == 300.0
        assert result["total_supply"] == 300.0
        assert result["gap"] == 0.0

    def test_밸런싱_공급부족(self, service, mock_repos) -> None:
        """공급이 부족하면 음수 gap과 추가 조달 권고를 반환한다."""
        mock_repos["demand_repo"].find_many.return_value = [
            {"forecast_qty": 500},
        ]
        mock_repos["supply_repo"].find_many.return_value = [
            {"planned_qty": 200},
        ]

        result = service.balance_demand_supply("ITEM-002")

        assert result["gap"] == -300.0
        assert len(result["recommendations"]) > 0
        assert "공급 부족" in result["recommendations"][0]

    def test_밸런싱_과잉공급(self, service, mock_repos) -> None:
        """과잉 공급(20% 초과)이면 재고 과다 권고를 반환한다."""
        mock_repos["demand_repo"].find_many.return_value = [
            {"forecast_qty": 100},
        ]
        mock_repos["supply_repo"].find_many.return_value = [
            {"planned_qty": 200},
        ]

        result = service.balance_demand_supply("ITEM-003")

        assert result["gap"] == 100.0
        assert len(result["recommendations"]) > 0
        assert "과잉 공급" in result["recommendations"][0]

    def test_밸런싱_빈_데이터(self, service, mock_repos) -> None:
        """수요/공급이 없으면 0으로 반환한다."""
        mock_repos["demand_repo"].find_many.return_value = []
        mock_repos["supply_repo"].find_many.return_value = []

        result = service.balance_demand_supply("ITEM-004")

        assert result["total_demand"] == 0.0
        assert result["total_supply"] == 0.0


class TestRunScenario:
    """시나리오 실행 테스트."""

    def test_시나리오_실행_성공(self, service, mock_repos) -> None:
        """시나리오 실행 시 수요 조정과 비용을 계산한다."""
        mock_repos["scenario_repo"].find_by_id.return_value = {
            "_id": "PLS-00001",
            "base_demand_plan_id": "DMP-001",
            "demand_adjustment": 10,  # +10%
            "assumptions": {"unit_cost": 5000},
        }
        mock_repos["demand_repo"].find_by_id.return_value = {
            "_id": "DMP-001",
            "forecast_qty": 1000,
        }

        result = service.run_scenario("PLS-00001")

        assert result["status"] == "completed"
        assert result["base_qty"] == 1000.0
        assert result["adjusted_qty"] == 1100.0  # 1000 * 1.10
        assert result["estimated_cost"] == 5500000.0  # 1100 * 5000

    def test_미존재_시나리오_에러(self, service, mock_repos) -> None:
        """존재하지 않는 시나리오이면 ValueError가 발생한다."""
        mock_repos["scenario_repo"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="계획 시나리오를 찾을 수 없습니다"):
            service.run_scenario("PLS-99999")


class TestCalculateUtilization:
    """생산능력 가용률 계산 테스트."""

    def test_가용률_계산(self, service, mock_repos) -> None:
        """available_hours와 planned_hours로 가용률을 계산한다."""
        mock_repos["capacity_repo"].find_many.return_value = [
            {"workstation": "WS-001", "available_hours": 160, "planned_hours": 120},
            {"workstation": "WS-002", "available_hours": 160, "planned_hours": 80},
        ]

        result = service.calculate_utilization()

        assert result["plan_count"] == 2
        assert result["plans"][0]["utilization_percent"] == 75.0  # 120/160
        assert result["plans"][1]["utilization_percent"] == 50.0  # 80/160
        assert result["average_utilization"] == 62.5

    def test_빈_결과(self, service, mock_repos) -> None:
        """capacity plan이 없으면 빈 결과를 반환한다."""
        mock_repos["capacity_repo"].find_many.return_value = []

        result = service.calculate_utilization()

        assert result["plan_count"] == 0
        assert result["average_utilization"] == 0.0
