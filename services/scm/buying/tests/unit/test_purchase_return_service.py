"""구매 반품 서비스(PurchaseReturnService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    with patch(
        "oneerp_buying_app.services.purchase_return_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_buying_app.services.purchase_return_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.purchase_return_service import PurchaseReturnService

        service = PurchaseReturnService(tenant_id="test-tenant")

    return service, repos["purchase_returns"], repos["purchase_receipts"], repos["purchase_orders"]


class Test반품생성:
    """create_return_from_receipt 테스트."""

    def test_정상_반품_생성(self) -> None:
        service, return_repo, receipt_repo, _po = _make_service()
        receipt_repo.find_by_id.return_value = {
            "_id": "PRCP-001",
            "supplier": "SUP-001",
            "items": [
                {"item_code": "ITEM-001", "qty": 100, "rate": 50},
                {"item_code": "ITEM-002", "qty": 200, "rate": 30},
            ],
        }

        result = service.create_return_from_receipt(
            receipt_id="PRCP-001",
            return_items=[{"item_code": "ITEM-001", "qty": 10}],
            reason="불량",
        )

        assert result["return_id"] == "PRT-001"
        assert result["item_count"] == 1
        assert result["total"] == 500.0  # 10 * 50
        return_repo.insert.assert_called_once()

    def test_반품수량_초과시_에러(self) -> None:
        service, _return, receipt_repo, _po = _make_service()
        receipt_repo.find_by_id.return_value = {
            "_id": "PRCP-001",
            "items": [{"item_code": "ITEM-001", "qty": 10, "rate": 50}],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.create_return_from_receipt(
                receipt_id="PRCP-001",
                return_items=[{"item_code": "ITEM-001", "qty": 20}],
            )
        assert "초과합니다" in (exc_info.value.detail or "")

    def test_존재하지않는_아이템_에러(self) -> None:
        service, _return, receipt_repo, _po = _make_service()
        receipt_repo.find_by_id.return_value = {
            "_id": "PRCP-001",
            "items": [{"item_code": "ITEM-001", "qty": 10, "rate": 50}],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.create_return_from_receipt(
                receipt_id="PRCP-001",
                return_items=[{"item_code": "ITEM-999", "qty": 5}],
            )
        assert "입고전표에 없습니다" in (exc_info.value.detail or "")

    def test_입고전표_미존재시_에러(self) -> None:
        service, _return, receipt_repo, _po = _make_service()
        receipt_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.create_return_from_receipt(
                receipt_id="PRCP-999",
                return_items=[],
            )
        assert "구매입고" in (exc_info.value.detail or "")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")
