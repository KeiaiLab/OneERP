"""피킹/포장 서비스 — PickList 생성 및 PackingSlip 흐름 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-STK-008: 피킹 완료 검증 (모든 아이템 picked_qty == qty)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PickPackService:
    """피킹(PickList) → 포장(PackingSlip) 비즈니스 로직.

    판매주문/배송노트에서 피킹 리스트를 생성하고,
    피킹 완료 후 포장 전표를 생성한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._pick_repo = Repository("pick_lists", tenant_id=tenant_id)
        self._pack_repo = Repository("packing_slips", tenant_id=tenant_id)
        self._so_repo = Repository("sales_orders", tenant_id=tenant_id)

    def create_pick_list(
        self,
        sales_order_id: str,
    ) -> dict[str, Any]:
        """판매주문에서 피킹 리스트를 생성한다.

        Args:
            sales_order_id: 판매주문 ID

        Returns:
            생성된 PickList 정보
        """
        so = self._so_repo.find_by_id(sales_order_id)
        if not so:
            msg = f"판매주문 '{sales_order_id}'을 찾을 수 없습니다"
            raise_not_found(msg)

        pick_items = [
            {
                "item_code": item.get("item_code", ""),
                "qty": Decimal(str(item.get("qty", 0))),
                "warehouse": item.get("warehouse", ""),
                "picked_qty": 0,
            }
            for item in so.get("items", [])
        ]

        pl_id = generate_name("PL", tenant_id=self._tenant_id)
        self._pick_repo.insert(
            {
                "_id": pl_id,
                "purpose": "delivery",
                "sales_order": sales_order_id,
                "items": pick_items,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("피킹 리스트 생성: %s (SO: %s)", pl_id, sales_order_id)

        return {
            "pick_list_id": pl_id,
            "sales_order": sales_order_id,
            "item_count": len(pick_items),
        }

    def create_packing_slip(
        self,
        pick_list_id: str,
        delivery_note: str = "",
    ) -> dict[str, Any]:
        """피킹 리스트에서 포장 전표를 생성한다.

        모든 아이템이 피킹 완료되어야 포장 전표 생성 가능.

        Args:
            pick_list_id: 피킹 리스트 ID
            delivery_note: 배송노트 ID (선택)

        Returns:
            생성된 PackingSlip 정보
        """
        pl = self._pick_repo.find_by_id(pick_list_id)
        if not pl:
            msg = f"피킹 리스트 '{pick_list_id}'을 찾을 수 없습니다"
            raise_not_found(msg)

        # 피킹 완료 검증
        items = pl.get("items", [])
        unpicked = [
            item
            for item in items
            if Decimal(str(item.get("picked_qty", 0))) < Decimal(str(item.get("qty", 0)))
        ]
        if unpicked:
            codes = [item.get("item_code", "") for item in unpicked]
            msg = f"미피킹 아이템이 있습니다: {', '.join(codes)}"
            raise_unprocessable("ERR-STK-002", msg)

        pack_items = [
            {
                "item_code": item.get("item_code", ""),
                "qty": Decimal(str(item.get("qty", 0))),
                "net_weight": 0,
                "gross_weight": 0,
            }
            for item in items
        ]

        ps_id = generate_name("PS", tenant_id=self._tenant_id)
        self._pack_repo.insert(
            {
                "_id": ps_id,
                "pick_list": pick_list_id,
                "delivery_note": delivery_note,
                "items": pack_items,
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("포장 전표 생성: %s (PL: %s)", ps_id, pick_list_id)

        return {
            "packing_slip_id": ps_id,
            "pick_list": pick_list_id,
            "item_count": len(pack_items),
        }
