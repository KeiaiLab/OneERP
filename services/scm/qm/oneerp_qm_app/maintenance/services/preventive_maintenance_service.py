"""예방보전 서비스 — PM 스케줄링 및 작업지시 자동 생성."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PreventiveMaintenanceService:
    """예방보전 비즈니스 로직.

    예방보전계획에 따라 작업지시를 자동 생성하고,
    실행 날짜와 다음 예정일을 관리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._plan_repo = Repository("preventive_maintenance_plans", tenant_id=tenant_id)
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)
        self._equip_repo = Repository("equipments", tenant_id=tenant_id)

    def generate_work_orders(
        self,
        target_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """기한이 도래한 예방보전계획에 대해 작업지시를 자동 생성한다.

        Args:
            target_date: 기준일 (미지정 시 오늘)

        Returns:
            생성된 작업지시 목록
        """
        if target_date is None:
            target_date = datetime.now(tz=UTC).date()

        # 활성 상태이고 기한이 도래한 계획 조회
        plans = self._plan_repo.find_many({"is_active": True}, limit=10000)

        results: list[dict[str, Any]] = []
        for plan in plans:
            next_due = plan.get("next_due_date")
            if next_due is None:
                # next_due_date가 없으면 start_date 기반으로 판단
                start = plan.get("start_date")
                if start is None:
                    continue
                next_due = start

            # 문자열 → date 변환 (DB에서 문자열로 올 수 있음)
            if isinstance(next_due, str):
                next_due = date.fromisoformat(next_due)

            if next_due > target_date:
                continue

            plan_id = plan["_id"]
            equipment_id = plan.get("equipment_id", "")

            # 설비 존재 확인
            equipment = self._equip_repo.find_by_id(equipment_id)
            if not equipment:
                logger.warning(
                    "PM 계획 %s: 설비 '%s'를 찾을 수 없어 건너뜀",
                    plan_id,
                    equipment_id,
                )
                continue

            # 작업지시 생성
            wo_id = generate_name("WO", tenant_id=self._tenant_id)
            self._wo_repo.insert(
                {
                    "_id": wo_id,
                    "equipment_id": equipment_id,
                    "title": f"예방보전: {plan.get('plan_name', '')}",
                    "work_order_type": "preventive",
                    "priority": "medium",
                    "status": "open",
                    "assigned_team": plan.get("assigned_team", ""),
                    "scheduled_date": target_date,
                    "pm_plan_id": plan_id,
                    "description": plan.get("description", ""),
                    "tenant_id": self._tenant_id,
                },
            )

            # 계획의 마지막 실행일과 다음 예정일 업데이트
            interval_days = int(plan.get("interval_days", 30))
            new_next_due = target_date + timedelta(days=interval_days)
            self._plan_repo.update_by_id(
                plan_id,
                {
                    "last_execution_date": target_date,
                    "next_due_date": new_next_due,
                },
            )

            logger.info(
                "PM 작업지시 생성: %s (계획: %s, 설비: %s)",
                wo_id,
                plan_id,
                equipment_id,
            )
            results.append(
                {
                    "work_order_id": wo_id,
                    "plan_id": plan_id,
                    "equipment_id": equipment_id,
                    "scheduled_date": target_date,
                    "next_due_date": new_next_due,
                },
            )

        logger.info("PM 작업지시 자동 생성 완료: %d건", len(results))
        return results

    def get_upcoming_plans(
        self,
        days_ahead: int = 7,
        reference_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """향후 N일 이내에 기한이 도래하는 예방보전계획을 조회한다.

        Args:
            days_ahead: 조회 기간(일)
            reference_date: 기준일 (미지정 시 오늘)

        Returns:
            기한 도래 예정 계획 목록
        """
        if reference_date is None:
            reference_date = datetime.now(tz=UTC).date()

        cutoff = reference_date + timedelta(days=days_ahead)
        plans = self._plan_repo.find_many({"is_active": True}, limit=10000)

        upcoming: list[dict[str, Any]] = []
        for plan in plans:
            next_due = plan.get("next_due_date")
            if next_due is None:
                continue
            if isinstance(next_due, str):
                next_due = date.fromisoformat(next_due)

            if reference_date <= next_due <= cutoff:
                upcoming.append(plan)

        return upcoming
