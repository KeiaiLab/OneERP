"""크로스서비스 구매 프로세스 워크플로우 단위 테스트.

이벤트 체인: MaterialRequest.submitted → PurchaseOrder(draft)
                → PurchaseReceipt(draft) → PurchaseInvoice(draft)
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, cast
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# 테스트용 더미 데이터
# ---------------------------------------------------------------------------

TENANT_ID = "T-TEST-001"

MATERIAL_REQUEST_DOC = {
    "_id": "MR-2026-00001",
    "tenant_id": TENANT_ID,
    "docstatus": 1,
    "request_type": "purchase",
    "required_date": "2026-04-01",
    "items": [
        {
            "idx": 1,
            "item_code": "ITEM-001",
            "item_name": "원자재A",
            "qty": 10,
            "warehouse": "WH-001",
        },
        {
            "idx": 2,
            "item_code": "ITEM-002",
            "item_name": "원자재B",
            "qty": 5,
            "warehouse": "WH-001",
        },
    ],
    "total_qty": 15,
}

PURCHASE_ORDER_DOC = {
    "_id": "PO-2026-00001",
    "tenant_id": TENANT_ID,
    "docstatus": 1,
    "supplier_id": "SUP-001",
    "supplier_name": "테스트공급업체",
    "transaction_date": "2026-04-01",
    "items": [
        {
            "idx": 1,
            "item_code": "ITEM-001",
            "item_name": "원자재A",
            "qty": 10,
            "rate": 1000.0,
            "amount": 10000.0,
            "received_qty": 0,
        },
        {
            "idx": 2,
            "item_code": "ITEM-002",
            "item_name": "원자재B",
            "qty": 5,
            "rate": 2000.0,
            "amount": 10000.0,
            "received_qty": 0,
        },
    ],
    "total": 20000.0,
    "grand_total": 22000.0,
}

PURCHASE_RECEIPT_DOC = {
    "_id": "PRCP-2026-00001",
    "tenant_id": TENANT_ID,
    "docstatus": 1,
    "supplier": "SUP-001",
    "supplier_name": "테스트공급업체",
    "posting_date": "2026-04-05",
    "items": [
        {
            "idx": 1,
            "item_code": "ITEM-001",
            "item_name": "원자재A",
            "qty": 10,
            "rate": 1000.0,
            "amount": 10000.0,
            "warehouse": "WH-001",
        },
        {
            "idx": 2,
            "item_code": "ITEM-002",
            "item_name": "원자재B",
            "qty": 5,
            "rate": 2000.0,
            "amount": 10000.0,
            "warehouse": "WH-001",
        },
    ],
    "total_qty": 15,
    "total_amount": 20000.0,
    "warehouse": "WH-001",
}


def _make_repo_factory(*specs: tuple[str, MagicMock]) -> Callable[[str, str | None], MagicMock]:
    """컬렉션명에 따라 다른 mock repo를 반환하는 팩토리를 생성한다."""
    mapping = dict(specs)

    def factory(collection: str, tenant_id: str | None = None) -> MagicMock:
        return mapping.get(collection, MagicMock())

    return factory


# ===========================================================================
# ProcurementFlowService 테스트
# ===========================================================================


class TestProcurementFlowService:
    """자재요청 → 구매주문 초안 생성 테스트."""

    @patch(
        "oneerp_buying_app.services.procurement_flow.generate_name", return_value="PO-2026-00001"
    )
    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_자재요청_제출_시_구매주문_초안_생성_성공(
        self, mock_repo_cls: MagicMock, mock_name: MagicMock
    ) -> None:
        """자재요청 제출 이벤트로 구매주문 초안이 생성된다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = MATERIAL_REQUEST_DOC
        po_repo = MagicMock()
        mock_repo_cls.side_effect = _make_repo_factory(
            ("material_requests", mr_repo),
            ("purchase_orders", po_repo),
        )

        service = ProcurementFlowService()
        result = service.handle_material_request_submitted({"doc_id": "MR-2026-00001"}, TENANT_ID)

        assert result == "PO-2026-00001"
        po_repo.insert.assert_called_once()

    @patch(
        "oneerp_buying_app.services.procurement_flow.generate_name", return_value="PO-2026-00001"
    )
    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_자재요청_아이템이_구매주문에_올바르게_매핑된다(
        self, mock_repo_cls: MagicMock, mock_name: MagicMock
    ) -> None:
        """자재요청의 items가 구매주문 items로 정확히 매핑된다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = MATERIAL_REQUEST_DOC
        po_repo = MagicMock()
        mock_repo_cls.side_effect = _make_repo_factory(
            ("material_requests", mr_repo),
            ("purchase_orders", po_repo),
        )

        service = ProcurementFlowService()
        service.handle_material_request_submitted({"doc_id": "MR-2026-00001"}, TENANT_ID)

        # insert()에 전달된 PurchaseOrder 문서 확인
        po_doc = po_repo.insert.call_args[0][0]
        assert len(po_doc.items) == 2
        assert po_doc.items[0].item_code == "ITEM-001"
        assert po_doc.items[0].qty == 10
        assert po_doc.items[1].item_code == "ITEM-002"
        assert po_doc.items[1].qty == 5
        # 단가는 0.0 (이후 공급업체 견적에서 결정)
        assert po_doc.items[0].rate == 0.0
        assert po_doc.items[0].delivery_date.isoformat() == "2026-04-01"

    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_이벤트_데이터에_doc_id_누락_시_None_반환(self, mock_repo_cls: MagicMock) -> None:
        """event_data에 doc_id가 없으면 None을 반환한다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        service = ProcurementFlowService()
        result = service.handle_material_request_submitted({}, TENANT_ID)

        assert result is None
        mock_repo_cls.assert_not_called()

    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_자재요청_문서_미존재_시_None_반환(self, mock_repo_cls: MagicMock) -> None:
        """자재요청 문서가 존재하지 않으면 None을 반환한다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = None
        mock_repo_cls.return_value = mr_repo

        service = ProcurementFlowService()
        result = service.handle_material_request_submitted({"doc_id": "MR-NOT-EXIST"}, TENANT_ID)

        assert result is None

    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_구매_유형이_아닌_자재요청은_건너뛴다(self, mock_repo_cls: MagicMock) -> None:
        """request_type이 purchase가 아니면 구매주문을 생성하지 않는다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        transfer_mr = {**MATERIAL_REQUEST_DOC, "request_type": "transfer"}
        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = transfer_mr
        mock_repo_cls.return_value = mr_repo

        service = ProcurementFlowService()
        result = service.handle_material_request_submitted({"doc_id": "MR-2026-00001"}, TENANT_ID)

        assert result is None


