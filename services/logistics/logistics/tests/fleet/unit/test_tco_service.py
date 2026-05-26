"""TCO 서비스(TcoService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_service() -> tuple:
    """TcoService와 mock 레포지토리들을 생성한다."""
    with patch("oneerp_logistics_app.fleet.services.tco_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_logistics_app.fleet.services.tco_service import TcoService

        service = TcoService(tenant_id="test-tenant")
    return service, repos["vehicles"], repos["fuel_entries"], repos["vehicle_maintenances"]


class TestTco계산:
    """TCO 계산 테스트."""

    def test_정상_계산(self) -> None:
        """취득가 + 유류비 + 정비비 합산을 검증한다."""
        service, vehicle_repo, fuel_repo, maint_repo = _make_service()

        vehicle_repo.find_by_id.return_value = {
            "_id": "VH-0001",
            "vehicle_name": "소나타",
            "acquisition_cost": "30000000",
        }
        fuel_repo.find_many.return_value = [
            {"amount": "50000"},
            {"amount": "60000"},
        ]
        maint_repo.find_many.return_value = [
            {"cost": "200000"},
        ]

        result = service.calculate_tco("VH-0001")

        assert result["vehicle_id"] == "VH-0001"
        assert result["acquisition_cost"] == "30000000"
        assert result["total_fuel_cost"] == "110000"
        assert result["total_maintenance_cost"] == "200000"
        assert result["tco"] == "30310000"

    def test_차량_미존재(self) -> None:
        """차량이 없으면 에러를 반환한다."""
        service, vehicle_repo, _fuel, _maint = _make_service()
        vehicle_repo.find_by_id.return_value = None

        result = service.calculate_tco("VH-9999")

        assert "error" in result

    def test_비용_없는_차량(self) -> None:
        """유류/정비 기록이 없는 차량의 TCO는 취득가만 반영한다."""
        service, vehicle_repo, fuel_repo, maint_repo = _make_service()

        vehicle_repo.find_by_id.return_value = {
            "_id": "VH-0002",
            "vehicle_name": "아반떼",
            "acquisition_cost": "25000000",
        }
        fuel_repo.find_many.return_value = []
        maint_repo.find_many.return_value = []

        result = service.calculate_tco("VH-0002")

        assert result["tco"] == "25000000"
        assert result["total_fuel_cost"] == "0"
        assert result["total_maintenance_cost"] == "0"
