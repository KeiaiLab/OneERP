"""계획 최적화 API 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_advanced_planning_app.main import app as planning_app

# 테스트용 인증 헤더
_AUTH_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "test-user",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}

client = TestClient(planning_app)


def test_밸런싱_API_정상() -> None:
    """GET /api/v1/planning/balance — 수요-공급 밸런싱 시 200."""
    mock_result = {
        "item_code": "ITEM-001",
        "total_demand": 300.0,
        "total_supply": 300.0,
        "gap": 0.0,
        "recommendations": [],
    }

    with patch(
        "oneerp_advanced_planning_app.routes.planning_optimizer.PlanningOptimizerService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.balance_demand_supply.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.get(
            "/api/v1/planning/balance",
            params={"item_code": "ITEM-001"},
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["gap"] == 0.0


def test_시나리오_실행_API_정상() -> None:
    """POST /api/v1/planning/scenarios/{id}/run — 시나리오 실행 시 200."""
    mock_result = {
        "scenario_id": "PLS-00001",
        "status": "completed",
        "base_qty": 1000.0,
        "adjusted_qty": 1100.0,
    }

    with patch(
        "oneerp_advanced_planning_app.routes.planning_optimizer.PlanningOptimizerService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.run_scenario.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/planning/scenarios/PLS-00001/run",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"


def test_가용률_API_정상() -> None:
    """GET /api/v1/planning/utilization — 가용률 조회 시 200."""
    mock_result = {
        "plans": [],
        "plan_count": 0,
        "average_utilization": 0.0,
    }

    with patch(
        "oneerp_advanced_planning_app.routes.planning_optimizer.PlanningOptimizerService"
    ) as mock_svc_cls:
        mock_svc = MagicMock()
        mock_svc.calculate_utilization.return_value = mock_result
        mock_svc_cls.return_value = mock_svc

        resp = client.get(
            "/api/v1/planning/utilization",
            headers=_AUTH_HEADERS,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_count"] == 0
