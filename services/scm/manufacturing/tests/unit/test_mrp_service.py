"""MRP 서비스(MRPService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_manufacturing_app.services.mrp_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_manufacturing_app.services.mrp_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.mrp_service import MRPService

        service = MRPService(tenant_id="test-tenant")
    return (
        service,
        repos["demand_forecasts"],
        repos["mrp_runs"],
        repos["boms"],
        repos["stock_balances"],
    )


class TestMRP실행:
    def test_재고부족_구매요청_생성(self) -> None:
        """재고 부족 + BOM 없음 → 구매요청."""
        service, forecast_repo, _mrp_repo, bom_repo, stock_repo = _make_service()
        forecast_repo.find_by_id.return_value = {
            "_id": "DF-001",
            "items": [{"item_code": "ITEM-001", "qty": 100}],
        }
        stock_repo.find_many.return_value = [{"item_code": "ITEM-001", "qty": 30}]
        bom_repo.find_many.return_value = []

        result = service.run_mrp("DF-001")

        assert result["purchase_request_count"] == 1
        assert result["work_order_count"] == 0
        assert result["purchase_requests"][0]["qty"] == 70  # 100 - 30

    def test_재고부족_BOM_있으면_작업지시(self) -> None:
        """재고 부족 + BOM 있음 → 작업지시."""
        service, forecast_repo, _mrp, bom_repo, stock_repo = _make_service()
        forecast_repo.find_by_id.return_value = {
            "_id": "DF-001",
            "items": [{"item_code": "ITEM-001", "qty": 50}],
        }
        stock_repo.find_many.return_value = [{"item_code": "ITEM-001", "qty": 10}]
        bom_repo.find_many.return_value = [{"_id": "BOM-001"}]

        result = service.run_mrp("DF-001")

        assert result["purchase_request_count"] == 0
        assert result["work_order_count"] == 1
        assert result["work_orders"][0]["qty"] == 40

    def test_재고충분_발주없음(self) -> None:
        """재고 충분하면 발주/작업지시 없음."""
        service, forecast_repo, _mrp, _bom, stock_repo = _make_service()
        forecast_repo.find_by_id.return_value = {
            "_id": "DF-001",
            "items": [{"item_code": "ITEM-001", "qty": 50}],
        }
        stock_repo.find_many.return_value = [{"item_code": "ITEM-001", "qty": 100}]

        result = service.run_mrp("DF-001")

        assert result["purchase_request_count"] == 0
        assert result["work_order_count"] == 0

    def test_예측_미존재_에러(self) -> None:
        """수요예측 미존재 시 OneERPError(ERR-MFG-002)."""
        service, forecast_repo, _mrp, _bom, _stock = _make_service()
        forecast_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="ERR-MFG-002"):
            service.run_mrp("DF-999")
