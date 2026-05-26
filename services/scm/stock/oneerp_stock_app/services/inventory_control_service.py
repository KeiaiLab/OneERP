"""재고 관리 서비스 — 안전재고/리오더/순환재고조사 엔진.

L2 비즈니스 룰 매핑:
- BR-STK-016: 안전재고 미달 알림 (current_qty < minimum_qty 시 알림 대상)
- BR-STK-017: 리오더 포인트 도달 알림 (current_qty <= reorder_level 시 재발주 대상)
- BR-STK-018: 순환재고조사 차이 계산 (counted_qty vs system_qty 비교)
"""

from __future__ import annotations

import logging
from decimal import Decimal

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class InventoryControlService:
    """안전재고·리오더·순환재고조사 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bin_repo = Repository("stock_bins", tenant_id=tenant_id)
        self._safety_repo = Repository("safety_stock_rules", tenant_id=tenant_id)
        self._reorder_repo = Repository("reorder_levels", tenant_id=tenant_id)
        self._cycle_repo = Repository("cycle_counts", tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # BR-STK-016: 안전재고 알림
    # ------------------------------------------------------------------

    def check_safety_stock_alerts(self) -> list[dict]:
        """BR-STK-016: 안전재고 미달 품목 목록을 반환한다.

        safety_stock_rules에서 규칙 조회 → stock_bins에서 현재 수량 비교.
        current_qty < minimum_qty이면 알림 대상.

        Returns:
            알림 대상 목록 [{item_code, warehouse_id, current_qty, minimum_qty, shortfall}]
        """
        rules = self._safety_repo.find_many({}, limit=1000)
        if not rules:
            return []

        alerts: list[dict] = []
        for rule in rules:
            item_code = rule.get("item_code", "")
            warehouse_id = rule.get("warehouse_id", "")
            minimum_qty = Decimal(str(rule.get("minimum_qty", 0)))

            current_qty = self._get_bin_qty(item_code, warehouse_id)

            if current_qty < minimum_qty:
                shortfall = minimum_qty - current_qty
                alerts.append(
                    {
                        "item_code": item_code,
                        "warehouse_id": warehouse_id,
                        "current_qty": current_qty,
                        "minimum_qty": minimum_qty,
                        "shortfall": shortfall,
                    }
                )

        logger.info("안전재고 알림 점검 완료: %d건 미달", len(alerts))
        return alerts

    # ------------------------------------------------------------------
    # BR-STK-017: 리오더 포인트
    # ------------------------------------------------------------------

    def check_reorder_points(self) -> list[dict]:
        """BR-STK-017: 리오더 포인트 도달 품목 목록을 반환한다.

        reorder_levels에서 규칙 조회 → stock_bins에서 현재 수량 비교.
        current_qty <= reorder_level이면 재발주 대상.

        Returns:
            재발주 대상 목록 [{item_code, warehouse, current_qty, reorder_level, reorder_qty}]
        """
        rules = self._reorder_repo.find_many({}, limit=1000)
        if not rules:
            return []

        reorder_items: list[dict] = []
        for rule in rules:
            item_code = rule.get("item_code", "")
            warehouse = rule.get("warehouse", "")
            reorder_level = Decimal(str(rule.get("reorder_level", 0)))
            reorder_qty = Decimal(str(rule.get("reorder_qty", 0)))

            current_qty = self._get_bin_qty(item_code, warehouse)

            if current_qty <= reorder_level:
                reorder_items.append(
                    {
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "current_qty": current_qty,
                        "reorder_level": reorder_level,
                        "reorder_qty": reorder_qty,
                    }
                )

        logger.info("리오더 포인트 점검 완료: %d건 재발주 대상", len(reorder_items))
        return reorder_items

    # ------------------------------------------------------------------
    # BR-STK-018: 순환재고조사
    # ------------------------------------------------------------------

    def execute_cycle_count(self, cycle_count_id: str) -> dict:
        """BR-STK-018: 순환재고조사 차이를 계산한다.

        cycle_counts 문서 조회 → actual_qty vs system_qty(stock_bins) 비교.
        variance = actual_qty - system_qty.

        Args:
            cycle_count_id: 순환재고조사 문서 ID

        Returns:
            {cycle_count_id, items: [{item_code, warehouse_id, system_qty, counted_qty, variance}],
             total_variance}

        Raises:
            OneERPError(404): 순환재고조사 문서를 찾을 수 없을 때
            OneERPError(422): 이미 완료된 순환재고조사를 다시 실행할 때
        """
        cc_doc = self._cycle_repo.find_by_id(cycle_count_id)
        if not cc_doc:
            msg = f"순환재고조사를 찾을 수 없습니다: {cycle_count_id}"
            raise_not_found(msg)

        # 이미 완료된 조사는 재실행 불가
        status = cc_doc.get("status", "draft")
        if status == "completed":
            msg = f"이미 완료된 순환재고조사입니다: {cycle_count_id}"
            raise_unprocessable("ERR-STK-003", msg)

        item_code = cc_doc.get("item_code", "")
        warehouse_id = cc_doc.get("warehouse_id", "")
        counted_qty = Decimal(str(cc_doc.get("actual_qty", 0)))

        # stock_bins에서 시스템 수량 조회
        system_qty = self._get_bin_qty(item_code, warehouse_id)
        variance = counted_qty - system_qty

        items = [
            {
                "item_code": item_code,
                "warehouse_id": warehouse_id,
                "system_qty": system_qty,
                "counted_qty": counted_qty,
                "variance": variance,
            }
        ]

        # 문서에 시스템 수량과 차이를 기록하고 상태를 완료로 변경
        self._cycle_repo.update_by_id(
            cycle_count_id,
            {
                "system_qty": system_qty,
                "variance": variance,
                "status": "completed",
            },
        )

        logger.info(
            "순환재고조사 완료: %s (품목: %s, 차이: %s)",
            cycle_count_id,
            item_code,
            variance,
        )

        return {
            "cycle_count_id": cycle_count_id,
            "items": items,
            "total_variance": variance,
        }

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _get_bin_qty(self, item_code: str, warehouse: str) -> Decimal:
        """stock_bins에서 현재 수량을 조회한다.

        warehouse 필드명이 safety_stock_rules는 warehouse_id,
        reorder_levels는 warehouse를 사용하므로 양쪽 모두 지원한다.
        """
        bins = self._bin_repo.find_many(
            {"item_code": item_code, "warehouse": warehouse},
            limit=1,
        )
        if bins:
            return Decimal(str(bins[0].get("current_qty", 0)))
        return Decimal(0)
