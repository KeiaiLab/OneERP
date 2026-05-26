"""생산능력 계획 서비스 — 가용 시간 산출/계획 생성/충돌 검사.

L2 비즈니스 룰 매핑:
- BR-MFG-014: 기본 가용 시간 (계획 미등록 시 월 176시간)
- BR-MFG-015: 용량 초과 경고 (has_conflict=true)
- BR-MFG-019: 생산계획 일괄 생성 (items 검증)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class CapacityPlanningService:
    """생산능력 계획(Capacity Planning) 비즈니스 로직.

    작업장별 가용 시간 산출, 계획 생성, 용량 초과 검사.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._plan_repo = Repository("capacity_plans", tenant_id=tenant_id)
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)

    def calculate_available_capacity(
        self,
        workstation_id: str,
        period: str,
    ) -> dict[str, Any]:
        """작업장의 잔여 가용 시간을 산출한다.

        Args:
            workstation_id: 작업장 ID
            period: 기간 (예: "2026-03")

        Returns:
            {workstation_id, period, total_hours, planned_hours, available_hours}
        """
        # 해당 기간 계획 조회
        plans = self._plan_repo.find_many(
            {"workstation_id": workstation_id, "period": period},
            limit=1,
        )

        if plans:
            plan = plans[0]
            total_hours = float(plan.get("available_hours", 0))
            planned_hours = float(plan.get("planned_hours", 0))
        else:
            # 기본값: 월 22일 x 8시간 = 176시간
            total_hours = 176.0
            planned_hours = 0.0

        available_hours = total_hours - planned_hours

        return {
            "workstation_id": workstation_id,
            "period": period,
            "total_hours": total_hours,
            "planned_hours": planned_hours,
            "available_hours": max(available_hours, 0),
        }

    def create_capacity_plan(
        self,
        workstation_id: str,
        period: str,
        available_hours: float,
    ) -> dict[str, Any]:
        """생산능력 계획을 생성한다.

        Args:
            workstation_id: 작업장 ID
            period: 기간 (예: "2026-03")
            available_hours: 총 가용 시간

        Returns:
            생성된 계획 문서
        """
        plan_id = generate_name("CPLAN", tenant_id=self._tenant_id)
        plan_doc = {
            "_id": plan_id,
            "workstation_id": workstation_id,
            "period": period,
            "available_hours": available_hours,
            "planned_hours": 0.0,
            "utilization_rate": 0.0,
            "status": "draft",
            "tenant_id": self._tenant_id,
        }
        self._plan_repo.insert(plan_doc)

        logger.info(
            "생산능력 계획 생성: %s (작업장: %s, 가용: %s시간)",
            plan_id,
            workstation_id,
            available_hours,
        )
        return plan_doc

    def check_capacity_conflict(
        self,
        workstation_id: str,
        required_hours: float,
        period: str,
    ) -> dict[str, Any]:
        """용량 초과 여부를 검사한다.

        Args:
            workstation_id: 작업장 ID
            required_hours: 요청 시간
            period: 기간

        Returns:
            {has_conflict, available_hours, required_hours, surplus_or_deficit}
        """
        capacity = self.calculate_available_capacity(workstation_id, period)
        available = capacity["available_hours"]
        surplus = available - required_hours
        has_conflict = surplus < 0

        if has_conflict:
            logger.warning(
                "용량 초과: 작업장 %s, 기간 %s — 부족 %.1f시간",
                workstation_id,
                period,
                abs(surplus),
            )

        return {
            "workstation_id": workstation_id,
            "period": period,
            "has_conflict": has_conflict,
            "available_hours": available,
            "required_hours": required_hours,
            "surplus_or_deficit": surplus,
        }
