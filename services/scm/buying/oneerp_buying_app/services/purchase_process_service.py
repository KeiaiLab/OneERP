"""구매 프로세스 서비스 - RFQ 생성, 견적 비교, PO 확정 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-BUY-002: RFQ 복수 공급업체 (suppliers 1개 이상 필수)
- BR-BUY-003: 견적 비교 최저가 추천 (아이템별 min rate)
- BR-BUY-015: SQ -> PO 전환 (공급업체/아이템/금액 복사)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PurchaseProcessService:
    """구매 프로세스 오케스트레이션.

    자재요청 -> 견적요청(RFQ) -> 견적비교 -> 발주(PO) -> 입고 -> 송장 흐름을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._mr_repo = Repository("material_requests", tenant_id=tenant_id)
        self._rfq_repo = Repository("request_for_quotations", tenant_id=tenant_id)
        self._sq_repo = Repository("supplier_quotations", tenant_id=tenant_id)
        self._po_repo = Repository("purchase_orders", tenant_id=tenant_id)
        self._receipt_repo = Repository("purchase_receipts", tenant_id=tenant_id)
        self._invoice_repo = Repository("purchase_invoices", tenant_id=tenant_id)

    @staticmethod
    def _normalize_date(value: Any) -> str:
        """문서/문자열 날짜 값을 ISO 문자열로 정규화한다."""
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if value:
            return str(value)
        return datetime.now(tz=UTC).date().isoformat()

    def create_rfq_from_mr(
        self,
        material_request_id: str,
        suppliers: list[str],
        transaction_date: date | None = None,
    ) -> dict[str, Any]:
        """BR-BUY-002: 자재요청에서 견적요청(RFQ)을 생성한다."""
        mr = self._mr_repo.find_by_id(material_request_id)
        if not mr:
            raise_not_found(f"자재요청 '{material_request_id}'을 찾을 수 없습니다")

        if not suppliers:
            raise_bad_request("ERR-BUY-001: 공급업체를 1개 이상 지정해야 합니다")

        normalized_transaction_date = transaction_date
        if normalized_transaction_date is None:
            required_date = mr.get("required_date")
            if isinstance(required_date, date):
                normalized_transaction_date = required_date
            elif required_date:
                normalized_transaction_date = date.fromisoformat(str(required_date))
            else:
                normalized_transaction_date = datetime.now(tz=UTC).date()

        rfq_items = [
            {
                "item_code": item.get("item_code", ""),
                "item_name": item.get("item_name", ""),
                "qty": item.get("qty", 0),
            }
            for item in mr.get("items", [])
        ]

        rfq_id = generate_name("RFQ", tenant_id=self._tenant_id)
        rfq_doc = {
            "_id": rfq_id,
            "material_request": material_request_id,
            "transaction_date": self._normalize_date(normalized_transaction_date),
            "suppliers": suppliers,
            "items": rfq_items,
            "tenant_id": self._tenant_id,
        }
        self._rfq_repo.insert(rfq_doc)

        logger.info(
            "RFQ 생성: %s (MR: %s, 공급업체: %d개)",
            rfq_id,
            material_request_id,
            len(suppliers),
        )

        return {
            "rfq_id": rfq_id,
            "material_request": material_request_id,
            "supplier_count": len(suppliers),
            "item_count": len(rfq_items),
        }

    def compare_quotations(self, rfq_id: str) -> dict[str, Any]:
        """BR-BUY-003: RFQ에 대한 공급업체 견적을 비교한다."""
        quotations = self._sq_repo.find_many(
            {"rfq_reference": rfq_id, "docstatus": 1},
            limit=100,
            sort=[("grand_total", 1), ("created_at", 1)],
        )

        if not quotations:
            return {
                "rfq_id": rfq_id,
                "quotation_count": 0,
                "quotations": [],
                "recommendations": [],
            }

        item_prices: dict[str, list[dict[str, Any]]] = {}
        comparison_quotes: list[dict[str, Any]] = []
        for sq in quotations:
            supplier = sq.get("supplier", "")
            supplier_name = sq.get("supplier_name", "")
            comparison_quotes.append(
                {
                    "quotation_id": sq.get("_id", ""),
                    "supplier": supplier,
                    "supplier_name": supplier_name,
                    "transaction_date": self._normalize_date(sq.get("transaction_date")),
                    "valid_till": self._normalize_date(sq.get("valid_till")),
                    "grand_total": float(sq.get("grand_total", sq.get("total", 0))),
                    "items": sq.get("items", []),
                }
            )
            for item in sq.get("items", []):
                item_code = item.get("item_code", "")
                item_prices.setdefault(item_code, []).append(
                    {
                        "supplier": supplier,
                        "supplier_name": supplier_name,
                        "quotation_id": sq.get("_id", ""),
                        "rate": float(item.get("rate", 0)),
                        "qty": float(item.get("qty", 0)),
                        "amount": float(item.get("amount", 0)),
                    }
                )

        recommendations: list[dict[str, Any]] = []
        for item_code, prices in item_prices.items():
            ordered_prices = sorted(
                prices,
                key=lambda price: (
                    price["rate"],
                    price["supplier_name"],
                    price["quotation_id"],
                ),
            )
            best = ordered_prices[0]
            alternatives = ordered_prices[1:]
            recommendations.append(
                {
                    "item_code": item_code,
                    "recommended_supplier": best["supplier"],
                    "recommended_supplier_name": best["supplier_name"],
                    "best_rate": best["rate"],
                    "quotation_id": best["quotation_id"],
                    "alternatives": len(alternatives),
                    "alternative_quotes": alternatives,
                }
            )

        return {
            "rfq_id": rfq_id,
            "quotation_count": len(quotations),
            "quotations": comparison_quotes,
            "recommendations": recommendations,
        }

    def create_po_from_quotation(self, quotation_id: str) -> dict[str, Any]:
        """공급업체 견적에서 구매주문(PO)을 생성한다."""
        sq = self._sq_repo.find_by_id(quotation_id)
        if not sq:
            raise_not_found(f"공급업체 견적 '{quotation_id}'을 찾을 수 없습니다")
        if sq.get("docstatus", 0) != 1:
            raise_bad_request("ERR-BUY-041: 제출된 견적에서만 구매주문을 생성할 수 있습니다")

        delivery_date = self._normalize_date(sq.get("valid_till") or sq.get("transaction_date"))
        po_items = [
            {
                "item_code": item.get("item_code", ""),
                "item_name": item.get("item_name", ""),
                "qty": float(item.get("qty", 0)),
                "rate": float(item.get("rate", 0)),
                "amount": float(item.get("amount", 0))
                or float(item.get("qty", 0)) * float(item.get("rate", 0)),
                "received_qty": 0,
                "delivery_date": self._normalize_date(item.get("delivery_date") or delivery_date),
            }
            for item in sq.get("items", [])
        ]

        total = sum((float(item["amount"]) for item in po_items), 0.0)
        transaction_date = self._normalize_date(sq.get("transaction_date"))

        po_id = generate_name("PO", tenant_id=self._tenant_id)
        po_doc = {
            "_id": po_id,
            "supplier_id": sq.get("supplier", ""),
            "supplier_name": sq.get("supplier_name", ""),
            "transaction_date": transaction_date,
            "quotation_reference": quotation_id,
            "items": po_items,
            "total": total,
            "grand_total": total,
            "docstatus": 0,
            "tenant_id": self._tenant_id,
        }
        self._po_repo.insert(po_doc)

        logger.info(
            "PO 생성: %s (SQ: %s, 공급업체: %s, 금액: %.2f)",
            po_id,
            quotation_id,
            sq.get("supplier", ""),
            total,
        )

        return {
            "po_id": po_id,
            "supplier": sq.get("supplier", ""),
            "quotation_reference": quotation_id,
            "total": total,
            "item_count": len(po_items),
        }

    def create_receipt_from_purchase_order(self, purchase_order_id: str) -> dict[str, Any]:
        """제출된 구매주문에서 구매입고 초안을 생성한다."""
        po = self._po_repo.find_by_id(purchase_order_id)
        if not po:
            raise_not_found(f"구매주문 '{purchase_order_id}'을 찾을 수 없습니다")
        if po.get("docstatus", 0) != 1:
            raise_bad_request("ERR-BUY-042: 제출된 구매주문에서만 구매입고를 생성할 수 있습니다")

        receipt_items: list[dict[str, Any]] = []
        for item in po.get("items", []):
            qty = float(item.get("qty", 0))
            received_qty = float(item.get("received_qty", 0))
            remaining_qty = qty - received_qty
            if remaining_qty <= 0:
                continue
            rate = float(item.get("rate", 0))
            receipt_items.append(
                {
                    "item_code": item.get("item_code", ""),
                    "item_name": item.get("item_name", ""),
                    "qty": remaining_qty,
                    "rate": rate,
                    "amount": remaining_qty * rate,
                    "warehouse": item.get("warehouse", ""),
                    "purchase_order": purchase_order_id,
                    "delivery_date": self._normalize_date(
                        item.get("delivery_date") or po.get("transaction_date")
                    ),
                }
            )

        if not receipt_items:
            raise_bad_request("ERR-BUY-043: 입고할 잔여 수량이 없습니다")

        total_qty = sum(float(item["qty"]) for item in receipt_items)
        total_amount = sum(float(item["amount"]) for item in receipt_items)
        receipt_id = generate_name("PRCP", tenant_id=self._tenant_id)
        receipt_doc = {
            "_id": receipt_id,
            "tenant_id": self._tenant_id,
            "purchase_order_id": purchase_order_id,
            "supplier": po.get("supplier_id", ""),
            "supplier_name": po.get("supplier_name", ""),
            "posting_date": self._normalize_date(po.get("transaction_date")),
            "items": receipt_items,
            "total_qty": total_qty,
            "total_amount": total_amount,
            "warehouse": po.get("items", [{}])[0].get("warehouse", "") if po.get("items") else "",
            "docstatus": 0,
        }
        self._receipt_repo.insert(receipt_doc)
        return {
            "purchase_receipt_id": receipt_id,
            "source_purchase_order_id": purchase_order_id,
        }

    def create_invoice_from_purchase_order(self, purchase_order_id: str) -> dict[str, Any]:
        """제출된 구매주문에서 구매송장 초안을 생성한다."""
        po = self._po_repo.find_by_id(purchase_order_id)
        if not po:
            raise_not_found(f"구매주문 '{purchase_order_id}'을 찾을 수 없습니다")
        if po.get("docstatus", 0) != 1:
            raise_bad_request("ERR-BUY-044: 제출된 구매주문에서만 구매송장을 생성할 수 있습니다")

        invoice_items = [
            {
                "item_code": item.get("item_code", ""),
                "item_name": item.get("item_name", ""),
                "qty": float(item.get("qty", 0)),
                "rate": float(item.get("rate", 0)),
                "amount": float(item.get("amount", 0))
                or float(item.get("qty", 0)) * float(item.get("rate", 0)),
            }
            for item in po.get("items", [])
        ]
        if not invoice_items:
            raise_bad_request("ERR-BUY-045: 구매송장으로 복사할 품목이 없습니다")

        grand_total = float(po.get("grand_total", 0)) or sum(
            float(item["amount"]) for item in invoice_items
        )
        posting_date = self._normalize_date(po.get("transaction_date"))
        invoice_id = generate_name("PI", tenant_id=self._tenant_id)
        invoice_doc = {
            "_id": invoice_id,
            "tenant_id": self._tenant_id,
            "purchase_order_id": purchase_order_id,
            "supplier_id": po.get("supplier_id", ""),
            "supplier_name": po.get("supplier_name", ""),
            "posting_date": posting_date,
            "due_date": posting_date,
            "items": invoice_items,
            "taxes": [],
            "net_total": grand_total,
            "grand_total": grand_total,
            "outstanding_amount": grand_total,
            "docstatus": 0,
        }
        self._invoice_repo.insert(invoice_doc)
        return {
            "purchase_invoice_id": invoice_id,
            "source_purchase_order_id": purchase_order_id,
        }
