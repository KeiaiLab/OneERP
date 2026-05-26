"""차량 관리 서비스(FleetService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_assets_app.services.fleet_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_assets_app.services.fleet_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_assets_app.services.fleet_service import FleetService

        service = FleetService(tenant_id="test-tenant")
    return (
        service,
        repos["vehicles"],
        repos["vehicle_assignments"],
        repos["vehicle_logs"],
        repos["fuel_entries"],
        repos["vehicle_maintenances"],
    )


class Test차량배정:
    def test_배정(self) -> None:
        service, vehicle_repo, assign_repo, _log, _fuel, _maint = _make_service()
        vehicle_repo.find_by_id.return_value = {"_id": "V-001"}

        result = service.assign_vehicle("V-001", "EMP-001", "2026-01-01", "2026-12-31")
        assert result["assignment_id"] == "VA-001"
        assign_repo.insert.assert_called_once()

    def test_차량_미존재_에러(self) -> None:
        service, vehicle_repo, _assign, _log, _fuel, _maint = _make_service()
        vehicle_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.assign_vehicle("V-999", "EMP-001", "2026-01-01", "2026-12-31")


class Test차량요약:
    def test_요약_집계(self) -> None:
        service, _vehicle, _assign, log_repo, fuel_repo, maint_repo = _make_service()
        log_repo.find_many.return_value = [
            {"distance_km": 100},
            {"distance_km": 200},
        ]
        fuel_repo.find_many.return_value = [{"amount": 50000}]
        maint_repo.find_many.return_value = [{"cost": 100000}]

        result = service.get_vehicle_summary("V-001")

        assert result["total_trips"] == 2
        assert result["total_distance_km"] == 300.0
        assert result["total_fuel_cost"] == 50000.0
        assert result["cost_per_km"] == 500.0  # (50000+100000)/300
