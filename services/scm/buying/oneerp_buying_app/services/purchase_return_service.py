"""구매 반품 서비스 — 반품 생성 및 재고/미지급금 조정 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-BUY-004: 구매 반품 수량 검증 (반품 수량 <= 입고 수량)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PurchaseReturnService:
    """구매 반품 비즈니스 로직.

    구매입고/구매송장 기반 반품 생성 및 수량/금액 검증.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._return_repo = Repository("purchase_returns", tenant_id=tenant_id)
        self._receipt_repo = Repository("purchase_receipts", tenant_id=tenant_id)
        self._po_repo = Repository("purchase_orders", tenant_id=tenant_id)

    def create_return_from_receipt(
        self,
        receipt_id: str,
        return_items: list[dict[str, Any]],
        reason: str = "",
    ) -> dict[str, Any]:
        """BR-BUY-004: 입고전표 기반으로 반품을 생성한다.

        반품 수량이 입고 수량을 초과할 수 없다.

        Args:
            receipt_id: 구매입고 ID
            return_items: 반품 아이템 [{"item_code": "...", "qty": N}, ...]
            reason: 반품 사유

        Returns:
            생성된 반품 정보
        """
        receipt = self._receipt_repo.find_by_id(receipt_id)
        if not receipt:
            raise_not_found(f"구매입고 '{receipt_id}'을 찾을 수 없습니다")

        # 입고 아이템별 수량 매핑
        receipt_qty_map: dict[str, float] = {}
        receipt_rate_map: dict[str, float] = {}
        for item in receipt.get("items", []):
            code = item.get("item_code", "")
            receipt_qty_map[code] = float(item.get("qty", 0))
            receipt_rate_map[code] = float(item.get("rate", 0))

        # 반품 수량 검증 + 금액 계산
        validated_items: list[dict[str, Any]] = []
        total = 0.0
        for ri in return_items:
            item_code = ri.get("item_code", "")
            return_qty = float(ri.get("qty", 0))

            if item_code not in receipt_qty_map:
                raise_bad_request(f"ERR-BUY-003: 아이템 '{item_code}'은 입고전표에 없습니다")

            if return_qty > receipt_qty_map[item_code]:
                raise_bad_request(
                    f"ERR-BUY-004: 아이템 '{item_code}' 반품수량({return_qty})이 "
                    f"입고수량({receipt_qty_map[item_code]})을 초과합니다"
                )

            rate = receipt_rate_map.get(item_code, 0)
            amount = round(return_qty * rate, 2)
            validated_items.append(
                {
                    "item_code": item_code,
                    "qty": return_qty,
                    "rate": rate,
                    "amount": amount,
                }
            )
            total += amount

        prt_id = generate_name("PRT", tenant_id=self._tenant_id)
        return_doc = {
            "_id": prt_id,
            "supplier": receipt.get("supplier", ""),
            "receipt_reference": receipt_id,
            "return_date": None,
            "reason": reason,
            "items": validated_items,
            "total": round(total, 2),
            "tenant_id": self._tenant_id,
        }
        self._return_repo.insert(return_doc)

        logger.info(
            "구매 반품 생성: %s (입고: %s, 아이템: %d, 금액: %.2f)",
            prt_id,
            receipt_id,
            len(validated_items),
            total,
        )

        return {
            "return_id": prt_id,
            "receipt_reference": receipt_id,
            "item_count": len(validated_items),
            "total": round(total, 2),
        }
