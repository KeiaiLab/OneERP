"""판매 반품 서비스 — 반품 접수, 수량 검증, 환불 금액 계산 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-SELL-004: 반품 수량 ≤ 원본 송장 수량 (품목별)
- BR-SELL-005: 환불 금액 = 반품 수량 x 원본 단가
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class SalesReturnService:
    """판매 반품 비즈니스 로직.

    판매주문/송장 기반 반품 생성 및 수량/금액 검증.
    """

    def __init__(self, tenant_id: str, user_sub: str = "") -> None:
        self._tenant_id = tenant_id
        self._user_sub = user_sub
        self._return_repo = Repository("sales_returns", tenant_id=tenant_id)
        self._invoice_repo = Repository("sales_invoices", tenant_id=tenant_id)

    # ------------------------------------------------------------
    # Route CRUD 위임 (M3 arch-baseline 감소: Route 에서 Repository 직접 금지)
    # ------------------------------------------------------------

    def create_from_request(self, body: Any) -> dict[str, Any]:
        """SalesReturnCreate 요청을 받아 단순 판매반품을 생성한다."""
        from oneerp_selling_app.models.sales_return import SalesReturn

        doc_id = generate_name("SRT", tenant_id=self._tenant_id)
        items_raw = [item.model_dump() for item in body.items]
        items_raw, total = calculate_line_totals(items_raw)
        doc = SalesReturn(
            _id=doc_id,
            tenant_id=self._tenant_id,
            customer=body.customer,
            return_date=body.return_date,
            reason=body.reason,
            items=body.items,
            total=total,
            created_by=self._user_sub,
            updated_by=self._user_sub,
        )
        self._return_repo.insert(doc)
        return {"id": doc_id, "message": "판매반품이 생성되었습니다"}

    def list_returns(self, skip: int, limit: int) -> dict[str, Any]:
        """판매반품 목록 페이지네이션."""
        docs = self._return_repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._return_repo.count()
        return {"data": docs, "total": total}

    def get_return(self, doc_id: str) -> dict[str, Any] | None:
        """판매반품 상세 조회."""
        return self._return_repo.find_by_id(doc_id)

    def update_return(self, doc_id: str, body: Any) -> dict[str, Any]:
        """판매반품 수정. 초안 상태에서만 허용."""
        doc = self._return_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("판매반품을 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("초안 상태에서만 수정할 수 있습니다")

        update_data = body.model_dump(exclude_none=True)
        if "items" in update_data:
            items_raw = update_data["items"]
            items_raw, total = calculate_line_totals(items_raw)
            update_data["items"] = items_raw
            update_data["total"] = total
        update_data["updated_by"] = self._user_sub
        self._return_repo.update_by_id(doc_id, update_data)
        return {"id": doc_id, "message": "판매반품이 수정되었습니다"}

    def submit_return(self, doc_id: str) -> dict[str, Any]:
        """판매반품 제출 (초안 → 제출)."""
        doc = self._return_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("판매반품을 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("초안 상태에서만 제출할 수 있습니다")

        self._return_repo.submit_with_event(
            doc_id,
            event_type=EventType.SALES_RETURN_SUBMITTED,
            triggered_by=self._user_sub,
        )
        return {"id": doc_id, "message": "판매반품이 제출되었습니다"}

    def cancel_return(self, doc_id: str) -> dict[str, Any]:
        """판매반품 취소 (제출 → 취소)."""
        doc = self._return_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("판매반품을 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
            raise_bad_request("제출된 문서만 취소할 수 있습니다")

        self._return_repo.cancel(doc_id)
        return {"id": doc_id, "message": "판매반품이 취소되었습니다"}

    def create_return_from_invoice(
        self,
        invoice_id: str,
        return_items: list[dict[str, Any]],
        reason: str = "",
    ) -> dict[str, Any]:
        """BR-SELL-004/005: 판매송장 기반 반품을 생성한다.

        BR-SELL-004: 반품 수량 ≤ 원본 송장 수량 (품목별).
        BR-SELL-005: 환불 금액 = 반품 수량 x 원본 단가.

        Args:
            invoice_id: 판매송장 ID
            return_items: [{"item_code": "...", "qty": N}, ...]
            reason: 반품 사유

        Returns:
            반품 생성 결과
        """
        invoice = self._invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise_not_found(f"판매송장 '{invoice_id}'을 찾을 수 없습니다")

        # 송장 아이템별 수량/단가 매핑
        inv_qty_map: dict[str, float] = {}
        inv_rate_map: dict[str, float] = {}
        for item in invoice.get("items", []):
            code = item.get("item_code", "")
            inv_qty_map[code] = float(item.get("qty", 0))
            inv_rate_map[code] = float(item.get("rate", 0))

        # 반품 수량 검증 + 금액 계산
        validated_items: list[dict[str, Any]] = []
        total_refund = 0.0
        for ri in return_items:
            item_code = ri.get("item_code", "")
            return_qty = float(ri.get("qty", 0))

            if item_code not in inv_qty_map:
                raise_unprocessable(
                    "ERR-SELL-031",
                    f"아이템 '{item_code}'은 송장에 없습니다",
                )

            if return_qty > inv_qty_map[item_code]:
                raise_unprocessable(
                    "ERR-SELL-031",
                    f"아이템 '{item_code}' 반품수량({return_qty})이 "
                    f"송장수량({inv_qty_map[item_code]})을 초과합니다",
                )

            rate = inv_rate_map.get(item_code, 0)
            amount = round(return_qty * rate, 2)
            validated_items.append(
                {
                    "item_code": item_code,
                    "qty": return_qty,
                    "rate": rate,
                    "amount": amount,
                }
            )
            total_refund += amount

        srt_id = generate_name("SRT", tenant_id=self._tenant_id)
        self._return_repo.insert(
            {
                "_id": srt_id,
                "customer": invoice.get("customer", ""),
                "invoice_reference": invoice_id,
                "reason": reason,
                "items": validated_items,
                "total": round(total_refund, 2),
                "tenant_id": self._tenant_id,
            }
        )

        logger.info(
            "판매 반품 생성: %s (송장: %s, 환불: %.2f)",
            srt_id,
            invoice_id,
            total_refund,
        )

        return {
            "return_id": srt_id,
            "invoice_reference": invoice_id,
            "item_count": len(validated_items),
            "total_refund": round(total_refund, 2),
        }