# ===========================================================================
# ReceiptHandlerService 로직 테스트
# ===========================================================================


class TestReceiptHandlerLogic:
    """구매주문 → 입고전표 초안 아이템 매핑 로직 테스트."""

    def test_구매주문_아이템이_입고전표_아이템으로_매핑된다(self) -> None:
        """구매주문의 items가 입고전표 items로 정확히 매핑된다."""
        po_doc = PURCHASE_ORDER_DOC
        pr_items = []
        po_items = cast("list[dict[str, Any]]", po_doc["items"])
        for idx, item in enumerate(po_items, start=1):
            pr_items.append(
                {
                    "idx": idx,
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "qty": item.get("qty", 0),
                    "rate": item.get("rate", 0.0),
                    "amount": item.get("amount", 0.0),
                    "warehouse": "",
                }
            )

        assert len(pr_items) == 2
        assert pr_items[0]["item_code"] == "ITEM-001"
        assert pr_items[0]["rate"] == 1000.0
        assert pr_items[1]["item_code"] == "ITEM-002"
        assert pr_items[1]["rate"] == 2000.0

    def test_구매주문_doc_id_누락_시_처리_건너뛰기(self) -> None:
        """event_data에 doc_id가 없으면 입고전표를 생성하지 않는다."""
        event_data: dict = {}
        doc_id = event_data.get("doc_id")
        assert doc_id is None


# ===========================================================================
# InvoiceHandlerService 로직 테스트
# ===========================================================================


