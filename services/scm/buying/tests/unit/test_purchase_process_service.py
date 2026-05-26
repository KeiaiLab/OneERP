"""구매 프로세스 서비스(PurchaseProcessService) 단위 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    with patch(
        "oneerp_buying_app.services.purchase_process_service.generate_name",
        side_effect=lambda prefix, **_: f"{prefix}-001",
    ):
        yield


def _make_service() -> tuple:
    with patch("oneerp_buying_app.services.purchase_process_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_buying_app.services.purchase_process_service import PurchaseProcessService

        service = PurchaseProcessService(tenant_id="test-tenant")

    return (
        service,
        repos["material_requests"],
        repos["request_for_quotations"],
        repos["supplier_quotations"],
        repos["purchase_orders"],
        repos["purchase_receipts"],
        repos["purchase_invoices"],
    )


class TestRFQ생성:
    """create_rfq_from_mr 테스트."""

    def test_정상_RFQ_생성(self) -> None:
        service, mr_repo, rfq_repo, _sq, _po, _receipt, _invoice = _make_service()
        mr_repo.find_by_id.return_value = {
            "_id": "MR-001",
            "items": [
                {"item_code": "ITEM-001", "item_name": "원자재A", "qty": 100},
                {"item_code": "ITEM-002", "item_name": "원자재B", "qty": 50},
            ],
        }

        result = service.create_rfq_from_mr("MR-001", suppliers=["SUP-001", "SUP-002"])

        assert result["rfq_id"] == "RFQ-001"
        assert result["supplier_count"] == 2
        assert result["item_count"] == 2
        rfq_repo.insert.assert_called_once()

    def test_RFQ_생성시_자재요청출처와_거래일자를_함께_기록한다(self) -> None:
        service, mr_repo, rfq_repo, _sq, _po, _receipt, _invoice = _make_service()
        mr_repo.find_by_id.return_value = {
            "_id": "MR-001",
            "required_date": "2026-03-28",
            "items": [{"item_code": "ITEM-001", "item_name": "원자재A", "qty": 100}],
        }

        service.create_rfq_from_mr(
            "MR-001",
            suppliers=["SUP-001"],
            transaction_date=date(2026, 3, 20),
        )

        inserted_rfq = rfq_repo.insert.call_args[0][0]
        assert inserted_rfq["material_request"] == "MR-001"
        assert inserted_rfq["transaction_date"] == "2026-03-20"

    def test_MR_미존재시_에러(self) -> None:
        service, mr_repo, _rfq, _sq, _po, _receipt, _invoice = _make_service()
        mr_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.create_rfq_from_mr("MR-999", suppliers=["SUP-001"])
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_공급업체_미지정시_에러(self) -> None:
        service, mr_repo, _rfq, _sq, _po, _receipt, _invoice = _make_service()
        mr_repo.find_by_id.return_value = {"_id": "MR-001", "items": []}

        with pytest.raises(OneERPError) as exc_info:
            service.create_rfq_from_mr("MR-001", suppliers=[])
        assert "공급업체를 1개 이상" in (exc_info.value.detail or "")


class Test견적비교:
    """compare_quotations 테스트."""

    def test_최저가_추천과_비교표를_반환한다(self) -> None:
        service, _mr, _rfq, sq_repo, _po, _receipt, _invoice = _make_service()
        sq_repo.find_many.return_value = [
            {
                "_id": "SQ-001",
                "supplier": "SUP-001",
                "supplier_name": "공급A",
                "grand_total": 1000,
                "items": [{"item_code": "ITEM-001", "rate": 100, "qty": 10, "amount": 1000}],
            },
            {
                "_id": "SQ-002",
                "supplier": "SUP-002",
                "supplier_name": "공급B",
                "grand_total": 800,
                "items": [{"item_code": "ITEM-001", "rate": 80, "qty": 10, "amount": 800}],
            },
            {
                "_id": "SQ-003",
                "supplier": "SUP-003",
                "supplier_name": "공급C",
                "grand_total": 900,
                "items": [{"item_code": "ITEM-001", "rate": 90, "qty": 10, "amount": 900}],
            },
        ]

        result = service.compare_quotations("RFQ-001")

        sq_repo.find_many.assert_called_once_with(
            {"rfq_reference": "RFQ-001", "docstatus": 1},
            limit=100,
            sort=[("grand_total", 1), ("created_at", 1)],
        )
        assert result["quotation_count"] == 3
        assert [quote["quotation_id"] for quote in result["quotations"]] == [
            "SQ-001",
            "SQ-002",
            "SQ-003",
        ]
        rec = result["recommendations"][0]
        assert rec["recommended_supplier"] == "SUP-002"
        assert rec["best_rate"] == 80
        assert rec["alternatives"] == 2
        assert [alt["quotation_id"] for alt in rec["alternative_quotes"]] == ["SQ-003", "SQ-001"]

    def test_견적_없으면_빈결과(self) -> None:
        service, _mr, _rfq, sq_repo, _po, _receipt, _invoice = _make_service()
        sq_repo.find_many.return_value = []

        result = service.compare_quotations("RFQ-001")

        assert result["quotation_count"] == 0
        assert result["recommendations"] == []


class TestPO생성:
    """create_po_from_quotation 테스트."""

    def test_견적_기반_PO_생성(self) -> None:
        service, _mr, _rfq, sq_repo, po_repo, _receipt, _invoice = _make_service()
        sq_repo.find_by_id.return_value = {
            "_id": "SQ-001",
            "docstatus": 1,
            "supplier": "SUP-001",
            "supplier_name": "테스트공급사",
            "valid_till": "2026-04-30",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 100,
                    "amount": 1000,
                },
            ],
        }

        result = service.create_po_from_quotation("SQ-001")

        assert result["po_id"] == "PO-001"
        assert result["supplier"] == "SUP-001"
        assert result["total"] == 1000.0
        po_repo.insert.assert_called_once()
        inserted_po = po_repo.insert.call_args[0][0]
        assert inserted_po["items"][0]["delivery_date"] == "2026-04-30"

    def test_견적_라인_amount가_없어도_qty_rate로_PO금액을_계산한다(self) -> None:
        service, _mr, _rfq, sq_repo, po_repo, _receipt, _invoice = _make_service()
        sq_repo.find_by_id.return_value = {
            "_id": "SQ-001",
            "docstatus": 1,
            "supplier": "SUP-001",
            "supplier_name": "테스트공급사",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 100,
                },
            ],
        }

        result = service.create_po_from_quotation("SQ-001")

        assert result["total"] == 1000.0
        inserted_po = po_repo.insert.call_args[0][0]
        assert inserted_po["items"][0]["amount"] == 1000.0

    def test_견적_미존재시_에러(self) -> None:
        service, _mr, _rfq, sq_repo, _po, _receipt, _invoice = _make_service()
        sq_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError) as exc_info:
            service.create_po_from_quotation("SQ-999")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_초안_견적으로는_PO를_생성할_수_없다(self) -> None:
        service, _mr, _rfq, sq_repo, _po, _receipt, _invoice = _make_service()
        sq_repo.find_by_id.return_value = {
            "_id": "SQ-001",
            "docstatus": 0,
            "supplier": "SUP-001",
            "items": [],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.create_po_from_quotation("SQ-001")
        assert "제출된 견적" in (exc_info.value.detail or "")


class Test하위문서초안생성:
    """구매주문 기반 하위 문서 초안 생성 테스트."""

    def test_제출된_구매주문에서_입고초안_생성(self) -> None:
        service, _mr, _rfq, _sq, po_repo, receipt_repo, _invoice = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "테스트공급사",
            "transaction_date": "2026-04-08",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 100,
                    "amount": 1000,
                    "received_qty": 3,
                    "delivery_date": "2026-04-11",
                }
            ],
        }

        result = service.create_receipt_from_purchase_order("PO-001")

        assert result["purchase_receipt_id"] == "PRCP-001"
        assert result["source_purchase_order_id"] == "PO-001"
        receipt_repo.insert.assert_called_once()
        receipt_doc = receipt_repo.insert.call_args[0][0]
        assert receipt_doc["items"][0]["qty"] == 7
        assert receipt_doc["items"][0]["purchase_order"] == "PO-001"
        assert receipt_doc["items"][0]["delivery_date"] == "2026-04-11"

    def test_제출된_구매주문에서_송장초안_생성(self) -> None:
        service, _mr, _rfq, _sq, po_repo, _receipt, invoice_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "테스트공급사",
            "transaction_date": "2026-04-08",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 100,
                    "amount": 1000,
                    "received_qty": 3,
                    "delivery_date": "2026-04-11",
                }
            ],
            "grand_total": 1000,
        }

        result = service.create_invoice_from_purchase_order("PO-001")

        assert result["purchase_invoice_id"] == "PI-001"
        assert result["source_purchase_order_id"] == "PO-001"
        invoice_repo.insert.assert_called_once()
        invoice_doc = invoice_repo.insert.call_args[0][0]
        assert invoice_doc["purchase_order_id"] == "PO-001"
        assert invoice_doc["outstanding_amount"] == 1000

    def test_PO_라인_amount가_없어도_송장초안_총액을_계산한다(self) -> None:
        service, _mr, _rfq, _sq, po_repo, _receipt, invoice_repo = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "테스트공급사",
            "transaction_date": "2026-04-08",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 100,
                    "delivery_date": "2026-04-11",
                }
            ],
        }

        result = service.create_invoice_from_purchase_order("PO-001")

        assert result["purchase_invoice_id"] == "PI-001"
        invoice_doc = invoice_repo.insert.call_args[0][0]
        assert invoice_doc["items"][0]["amount"] == 1000.0
        assert invoice_doc["grand_total"] == 1000.0

    def test_초안_구매주문으로는_하위문서를_생성할_수_없다(self) -> None:
        service, _mr, _rfq, _sq, po_repo, _receipt, _invoice = _make_service()
        po_repo.find_by_id.return_value = {
            "_id": "PO-001",
            "docstatus": 0,
            "items": [],
        }

        with pytest.raises(OneERPError) as exc_info:
            service.create_receipt_from_purchase_order("PO-001")
        assert "제출된 구매주문" in (exc_info.value.detail or "")
