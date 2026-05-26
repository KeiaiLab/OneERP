"""판매 반품 서비스(SalesReturnService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_selling_app.services.sales_return_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_selling_app.services.sales_return_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_selling_app.services.sales_return_service import SalesReturnService

        service = SalesReturnService(tenant_id="test-tenant")
    return service, repos["sales_returns"], repos["sales_invoices"]


class Test판매반품:
    def test_정상_반품_생성(self) -> None:
        service, return_repo, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = {
            "_id": "SI-001",
            "customer": "CUST-001",
            "items": [{"item_code": "ITEM-001", "qty": 100, "rate": 50}],
        }

        result = service.create_return_from_invoice(
            "SI-001", [{"item_code": "ITEM-001", "qty": 10}], reason="불량"
        )

        assert result["return_id"] == "SRT-001"
        assert result["total_refund"] == 500.0
        return_repo.insert.assert_called_once()

    def test_반품수량_초과_에러(self) -> None:
        service, _ret, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = {
            "_id": "SI-001",
            "items": [{"item_code": "ITEM-001", "qty": 10, "rate": 50}],
        }

        with pytest.raises(OneERPError, match="ERR-SELL-031"):
            service.create_return_from_invoice("SI-001", [{"item_code": "ITEM-001", "qty": 20}])

    def test_송장없는_아이템_에러(self) -> None:
        service, _ret, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = {
            "_id": "SI-001",
            "items": [{"item_code": "ITEM-001", "qty": 10, "rate": 50}],
        }

        with pytest.raises(OneERPError, match="ERR-SELL-031"):
            service.create_return_from_invoice("SI-001", [{"item_code": "ITEM-999", "qty": 1}])

    def test_송장_미존재_에러(self) -> None:
        service, _ret, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.create_return_from_invoice("SI-999", [])

    def test_전체수량_반품_경계값(self) -> None:
        """BR-SELL-004: 경계값 — 송장 수량 전체를 반품하면 정상 처리."""
        service, _ret_repo, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = {
            "_id": "SI-FULL",
            "customer": "CUST-001",
            "items": [{"item_code": "ITEM-A", "qty": 50, "rate": 100}],
        }

        result = service.create_return_from_invoice("SI-FULL", [{"item_code": "ITEM-A", "qty": 50}])

        assert result["total_refund"] == 5000.0
        assert result["item_count"] == 1

    def test_다중품목_반품(self) -> None:
        """BR-SELL-004/005: 여러 품목 반품 시 각각 수량 검증 + 환불 합산."""
        service, _ret, inv_repo = _make_service()
        inv_repo.find_by_id.return_value = {
            "_id": "SI-MULTI",
            "customer": "CUST-002",
            "items": [
                {"item_code": "ITEM-A", "qty": 10, "rate": 1000},
                {"item_code": "ITEM-B", "qty": 5, "rate": 2000},
            ],
        }

        result = service.create_return_from_invoice(
            "SI-MULTI",
            [
                {"item_code": "ITEM-A", "qty": 3},
                {"item_code": "ITEM-B", "qty": 2},
            ],
        )

        # 3*1000 + 2*2000 = 7000
        assert result["total_refund"] == 7000.0
        assert result["item_count"] == 2
