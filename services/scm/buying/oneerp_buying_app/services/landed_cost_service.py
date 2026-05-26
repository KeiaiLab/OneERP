"""부대비용 배분 서비스 — 입고 아이템에 부대비용을 배분하는 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-BUY-005: 부대비용 배분 (qty=수량비율, amount=금액비율)
- BR-BUY-018: 부대비용 총액 = SUM(items.amount)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class LandedCostService:
    """부대비용(Landed Cost) 배분 비즈니스 로직.

    입고 전표의 아이템에 부대비용(운송비, 관세, 보험료 등)을
    수량 또는 금액 비율로 배분한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._lcv_repo = Repository("landed_cost_vouchers", tenant_id=tenant_id)
        self._receipt_repo = Repository("purchase_receipts", tenant_id=tenant_id)

    def allocate_costs(
        self,
        lcv_id: str,
    ) -> dict[str, Any]:
        """BR-BUY-005: 부대비용을 입고 아이템에 배분한다.

        LCV 문서의 items(부대비용 항목)을 receipt 아이템에 배분.
        배분 방식: qty(수량 비율) 또는 amount(금액 비율).

        Args:
            lcv_id: 부대비용전표 ID

        Returns:
            배분 결과 (allocations)
        """
        lcv = self._lcv_repo.find_by_id(lcv_id)
        if not lcv:
            raise_not_found(f"부대비용전표 '{lcv_id}'을 찾을 수 없습니다")

        receipt_id = lcv.get("receipt_document", "")
        receipt = self._receipt_repo.find_by_id(receipt_id)
        if not receipt:
            raise_not_found(f"입고전표 '{receipt_id}'을 찾을 수 없습니다")

        receipt_items = receipt.get("items", [])
        if not receipt_items:
            raise_bad_request("ERR-BUY-002: 입고전표에 아이템이 없습니다")

        # 배분 기준 합계 계산
        total_qty = sum(float(item.get("qty", 0)) for item in receipt_items)
        total_amount = sum(float(item.get("amount", 0)) for item in receipt_items)

        # 부대비용 항목별 배분
        lcv_items = lcv.get("items", [])
        total_landed_cost = sum(float(ci.get("tax_amount", 0)) for ci in lcv_items)

        allocations: list[dict[str, Any]] = []
        for receipt_item in receipt_items:
            item_code = receipt_item.get("item_code", "")
            item_qty = float(receipt_item.get("qty", 0))
            item_amount = float(receipt_item.get("amount", 0))

            allocated_cost = 0.0
            for cost_item in lcv_items:
                cost_amount = float(cost_item.get("tax_amount", 0))
                method = cost_item.get("allocation_method", "qty")

                if method == "qty" and total_qty > 0:
                    allocated_cost += cost_amount * (item_qty / total_qty)
                elif method == "amount" and total_amount > 0:
                    allocated_cost += cost_amount * (item_amount / total_amount)

            allocations.append(
                {
                    "item_code": item_code,
                    "original_amount": item_amount,
                    "landed_cost": round(allocated_cost, 2),
                    "total_cost": round(item_amount + allocated_cost, 2),
                }
            )

        logger.info(
            "부대비용 배분: %s (입고: %s, 부대비용: %.2f, 아이템: %d개)",
            lcv_id,
            receipt_id,
            total_landed_cost,
            len(allocations),
        )

        return {
            "lcv_id": lcv_id,
            "receipt_document": receipt_id,
            "total_landed_cost": total_landed_cost,
            "allocations": allocations,
        }
