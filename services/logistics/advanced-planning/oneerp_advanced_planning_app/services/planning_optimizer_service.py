"""계획 최적화 서비스 — 수요/공급 밸런싱, 시나리오 분석, 능력 계산."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PlanningOptimizerService:
    """계획 최적화 비즈니스 로직.

    수요-공급 밸런싱, What-if 시나리오 분석,
    생산능력 가용률 계산을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._demand_repo = Repository("demand_plans", tenant_id=tenant_id)
        self._supply_repo = Repository("supply_plans", tenant_id=tenant_id)
        self._capacity_repo = Repository("capacity_plans", tenant_id=tenant_id)
        self._scenario_repo = Repository("planning_scenarios", tenant_id=tenant_id)

    def balance_demand_supply(
        self,
        item_code: str,
        warehouse: str = "",
    ) -> dict[str, Any]:
        """수요-공급 밸런싱을 수행한다.

        Args:
            item_code: 품목 코드
            warehouse: 창고 코드 (선택)

        Returns:
            밸런싱 결과 (total_demand, total_supply, gap, recommendations)
        """
        # 수요 조회
        demand_query: dict[str, Any] = {"item_code": item_code, "status": "active"}
        if warehouse:
            demand_query["warehouse"] = warehouse
        demands = self._demand_repo.find_many(demand_query, limit=100)

        # 공급 조회
        supply_query: dict[str, Any] = {
            "item_code": item_code,
            "status": {"$in": ["confirmed", "in_progress"]},
        }
        if warehouse:
            supply_query["warehouse"] = warehouse
        supplies = self._supply_repo.find_many(supply_query, limit=100)

        total_demand = sum(Decimal(str(d.get("forecast_qty", 0))) for d in demands)
        total_supply = sum(Decimal(str(s.get("planned_qty", 0))) for s in supplies)
        gap = total_supply - total_demand

        recommendations: list[str] = []
        if gap < 0:
            recommendations.append(f"공급 부족: {abs(gap)} 단위 추가 조달 필요")
        elif gap > total_demand * Decimal("0.2"):
            recommendations.append(f"과잉 공급: {gap} 단위 재고 과다 예상")

        logger.info(
            "수요-공급 밸런싱: %s — 수요: %s, 공급: %s, 갭: %s",
            item_code,
            total_demand,
            total_supply,
            gap,
        )

        return {
            "item_code": item_code,
            "warehouse": warehouse,
            "total_demand": float(total_demand),
            "total_supply": float(total_supply),
            "gap": float(gap),
            "demand_count": len(demands),
            "supply_count": len(supplies),
            "recommendations": recommendations,
        }

    def run_scenario(self, scenario_id: str) -> dict[str, Any]:
        """What-if 시나리오를 실행한다.

        기본 수요계획에 조정 비율을 적용하고 결과를 산출한다.

        Args:
            scenario_id: 시나리오 ID

        Returns:
            시나리오 실행 결과 (adjusted_demand, estimated_cost 등)

        Raises:
            ValueError: 시나리오 미존재
        """
        scenario = self._scenario_repo.find_by_id(scenario_id)
        if not scenario:
            msg = f"계획 시나리오를 찾을 수 없습니다: {scenario_id}"
            raise ValueError(msg)

        # 상태 업데이트
        self._scenario_repo.update_by_id(scenario_id, {"status": "running"})

        # 기본 수요계획 조회
        base_plan_id = scenario.get("base_demand_plan_id", "")
        base_plan = self._demand_repo.find_by_id(base_plan_id) if base_plan_id else None

        base_qty = Decimal(str(base_plan.get("forecast_qty", 0))) if base_plan else Decimal(0)
        adjustment = Decimal(str(scenario.get("demand_adjustment", 0)))

        # 수요 조정 적용
        adjusted_qty = base_qty * (Decimal(1) + adjustment / Decimal(100))

        # 비용 추정 (단순 모델: 단위당 비용 * 조정 수량)
        assumptions = scenario.get("assumptions", {})
        unit_cost = Decimal(str(assumptions.get("unit_cost", 1000)))
        estimated_cost = adjusted_qty * unit_cost

        results = {
            "base_qty": float(base_qty),
            "adjusted_qty": float(adjusted_qty),
            "adjustment_percent": float(adjustment),
            "estimated_cost": float(estimated_cost),
            "unit_cost": float(unit_cost),
        }

        self._scenario_repo.update_by_id(
            scenario_id,
            {"status": "completed", "results": results},
        )

        logger.info(
            "시나리오 실행 완료: %s — 기본: %s, 조정: %s, 비용: %s",
            scenario_id,
            base_qty,
            adjusted_qty,
            estimated_cost,
        )

        return {"scenario_id": scenario_id, "status": "completed", **results}

    def calculate_utilization(self, workstation: str = "") -> dict[str, Any]:
        """생산능력 가용률을 계산한다.

        Args:
            workstation: 워크스테이션 코드 (미지정 시 전체)

        Returns:
            가용률 결과 (plans, average_utilization)
        """
        query: dict[str, Any] = {"status": "active"}
        if workstation:
            query["workstation"] = workstation

        plans = self._capacity_repo.find_many(query, limit=100)

        plan_results: list[dict[str, Any]] = []
        total_utilization = Decimal(0)

        for plan in plans:
            available = Decimal(str(plan.get("available_hours", 0)))
            planned = Decimal(str(plan.get("planned_hours", 0)))

            utilization = Decimal(0)
            if available > 0:
                utilization = (planned / available * 100).quantize(Decimal("0.01"))

            plan_results.append(
                {
                    "workstation": plan.get("workstation", ""),
                    "available_hours": float(available),
                    "planned_hours": float(planned),
                    "utilization_percent": float(utilization),
                }
            )
            total_utilization += utilization

        avg_utilization = Decimal(0)
        if plan_results:
            avg_utilization = (total_utilization / Decimal(str(len(plan_results)))).quantize(
                Decimal("0.01")
            )

        return {
            "workstation_filter": workstation,
            "plans": plan_results,
            "plan_count": len(plan_results),
            "average_utilization": float(avg_utilization),
        }
