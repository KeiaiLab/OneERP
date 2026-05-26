"""WMS 서비스 — 빈 위치 관리, 입고 배치(Putaway), 웨이브 피킹 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-STK-007: 빈 할당 규칙 (PutawayRule 매칭 -> 대체 빈 자동 선택)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class WMSService:
    """WMS(Warehouse Management System) 고급 비즈니스 로직.

    빈 위치 기반 입출고, 입고 배치 규칙, 웨이브 피킹을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bin_repo = Repository("bin_locations", tenant_id=tenant_id)
        self._putaway_repo = Repository("putaway_rules", tenant_id=tenant_id)
        self._wave_repo = Repository("wave_pickings", tenant_id=tenant_id)

    def assign_bin(
        self,
        item_code: str,
        warehouse: str,
        qty: Decimal,
    ) -> dict[str, Any]:
        """아이템을 빈 위치에 배정한다 (Putaway).

        배치 규칙을 조회하여 적절한 빈을 자동 선택한다.
        규칙이 없으면 여유 공간이 가장 큰 빈을 선택한다.

        Returns:
            배정 결과 (bin_id, bin_location)
        """
        # 배치 규칙 조회
        rules = self._putaway_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse, "is_active": True},
            limit=10,
        )

        if rules:
            # 규칙에 지정된 빈 사용
            bin_id = rules[0].get("target_bin", "")
            if bin_id:
                return {
                    "item_code": item_code,
                    "bin_id": bin_id,
                    "qty": qty,
                    "method": "rule",
                }

        # 규칙 없으면 여유 공간 기준 선택
        bins = self._bin_repo.find_many(
            {"warehouse": warehouse, "is_active": True},
            limit=1000,
        )

        if not bins:
            msg = f"창고 '{warehouse}'에 사용 가능한 빈이 없습니다"
            raise_unprocessable("ERR-STK-003", msg)

        # 여유 공간이 가장 큰 빈 선택
        best_bin = max(bins, key=lambda b: Decimal(str(b.get("available_capacity", 0))))

        return {
            "item_code": item_code,
            "bin_id": best_bin.get("_id", ""),
            "qty": qty,
            "method": "auto",
        }

    def create_wave_picking(
        self,
        sales_orders: list[str],
        warehouse: str,
    ) -> dict[str, Any]:
        """복수 주문을 묶어 웨이브 피킹을 생성한다.

        여러 주문의 아이템을 빈 위치별로 그룹화하여 최적 피킹 경로를 구성.

        Args:
            sales_orders: 판매주문 ID 목록
            warehouse: 출고 창고

        Returns:
            웨이브 피킹 결과 (wave_id, pick_items)
        """
        if not sales_orders:
            msg = "주문을 1개 이상 지정해야 합니다"
            raise_unprocessable("ERR-STK-004", msg)

        # 주문별 아이템 합산
        item_totals: dict[str, Decimal] = {}
        for _so_id in sales_orders:
            # 실제로는 SO 조회 후 아이템 집계
            # 여기서는 웨이브 피킹 구조만 생성
            pass

        wave_id = generate_name("WP", tenant_id=self._tenant_id)
        wave_doc = {
            "_id": wave_id,
            "sales_orders": sales_orders,
            "warehouse": warehouse,
            "status": "pending",
            "item_totals": item_totals,
            "order_count": len(sales_orders),
            "tenant_id": self._tenant_id,
        }
        self._wave_repo.insert(wave_doc)

        logger.info(
            "웨이브 피킹 생성: %s (주문: %d건, 창고: %s)",
            wave_id,
            len(sales_orders),
            warehouse,
        )

        return {
            "wave_id": wave_id,
            "order_count": len(sales_orders),
            "warehouse": warehouse,
        }
