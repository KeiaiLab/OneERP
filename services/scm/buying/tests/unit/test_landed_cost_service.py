"""부대비용 배분 서비스(LandedCostService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch("oneerp_buying_app.services.landed_cost_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.landed_cost_service import LandedCostService

        service = LandedCostService(tenant_id="test-tenant")

    return service, repos["landed_cost_vouchers"], repos["purchase_receipts"]


class Test부대비용배분:
    """allocate_costs 테스트."""

    def test_수량기반_배분(self) -> None:
        """수량 비율로 부대비용을 배분한다."""
        service, lcv_repo, receipt_repo = _make_service()
        lcv_repo.find_by_id.return_value = {
            "_id": "LCV-001",
            "receipt_document": "PRCP-001",
            "items": [{"description": "운송비", "tax_amount": 1000, "allocation_method": "qty"}],
        }
        receipt_repo.find_by_id.return_value = {
            "_id": "PRCP-001",
            "items": [
                {"item_code": "A", "qty": 30, "amount": 3000},
                {"item_code": "B", "qty": 70, "amount": 7000},
            ],
        }

        result = service.allocate_costs("LCV-001")

        assert result["total_landed_cost"] == 1000
        # A: 1000 * (30/100) = 300, B: 1000 * (70/100) = 700
        assert result["allocations"][0]["landed_cost"] == 300.0
        assert result["allocations"][1]["landed_cost"] == 700.0
        assert result["allocations"][0]["total_cost"] == 3300.0

    def test_금액기반_배분(self) -> None:
        """금액 비율로 부대비용을 배분한다."""
        service, lcv_repo, receipt_repo = _make_service()
        lcv_repo.find_by_id.return_value = {
            "_id": "LCV-001",
            "receipt_document": "PRCP-001",
            "items": [{"description": "관세", "tax_amount": 500, "allocation_method": "amount"}],
        }
        receipt_repo.find_by_id.return_value = {
            "_id": "PRCP-001",
            "items": [
                {"item_code": "A", "qty": 10, "amount": 2000},
                {"item_code": "B", "qty": 10, "amount": 8000},
            ],
        }

        result = service.allocate_costs("LCV-001")

        # A: 500 * (2000/10000) = 100, B: 500 * (8000/10000) = 400
        assert result["allocations"][0]["landed_cost"] == 100.0
        assert result["allocations"][1]["landed_cost"] == 400.0

    def test_LCV_미존재시_에러(self) -> None:
        service, lcv_repo, _receipt = _make_service()
        lcv_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.allocate_costs("LCV-999")
        assert "부대비용전표" in (exc_info.value.detail or "")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_입고전표_미존재시_에러(self) -> None:
        service, lcv_repo, receipt_repo = _make_service()
        lcv_repo.find_by_id.return_value = {
            "_id": "LCV-001",
            "receipt_document": "PRCP-999",
            "items": [],
        }
        receipt_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.allocate_costs("LCV-001")
        assert "입고전표" in (exc_info.value.detail or "")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")
