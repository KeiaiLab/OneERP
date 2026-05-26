"""BOM 전개 서비스 — 재귀 BOM 전개/트리 구성/원가 산출.

L2 비즈니스 룰 매핑:
- BR-MFG-004: BOM 전개 깊이 제한 (max_depth=10)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class BOMExplosionService:
    """BOM(Bill of Materials) 전개 비즈니스 로직.

    다단계 BOM을 재귀적으로 전개하여 flat 자재 목록,
    트리 구조, 총원가를 계산한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bom_repo = Repository("boms", tenant_id=tenant_id)

    def explode_bom(
        self,
        bom_id: str,
        qty: float = 1.0,
        max_depth: int = 10,
    ) -> list[dict[str, Any]]:
        """BOM을 재귀적으로 전개하여 flat 자재 목록을 반환한다.

        Args:
            bom_id: BOM 문서 ID
            qty: 상위 수량 배수
            max_depth: 최대 전개 깊이 (순환 방지)

        Returns:
            [{item_code, qty, uom, level}] 형태의 flat 자재 목록
        """
        result: list[dict[str, Any]] = []
        self._explode_recursive(bom_id, qty, 0, max_depth, result)
        return result

    def _explode_recursive(
        self,
        bom_id: str,
        parent_qty: float,
        current_depth: int,
        max_depth: int,
        result: list[dict[str, Any]],
    ) -> None:
        """재귀 BOM 전개 내부 함수."""
        if current_depth >= max_depth:
            return

        bom = self._bom_repo.find_by_id(bom_id)
        if not bom:
            return

        for item in bom.get("items", []):
            item_qty = float(item.get("qty", 0)) * parent_qty
            item_code = item.get("item_code", "")
            child_bom_id = item.get("bom_id", "")

            if child_bom_id:
                # 하위 BOM이 있으면 재귀 전개
                self._explode_recursive(
                    child_bom_id,
                    item_qty,
                    current_depth + 1,
                    max_depth,
                    result,
                )
            else:
                # 말단 자재 — flat 목록에 추가 (단가 정보 포함)
                result.append(
                    {
                        "item_code": item_code,
                        "qty": item_qty,
                        "uom": item.get("uom", ""),
                        "level": current_depth + 1,
                        "rate": float(item.get("unit_price", 0)),
                    }
                )

    def get_bom_tree(self, bom_id: str) -> dict[str, Any]:
        """BOM을 nested dict 트리 구조로 반환한다.

        Args:
            bom_id: BOM 문서 ID

        Returns:
            {item_code, qty, children: [...]} 형태의 트리
        """
        bom = self._bom_repo.find_by_id(bom_id)
        if not bom:
            raise OneERPError(
                status_code=404,
                error="ERR-MFG-001",
                detail=f"BOM '{bom_id}'을 찾을 수 없습니다",
            )

        return self._build_tree(bom)

    def _build_tree(self, bom: dict[str, Any]) -> dict[str, Any]:
        """재귀적으로 BOM 트리를 구성한다."""
        children: list[dict[str, Any]] = []
        for item in bom.get("items", []):
            child_bom_id = item.get("bom_id", "")
            if child_bom_id:
                child_bom = self._bom_repo.find_by_id(child_bom_id)
                if child_bom:
                    child_tree = self._build_tree(child_bom)
                    child_tree["qty"] = float(item.get("qty", 0))
                    children.append(child_tree)
            else:
                children.append(
                    {
                        "item_code": item.get("item_code", ""),
                        "qty": float(item.get("qty", 0)),
                        "uom": item.get("uom", ""),
                        "children": [],
                    }
                )

        return {
            "item_code": bom.get("item_code", ""),
            "bom_id": bom.get("_id", ""),
            "qty": 1.0,
            "children": children,
        }

    def calculate_cost(
        self,
        bom_id: str,
        qty: float = 1.0,
    ) -> dict[str, Any]:
        """BOM 전개 결과에 단가를 곱하여 총원가를 산출한다.

        Args:
            bom_id: BOM 문서 ID
            qty: 생산 수량

        Returns:
            {total_cost, items: [{item_code, qty, unit_price, cost}]}
        """
        flat_items = self.explode_bom(bom_id, qty)

        cost_items: list[dict[str, Any]] = []
        total_cost = Decimal(0)

        for item in flat_items:
            # 전개 시 포함된 단가를 직접 사용 (하위 BOM 자재도 올바른 단가 적용)
            unit_price = Decimal(str(item.get("rate", 0)))
            item_cost = Decimal(str(item["qty"])) * unit_price

            cost_items.append(
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "unit_price": unit_price,
                    "cost": item_cost,
                }
            )
            total_cost += item_cost

        return {
            "bom_id": bom_id,
            "qty": qty,
            "total_cost": total_cost,
            "items": cost_items,
        }

    @staticmethod
    def _find_unit_price(bom: dict[str, Any] | None, item_code: str) -> Decimal:
        """BOM 아이템에서 단가를 찾는다."""
        if not bom:
            return Decimal(0)
        for item in bom.get("items", []):
            if item.get("item_code") == item_code:
                return Decimal(str(item.get("unit_price", 0)))
        return Decimal(0)