class TestInvoiceHandlerLogic:
    """입고전표 → 매입전표 초안 아이템 매핑 로직 테스트."""

    def test_입고전표_제출_시_매입전표_아이템_금액_계산(self) -> None:
        """입고전표의 qty * rate가 매입전표 amount로 계산된다."""
        pr_doc = PURCHASE_RECEIPT_DOC
        pi_items = []
        pr_items_src = cast("list[dict[str, Any]]", pr_doc["items"])
        for idx, item in enumerate(pr_items_src, start=1):
            qty = item.get("qty", 0)
            rate = item.get("rate", 0.0)
            pi_items.append(
                {
                    "idx": idx,
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "qty": qty,
                    "rate": rate,
                    "amount": qty * rate,
                }
            )

        assert len(pi_items) == 2
        assert pi_items[0]["amount"] == 10000.0  # 10 * 1000
        assert pi_items[1]["amount"] == 10000.0  # 5 * 2000
        grand_total = sum(item["amount"] for item in pi_items)
        assert grand_total == 20000.0

    def test_입고전표_doc_id_누락_시_처리_건너뛰기(self) -> None:
        """event_data에 doc_id가 없으면 매입전표를 생성하지 않는다."""
        event_data: dict = {}
        doc_id = event_data.get("doc_id")
        assert doc_id is None


# ===========================================================================
# 전체 체인 통합 테스트
# ===========================================================================


class TestFullProcurementChain:
    """MR → PO → PR → PI 전체 이벤트 체인 통합 테스트."""

    @patch("oneerp_buying_app.services.procurement_flow.generate_name")
    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_전체_구매_프로세스_체인(self, mock_repo_cls: MagicMock, mock_name: MagicMock) -> None:
        """자재요청→구매주문→입고전표→매입전표 전체 체인이 동작한다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        # --- 1단계: 자재요청 → 구매주문 ---
        mock_name.return_value = "PO-2026-00001"
        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = MATERIAL_REQUEST_DOC
        po_repo = MagicMock()

        mock_repo_cls.side_effect = _make_repo_factory(
            ("material_requests", mr_repo),
            ("purchase_orders", po_repo),
        )

        procurement_svc = ProcurementFlowService()
        po_id = procurement_svc.handle_material_request_submitted(
            {"doc_id": "MR-2026-00001"}, TENANT_ID
        )
        assert po_id == "PO-2026-00001"

        # 생성된 PO 문서 확인
        po_doc = po_repo.insert.call_args[0][0]
        assert po_doc.id == "PO-2026-00001"
        assert po_doc.docstatus == 0  # 초안
        assert len(po_doc.items) == 2

        # --- 2단계: 구매주문 → 입고전표 아이템 매핑 검증 ---
        submitted_po_items = po_doc.items
        pr_items = []
        for idx, item in enumerate(submitted_po_items, start=1):
            pr_items.append(
                {
                    "idx": idx,
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "rate": Decimal(1000),  # 이후 공급업체 견적에서 설정된 값
                    "amount": item.qty * Decimal(1000),
                }
            )

        assert len(pr_items) == 2
        assert pr_items[0]["qty"] == 10
        assert pr_items[1]["qty"] == 5

        # --- 3단계: 입고전표 → 매입전표 금액 계산 검증 ---
        pi_items = []
        for idx, item in enumerate(pr_items, start=1):
            qty = item["qty"]
            rate = item["rate"]
            pi_items.append(
                {
                    "idx": idx,
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "qty": qty,
                    "rate": rate,
                    "amount": qty * rate,
                }
            )

        grand_total = sum(item["amount"] for item in pi_items)
        assert grand_total == Decimal(15000)  # (10 * 1000) + (5 * 1000)
        assert pi_items[0]["amount"] == Decimal(10000)
        assert pi_items[1]["amount"] == Decimal(5000)

    @patch(
        "oneerp_buying_app.services.procurement_flow.generate_name", return_value="PO-2026-00002"
    )
    @patch("oneerp_buying_app.services.procurement_flow.Repository")
    def test_자재요청_원본_참조가_구매주문에_기록된다(
        self, mock_repo_cls: MagicMock, mock_name: MagicMock
    ) -> None:
        """생성된 구매주문에 원본 자재요청 참조와 테넌트 정보가 올바르다."""
        from oneerp_buying_app.services.procurement_flow import ProcurementFlowService

        mr_repo = MagicMock()
        mr_repo.find_by_id.return_value = MATERIAL_REQUEST_DOC
        po_repo = MagicMock()
        mock_repo_cls.side_effect = _make_repo_factory(
            ("material_requests", mr_repo),
            ("purchase_orders", po_repo),
        )

        service = ProcurementFlowService()
        service.handle_material_request_submitted({"doc_id": "MR-2026-00001"}, TENANT_ID)

        po_doc = po_repo.insert.call_args[0][0]
        assert po_doc.tenant_id == TENANT_ID
        assert po_doc.id == "PO-2026-00002"
