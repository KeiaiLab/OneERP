"""포괄주문 서비스 — 포괄주문 분할 납품 및 잔량 관리 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-SELL-006: 포괄주문 잔량 검증 (주문 수량 ≤ 잔량)
- BR-SELL-007: 포괄주문 수량 누적 (ordered_qty += 신규 주문 수량)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class BlanketOrderService:
    """포괄주문(Blanket Order) 비즈니스 로직.

    포괄주문에서 분할 판매주문을 생성하고 잔량을 추적한다.
    """

    def __init__(self, tenant_id: str, user_sub: str = "") -> None:
        self._tenant_id = tenant_id
        self._user_sub = user_sub
        self._blo_repo = Repository("blanket_orders", tenant_id=tenant_id)
        self._so_repo = Repository("sales_orders", tenant_id=tenant_id)

    # ------------------------------------------------------------
    # Route CRUD 위임 (M3 arch-baseline 감소)
    # ------------------------------------------------------------

    def create_from_request(self, body: Any) -> dict[str, Any]:
        """BlanketOrderCreate 요청 바디로 포괄주문을 생성한다."""
        from oneerp_selling_app.models.blanket_order import BlanketOrder

        doc_id = generate_name("BLO", tenant_id=self._tenant_id)
        items_raw = [item.model_dump() for item in body.items]
        items_raw, total = calculate_line_totals(items_raw)
        doc = BlanketOrder(
            _id=doc_id,
            tenant_id=self._tenant_id,
            customer=body.customer,
            from_date=body.from_date,
            to_date=body.to_date,
            items=body.items,
            total=total,
            created_by=self._user_sub,
            updated_by=self._user_sub,
        )
        self._blo_repo.insert(doc)
        return {"id": doc_id, "message": "포괄주문이 생성되었습니다"}

    def list_orders(self, skip: int, limit: int) -> dict[str, Any]:
        """포괄주문 목록 페이지네이션."""
        docs = self._blo_repo.find_many(skip=skip, limit=limit, sort=[("created_at", -1)])
        total = self._blo_repo.count()
        return {"data": docs, "total": total}

    def get_order(self, doc_id: str) -> dict[str, Any] | None:
        """포괄주문 상세 조회."""
        return self._blo_repo.find_by_id(doc_id)

    def update_order(self, doc_id: str, body: Any) -> dict[str, Any]:
        """포괄주문 수정. 초안 상태에서만 허용."""
        doc = self._blo_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("포괄주문을 찾을 수 없습니다")
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
        self._blo_repo.update_by_id(doc_id, update_data)
        return {"id": doc_id, "message": "포괄주문이 수정되었습니다"}

    def submit_order(self, doc_id: str) -> dict[str, Any]:
        """포괄주문 제출 (초안 → 제출)."""
        doc = self._blo_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("포괄주문을 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.DRAFT:
            raise_bad_request("초안 상태에서만 제출할 수 있습니다")

        self._blo_repo.submit_with_event(
            doc_id,
            event_type=EventType.BLANKET_ORDER_SUBMITTED,
            triggered_by=self._user_sub,
        )
        return {"id": doc_id, "message": "포괄주문이 제출되었습니다"}

    def cancel_order(self, doc_id: str) -> dict[str, Any]:
        """포괄주문 취소 (제출 → 취소)."""
        doc = self._blo_repo.find_by_id(doc_id)
        if not doc:
            raise_not_found("포괄주문을 찾을 수 없습니다")
        assert doc is not None  # noqa: S101 — ty 타입 내로잉
        if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
            raise_bad_request("제출된 문서만 취소할 수 있습니다")

        self._blo_repo.cancel(doc_id)
        return {"id": doc_id, "message": "포괄주문이 취소되었습니다"}

    def create_sales_order(
        self,
        blanket_order_id: str,
        order_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """포괄주문에서 분할 판매주문을 생성한다.

        주문 수량이 포괄주문 잔량을 초과할 수 없다.

        Args:
            blanket_order_id: 포괄주문 ID
            order_items: [{"item_code": "...", "qty": N}, ...]

        Returns:
            생성된 SO 정보
        """
        blo = self._blo_repo.find_by_id(blanket_order_id)
        if not blo:
            msg = f"포괄주문 '{blanket_order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        # 포괄주문 아이템별 잔량 매핑
        blo_items = blo.get("items", [])
        remaining: dict[str, dict[str, float]] = {}
        for item in blo_items:
            code = item.get("item_code", "")
            total_qty = float(item.get("qty", 0))
            ordered_qty = float(item.get("ordered_qty", 0))
            remaining[code] = {
                "available": total_qty - ordered_qty,
                "rate": float(item.get("rate", 0)),
            }

        # 수량 검증 + SO 아이템 구성
        so_items: list[dict[str, Any]] = []
        total = 0.0
        for oi in order_items:
            item_code = oi.get("item_code", "")
            qty = float(oi.get("qty", 0))

            if item_code not in remaining:
                msg = f"아이템 '{item_code}'은 포괄주문에 없습니다"
                raise ValueError(msg)

            if qty > remaining[item_code]["available"]:
                msg = (
                    f"아이템 '{item_code}' 주문수량({qty})이 "
                    f"잔량({remaining[item_code]['available']})을 초과합니다"
                )
                raise ValueError(msg)

            rate = remaining[item_code]["rate"]
            amount = round(qty * rate, 2)
            so_items.append(
                {
                    "item_code": item_code,
                    "qty": qty,
                    "rate": rate,
                    "amount": amount,
                }
            )
            total += amount

        # 포괄주문 ordered_qty 업데이트
        updated_blo_items = []
        for item in blo_items:
            code = item.get("item_code", "")
            ordered = float(item.get("ordered_qty", 0))
            for oi in order_items:
                if oi.get("item_code") == code:
                    ordered += float(oi.get("qty", 0))
            updated_item = {**item, "ordered_qty": ordered}
            updated_blo_items.append(updated_item)

        # SO 문서 영속화
        so_id = generate_name("SO", tenant_id=self._tenant_id)
        so_doc = {
            "_id": so_id,
            "tenant_id": self._tenant_id,
            "blanket_order_id": blanket_order_id,
            "customer": blo.get("customer", ""),
            "items": so_items,
            "total": round(total, 2),
        }
        self._so_repo.insert(so_doc)

        # 포괄주문 ordered_qty 업데이트
        self._blo_repo.update_by_id(blanket_order_id, {"items": updated_blo_items})

        logger.info(
            "포괄주문 분할 SO: BLO=%s, SO=%s, 아이템=%d, 금액=%.2f",
            blanket_order_id,
            so_id,
            len(so_items),
            total,
        )

        return {
            "blanket_order_id": blanket_order_id,
            "so_id": so_id,
            "so_items": so_items,
            "total": round(total, 2),
            "item_count": len(so_items),
        }

    def get_remaining_quantities(
        self,
        blanket_order_id: str,
    ) -> list[dict[str, Any]]:
        """포괄주문의 아이템별 잔량을 조회한다."""
        blo = self._blo_repo.find_by_id(blanket_order_id)
        if not blo:
            msg = f"포괄주문 '{blanket_order_id}'을 찾을 수 없습니다"
            raise ValueError(msg)

        result: list[dict[str, Any]] = []
        for item in blo.get("items", []):
            total_qty = float(item.get("qty", 0))
            ordered_qty = float(item.get("ordered_qty", 0))
            result.append(
                {
                    "item_code": item.get("item_code", ""),
                    "total_qty": total_qty,
                    "ordered_qty": ordered_qty,
                    "remaining_qty": total_qty - ordered_qty,
                }
            )
        return result
