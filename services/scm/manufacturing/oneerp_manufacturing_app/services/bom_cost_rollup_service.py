"""BOM 원가 집계(Cost Rollup) 서비스 — 다단계 자재/노무/경비 계산.

ERPNext/Oracle/OpenBOM 베스트 프랙티스를 참고하여, 다단계 BOM의
총원가를 자재비/노무비/경비로 분해해 집계한다.

원가 구성 (Oracle JD Edwards / ERPNext 표준):
- material_cost: 모든 'P'(purchased) 자재의 단가 x 수량 합
- labour_cost: 라우팅 공정의 노동시간 x 시간당 단가 합
- overhead_cost: 작업장 시간당 간접비 x 공정 시간 합 + 자재비 비율 추가비
- total_cost = material + labour + overhead

다단계 처리:
- 하위 BOM이 있는 자재는 재귀 호출하여 sub-cost를 구한 뒤 상위로 전파
- 순환 참조 방지: max_depth=10
- 부산물(by_product) 가치는 총원가에서 차감 (선택)

L2 비즈니스 룰 매핑:
- BR-MFG-004: BOM 전개 깊이 제한 (max_depth=10)
- BR-MFG-016: OEE 산출 (간접비 배분의 기초)
- BR-MFG-018: 차이 분석 (계획 원가 vs 실적 원가)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

DEFAULT_OVERHEAD_RATIO = Decimal("0.0")  # 자재비 대비 간접비 비율 (기본 0%)
MAX_DEPTH = 10


class BOMCostRollupService:
    """BOM 다단계 원가 집계 비즈니스 로직.

    BOM 트리를 재귀적으로 전개하면서 자재비·노무비·경비를 합산한다.
    각 단계의 sub-cost를 캐시하여 중복 계산을 피한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._bom_repo = Repository("boms", tenant_id=tenant_id)
        self._routing_repo = Repository("routings", tenant_id=tenant_id)
        self._operation_repo = Repository("operations", tenant_id=tenant_id)
        self._workstation_repo = Repository("workstations", tenant_id=tenant_id)
        self._cost_repo = Repository("production_costs", tenant_id=tenant_id)
        # 계산 캐시 (item_code → cost dict)
        self._cost_cache: dict[str, dict[str, Decimal]] = {}

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def rollup_cost(
        self,
        bom_id: str,
        *,
        qty: Decimal = Decimal(1),
        overhead_ratio: Decimal = DEFAULT_OVERHEAD_RATIO,
        include_byproducts: bool = False,
    ) -> dict[str, Any]:
        """BOM의 다단계 원가를 집계한다.

        Args:
            bom_id: 최상위 BOM 문서 ID
            qty: 생산 수량 (배수)
            overhead_ratio: 자재비 대비 추가 간접비 비율 (예: 0.10 = 10%)
            include_byproducts: True면 부산물 가치를 총원가에서 차감

        Returns:
            {
                bom_id, item_code, qty,
                material_cost, labour_cost, overhead_cost,
                byproduct_credit, total_cost,
                breakdown: [{item_code, level, qty, material, labour, overhead, total}]
            }

        Raises:
            OneERPError(404): BOM 미존재
            OneERPError(422): qty <= 0
            OneERPError(422): overhead_ratio < 0
        """
        if qty <= 0:
            msg = f"생산 수량은 0보다 커야 합니다: {qty}"
            raise_unprocessable("ERR-MFG-COST-001", msg)
        if overhead_ratio < 0:
            msg = f"간접비 비율은 0 이상이어야 합니다: {overhead_ratio}"
            raise_unprocessable("ERR-MFG-COST-002", msg)

        # 캐시 초기화 (호출 단위)
        self._cost_cache = {}

        bom = self._bom_repo.find_by_id(bom_id)
        if bom is None:
            msg = f"BOM을 찾을 수 없습니다: {bom_id}"
            raise_not_found(msg)
        bom = cast("dict[str, Any]", bom)

        breakdown: list[dict[str, Any]] = []
        rolled = self._rollup_recursive(
            bom=bom,
            qty=qty,
            depth=0,
            overhead_ratio=overhead_ratio,
            breakdown=breakdown,
        )

        # 부산물 가치 차감 (선택)
        byproduct_credit = Decimal(0)
        if include_byproducts:
            byproduct_credit = self._sum_byproducts(bom)
            rolled["total"] -= byproduct_credit
            if rolled["total"] < 0:
                rolled["total"] = Decimal(0)

        result = {
            "bom_id": bom_id,
            "item_code": bom.get("item_code", ""),
            "qty": qty,
            "material_cost": rolled["material"],
            "labour_cost": rolled["labour"],
            "overhead_cost": rolled["overhead"],
            "byproduct_credit": byproduct_credit,
            "total_cost": rolled["total"],
            "breakdown": breakdown,
            "depth_reached": rolled["depth"],
        }

        logger.info(
            "BOM 원가 집계 완료: %s (자재: %s, 노무: %s, 경비: %s, 총: %s)",
            bom_id,
            rolled["material"],
            rolled["labour"],
            rolled["overhead"],
            result["total_cost"],
        )
        return result

    def save_production_cost(
        self,
        bom_id: str,
        *,
        work_order_id: str = "",
        overhead_ratio: Decimal = DEFAULT_OVERHEAD_RATIO,
    ) -> str:
        """원가 집계 결과를 ProductionCost 문서로 저장한다.

        Args:
            bom_id: BOM 문서 ID
            work_order_id: 연결할 작업지시 ID (선택)
            overhead_ratio: 추가 간접비 비율

        Returns:
            저장된 ProductionCost 문서 ID
        """
        rollup = self.rollup_cost(bom_id, overhead_ratio=overhead_ratio)

        from oneerp_core.naming import generate_name

        cost_id = generate_name("PCOST", tenant_id=self._tenant_id)
        cost_doc = {
            "_id": cost_id,
            "tenant_id": self._tenant_id,
            "item_code": rollup["item_code"],
            "item_name": rollup["item_code"],
            "material_cost": rollup["material_cost"],
            "labour_cost": rollup["labour_cost"],
            "overhead_cost": rollup["overhead_cost"],
            "total_cost": rollup["total_cost"],
            "work_order": work_order_id,
            "bom_ref": bom_id,
        }
        self._cost_repo.insert(cost_doc)

        logger.info("ProductionCost 저장: %s (BOM: %s)", cost_id, bom_id)
        return cost_id

    # ------------------------------------------------------------------
    # 재귀 집계
    # ------------------------------------------------------------------

    def _rollup_recursive(
        self,
        *,
        bom: dict[str, Any],
        qty: Decimal,
        depth: int,
        overhead_ratio: Decimal,
        breakdown: list[dict[str, Any]],
    ) -> dict[str, Decimal | int]:
        """재귀적으로 BOM 트리를 순회하며 원가를 집계한다.

        반환 dict: {material, labour, overhead, total, depth}
        """
        if depth >= MAX_DEPTH:
            logger.warning(
                "BOM 전개 최대 깊이 %d 도달: %s — 이하 자재 무시",
                MAX_DEPTH,
                bom.get("_id", ""),
            )
            return {
                "material": Decimal(0),
                "labour": Decimal(0),
                "overhead": Decimal(0),
                "total": Decimal(0),
                "depth": depth,
            }

        item_code = str(bom.get("item_code", ""))
        bom_qty = Decimal(str(bom.get("quantity", 1)))
        if bom_qty <= 0:
            bom_qty = Decimal(1)

        # 1. 자재비 집계
        material = Decimal(0)
        max_depth_reached = depth
        for line in bom.get("items", []):
            line_qty = Decimal(str(line.get("qty", 0))) * (qty / bom_qty)
            line_rate = Decimal(str(line.get("rate", 0)))

            child_bom_id = line.get("bom_id", "")
            if child_bom_id:
                # 하위 BOM 재귀 (말단 자재로 전파)
                child_bom = self._bom_repo.find_by_id(child_bom_id)
                if child_bom:
                    sub = self._rollup_recursive(
                        bom=child_bom,
                        qty=line_qty,
                        depth=depth + 1,
                        overhead_ratio=overhead_ratio,
                        breakdown=breakdown,
                    )
                    material += sub["material"] + sub["labour"] + sub["overhead"]
                    max_depth_reached = max(max_depth_reached, int(sub["depth"]))
                    continue

            line_material = line_qty * line_rate
            material += line_material

        # 2. 노무비/경비 집계 (라우팅 기반)
        labour, base_overhead = self._calculate_routing_cost(item_code, qty, bom_qty)

        # 3. 추가 간접비 (자재비 비율 가산)
        ratio_overhead = material * overhead_ratio
        overhead = base_overhead + ratio_overhead

        total = material + labour + overhead

        breakdown.append(
            {
                "item_code": item_code,
                "level": depth,
                "qty": qty,
                "material": material,
                "labour": labour,
                "overhead": overhead,
                "total": total,
            }
        )

        return {
            "material": material,
            "labour": labour,
            "overhead": overhead,
            "total": total,
            "depth": max_depth_reached,
        }

    # ------------------------------------------------------------------
    # 라우팅/부산물
    # ------------------------------------------------------------------

    def _calculate_routing_cost(
        self,
        item_code: str,
        qty: Decimal,
        base_qty: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """라우팅에서 노무비/경비(base)를 계산한다.

        반환: (labour_cost, overhead_cost) — base는 노무비와 동일 시간으로 가산.
        """
        if not item_code:
            return Decimal(0), Decimal(0)

        routings = self._routing_repo.find_many(
            {"item_code": item_code},
            limit=1,
        )
        if not routings:
            return Decimal(0), Decimal(0)

        routing = routings[0]
        operations = routing.get("operations", [])

        total_labour = Decimal(0)
        total_overhead = Decimal(0)
        scale = qty / base_qty if base_qty > 0 else Decimal(1)

        for op in operations:
            time_in_mins = Decimal(str(op.get("time_in_mins", 0)))
            workstation_id = op.get("workstation", "")

            hourly_rate = self._get_workstation_rate(workstation_id)
            labour_per_op = (time_in_mins / Decimal(60)) * hourly_rate * scale
            total_labour += labour_per_op

            # 경비는 동일 시간을 기준으로 작업장 hourly_overhead를 곱함
            hourly_overhead = self._get_workstation_overhead(workstation_id)
            overhead_per_op = (time_in_mins / Decimal(60)) * hourly_overhead * scale
            total_overhead += overhead_per_op

        return total_labour, total_overhead

    def _get_workstation_rate(self, workstation_id: str) -> Decimal:
        """작업장의 시간당 노무비를 조회한다."""
        if not workstation_id:
            return Decimal(0)

        ws_list = self._workstation_repo.find_many(
            {"_id": workstation_id},
            limit=1,
        )
        if not ws_list:
            return Decimal(0)

        return Decimal(str(ws_list[0].get("hourly_rate", 0)))

    def _get_workstation_overhead(self, workstation_id: str) -> Decimal:
        """작업장의 시간당 간접비를 조회한다 (선택 필드)."""
        if not workstation_id:
            return Decimal(0)

        ws_list = self._workstation_repo.find_many(
            {"_id": workstation_id},
            limit=1,
        )
        if not ws_list:
            return Decimal(0)

        return Decimal(str(ws_list[0].get("hourly_overhead", 0)))

    def _sum_byproducts(self, bom: dict[str, Any]) -> Decimal:
        """BOM 부산물 가치 합계 (총원가에서 차감)."""
        byproducts = bom.get("by_products", [])
        total = Decimal(0)
        for bp in byproducts:
            qty = Decimal(str(bp.get("qty", 0)))
            rate = Decimal(str(bp.get("rate", 0)))
            total += qty * rate
        return total
