"""감가상각 서비스(DepreciationService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_assets_app.services.depreciation_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_assets_app.services.depreciation_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_assets_app.services.depreciation_service import DepreciationService

        service = DepreciationService(tenant_id="test-tenant")
    return service, repos["assets"], repos["depreciation_entries"]


def _sample_asset(**overrides: object) -> dict:
    """기본 자산 데이터를 반환한다."""
    base = {
        "_id": "ASSET-001",
        "asset_name": "테스트 서버",
        "gross_amount": 12_000_000,
        "salvage_value": 0,
        "useful_life_years": 5,
        "current_value": 12_000_000,
        "depreciation_method": "straight_line",
        "status": "submitted",
    }
    base.update(overrides)
    return base


class Test정액법:
    def test_월별_상각액_계산(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset()

        result = service.calculate_straight_line("ASSET-001")

        # (12,000,000 - 0) / (5 * 12) = 200,000
        assert result == 200_000.0

    def test_잔존가치_포함(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(salvage_value=2_000_000)

        result = service.calculate_straight_line("ASSET-001")

        # (12,000,000 - 2,000,000) / (5 * 12) = 166,666.67
        assert result == pytest.approx(166_666.67, abs=0.01)

    def test_자산_미존재(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.calculate_straight_line("ASSET-999")

    def test_내용연수_0_에러(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(useful_life_years=0)

        with pytest.raises(OneERPError, match="ERR-AST-001"):
            service.calculate_straight_line("ASSET-001")


class Test정률법:
    def test_rate_지정(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(
            current_value=10_000_000,
        )

        result = service.calculate_declining_balance("ASSET-001", rate=0.4)

        # 10,000,000 * 0.4 / 12 = 333,333.33
        assert result == pytest.approx(333_333.33, abs=0.01)

    def test_rate_자동계산(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(
            gross_amount=10_000_000,
            salvage_value=1_000_000,
            useful_life_years=5,
            current_value=10_000_000,
        )

        result = service.calculate_declining_balance("ASSET-001")

        # rate = 1 - (1,000,000/10,000,000)^(1/5) ≈ 0.3690
        assert result > 0

    def test_자산_미존재(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.calculate_declining_balance("ASSET-999")

    def test_내용연수_0_에러(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(useful_life_years=0)

        with pytest.raises(OneERPError, match="ERR-AST-001"):
            service.calculate_declining_balance("ASSET-001")

    def test_취득원가_잔존가치_0_에러(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(
            gross_amount=0,
            salvage_value=0,
        )

        with pytest.raises(OneERPError, match="ERR-AST-002"):
            service.calculate_declining_balance("ASSET-001")


class Test월별일괄상각:
    def test_정상_상각(self) -> None:
        service, asset_repo, dep_repo = _make_service()
        asset_repo.find_many.return_value = [_sample_asset()]
        asset_repo.find_by_id.return_value = _sample_asset()

        results = service.run_monthly_depreciation("2026-03")

        assert len(results) == 1
        assert results[0]["depreciation_amount"] == 200_000.0
        assert results[0]["remaining_value"] == 11_800_000.0
        dep_repo.insert.assert_called_once()
        asset_repo.update_by_id.assert_called_once()

    def test_잔존가치_이하_자산_건너뛰기(self) -> None:
        service, asset_repo, dep_repo = _make_service()
        asset_repo.find_many.return_value = [
            _sample_asset(current_value=0, salvage_value=0),
        ]

        results = service.run_monthly_depreciation("2026-03")

        assert len(results) == 0
        dep_repo.insert.assert_not_called()

    def test_상각후_잔존가치_보호(self) -> None:
        service, asset_repo, _dep_repo = _make_service()
        # 잔존가치보다 약간 높은 장부가 — 상각액이 조정되어야 함
        asset_repo.find_many.return_value = [
            _sample_asset(current_value=100_000, salvage_value=0),
        ]
        asset_repo.find_by_id.return_value = _sample_asset(
            current_value=100_000,
            salvage_value=0,
        )

        results = service.run_monthly_depreciation("2026-03")

        assert len(results) == 1
        assert results[0]["remaining_value"] >= 0


class Test스케줄:
    def test_정액법_스케줄(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = _sample_asset(
            gross_amount=1_200_000,
            salvage_value=0,
            useful_life_years=1,
            current_value=1_200_000,
        )

        schedule = service.get_depreciation_schedule("ASSET-001")

        assert len(schedule) == 12
        assert schedule[0]["depreciation_amount"] == 100_000.0
        assert schedule[-1]["remaining_value"] == 0.0

    def test_자산_미존재(self) -> None:
        service, asset_repo, _dep = _make_service()
        asset_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.get_depreciation_schedule("ASSET-999")
