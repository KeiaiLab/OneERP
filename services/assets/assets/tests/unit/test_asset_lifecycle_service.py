"""자산 생애주기 서비스(AssetLifecycleService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_assets_app.services.asset_lifecycle_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_assets_app.services.asset_lifecycle_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_assets_app.services.asset_lifecycle_service import AssetLifecycleService

        service = AssetLifecycleService(tenant_id="test-tenant")
    return (
        service,
        repos["assets"],
        repos["asset_movements"],
        repos["asset_disposals"],
        repos["asset_revaluations"],
        repos["depreciation_entries"],
    )


def _sample_asset(**overrides: object) -> dict:
    base = {
        "_id": "ASSET-001",
        "asset_name": "테스트 서버",
        "current_value": 10_000_000,
        "gross_amount": 12_000_000,
        "status": "submitted",
    }
    base.update(overrides)
    return base


class Test자산이동:
    def test_정상_이동(self) -> None:
        service, asset_repo, mov_repo, _disp, _reval, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset()

        result = service.move_asset(
            "ASSET-001",
            "서울 본사",
            "부산 지사",
            date(2026, 3, 1),
        )

        assert result["movement_id"] == "AMOV-001"
        assert result["from_location"] == "서울 본사"
        assert result["to_location"] == "부산 지사"
        mov_repo.insert.assert_called_once()

    def test_자산_미존재(self) -> None:
        service, asset_repo, _mov, _disp, _reval, _dep = _make_service()
        asset_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.move_asset("ASSET-999", "A", "B")


class Test자산처분:
    def test_매각_처분(self) -> None:
        service, asset_repo, _mov, disp_repo, _reval, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(current_value=8_000_000)

        result = service.dispose_asset(
            "ASSET-001",
            "sale",
            sale_amount=9_000_000,
            disposal_date=date(2026, 3, 15),
        )

        assert result["disposal_id"] == "ADSP-001"
        assert result["gain_loss"] == 1_000_000.0  # 9M - 8M
        assert result["book_value"] == 8_000_000.0
        disp_repo.insert.assert_called_once()
        asset_repo.update_by_id.assert_called_once_with("ASSET-001", {"status": "scrapped"})

    def test_폐기_손실(self) -> None:
        service, asset_repo, _mov, _disp_repo, _reval, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(current_value=5_000_000)

        result = service.dispose_asset(
            "ASSET-001",
            "scrap",
            sale_amount=0,
            disposal_date=date(2026, 3, 15),
        )

        assert result["gain_loss"] == -5_000_000.0


class Test자산재평가:
    def test_가치_상승(self) -> None:
        service, asset_repo, _mov, _disp, reval_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(current_value=10_000_000)

        result = service.revalue_asset(
            "ASSET-001",
            12_000_000,
            date(2026, 3, 1),
        )

        assert result["revaluation_id"] == "ARVAL-001"
        assert result["old_value"] == 10_000_000
        assert result["new_value"] == 12_000_000
        assert result["difference"] == 2_000_000
        reval_repo.insert.assert_called_once()
        asset_repo.update_by_id.assert_called_once_with(
            "ASSET-001",
            {"current_value": 12_000_000},
        )

    def test_가치_하락(self) -> None:
        service, asset_repo, _mov, _disp, _reval_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(current_value=10_000_000)

        result = service.revalue_asset("ASSET-001", 7_000_000, date(2026, 3, 1))

        assert result["difference"] == -3_000_000


class Test자산이력:
    def test_통합_이력(self) -> None:
        service, asset_repo, mov_repo, disp_repo, reval_repo, dep_repo = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset()
        mov_repo.find_many.return_value = [{"_id": "MOV-1"}]
        disp_repo.find_many.return_value = []
        reval_repo.find_many.return_value = [{"_id": "RV-1"}]
        dep_repo.find_many.return_value = [{"_id": "DEP-1"}, {"_id": "DEP-2"}]

        result = service.get_asset_history("ASSET-001")

        assert result["asset_id"] == "ASSET-001"
        assert len(result["movements"]) == 1
        assert len(result["disposals"]) == 0
        assert len(result["revaluations"]) == 1
        assert len(result["depreciations"]) == 2

    def test_자산_미존재(self) -> None:
        service, asset_repo, _mov, _disp, _reval, _dep = _make_service()
        asset_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.get_asset_history("ASSET-999")
