"""고장보전 서비스 — 고장 접수, 작업지시 생성, 완료 처리."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class BreakdownService:
    """고장보전 비즈니스 로직.

    고장신고 접수 → 작업지시 생성 → 완료 처리 → 설비 지표 업데이트
    흐름을 관리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._br_repo = Repository("breakdown_reports", tenant_id=tenant_id)
        self._wo_repo = Repository("work_orders", tenant_id=tenant_id)
        self._equip_repo = Repository("equipments", tenant_id=tenant_id)

    def create_work_order_from_breakdown(
        self,
        breakdown_report_id: str,
    ) -> dict[str, Any]:
        """고장신고로부터 작업지시를 생성한다.

        고장신고 상태를 work_order_created로 변경하고,
        새 작업지시를 생성한다.

        Args:
            breakdown_report_id: 고장신고 ID

        Returns:
            생성된 작업지시 정보
        """
        br = self._br_repo.find_by_id(breakdown_report_id)
        if not br:
            msg = f"고장신고 '{breakdown_report_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        current_status = br.get("status", "reported")
        if current_status not in ("reported", "acknowledged"):
            msg = f"고장신고 상태가 '{current_status}'이므로 작업지시를 생성할 수 없습니다"
            raise ValueError(msg)

        equipment_id = br.get("equipment_id", "")

        # 우선순위 매핑: 고장 심각도 → 작업지시 우선순위
        severity = br.get("severity", "major")
        priority_map = {
            "minor": "low",
            "major": "high",
            "critical": "critical",
        }
        priority = priority_map.get(severity, "medium")

        wo_id = generate_name("WO", tenant_id=self._tenant_id)
        now = datetime.now(tz=UTC)

        self._wo_repo.insert(
            {
                "_id": wo_id,
                "equipment_id": equipment_id,
                "title": f"고장수리: {br.get('failure_mode', '미상')}",
                "work_order_type": "corrective",
                "priority": priority,
                "status": "open",
                "breakdown_report_id": breakdown_report_id,
                "description": br.get("description", ""),
                "scheduled_date": now.date(),
                "tenant_id": self._tenant_id,
            },
        )

        # 고장신고 상태 업데이트
        self._br_repo.update_by_id(
            breakdown_report_id,
            {
                "status": "work_order_created",
                "work_order_id": wo_id,
                "acknowledged_at": now,
            },
        )

        # 설비 상태를 under_maintenance로 변경
        if equipment_id:
            self._equip_repo.update_by_id(
                equipment_id,
                {"status": "under_maintenance"},
            )

        logger.info(
            "고장 작업지시 생성: %s (고장신고: %s, 설비: %s)",
            wo_id,
            breakdown_report_id,
            equipment_id,
        )
        return {
            "work_order_id": wo_id,
            "breakdown_report_id": breakdown_report_id,
            "equipment_id": equipment_id,
            "priority": priority,
        }

    def complete_work_order(
        self,
        work_order_id: str,
        *,
        labor_hours: float = 0.0,
        material_cost: Decimal = Decimal(0),
        labor_cost: Decimal = Decimal(0),
        root_cause: str = "",
        resolution: str = "",
    ) -> dict[str, Any]:
        """작업지시를 완료 처리한다.

        작업지시 상태를 completed로 변경하고, 비용을 기록한다.
        연관된 고장신고가 있으면 resolved로 변경한다.
        설비 상태를 active로 복원한다.

        Args:
            work_order_id: 작업지시 ID
            labor_hours: 투입 공수(시간)
            material_cost: 자재비
            labor_cost: 인건비
            root_cause: 근본 원인
            resolution: 조치 내용

        Returns:
            완료 처리 결과
        """
        wo = self._wo_repo.find_by_id(work_order_id)
        if not wo:
            msg = f"작업지시 '{work_order_id}'를 찾을 수 없습니다"
            raise ValueError(msg)

        current_status = wo.get("status", "draft")
        if current_status in ("completed", "cancelled"):
            msg = f"작업지시 상태가 '{current_status}'이므로 완료 처리할 수 없습니다"
            raise ValueError(msg)

        now = datetime.now(tz=UTC)
        total_cost = material_cost + labor_cost

        # 작업지시 업데이트
        self._wo_repo.update_by_id(
            work_order_id,
            {
                "status": "completed",
                "actual_end": now,
                "labor_hours": labor_hours,
                "material_cost": str(material_cost),
                "labor_cost": str(labor_cost),
                "total_cost": str(total_cost),
                "root_cause": root_cause,
                "resolution": resolution,
            },
        )

        equipment_id = wo.get("equipment_id", "")
        breakdown_report_id = wo.get("breakdown_report_id", "")

        # 연관 고장신고 resolved 처리
        if breakdown_report_id:
            self._br_repo.update_by_id(
                breakdown_report_id,
                {
                    "status": "resolved",
                    "resolved_at": now,
                },
            )

        # 설비 상태 복원 및 고장 횟수 증가
        if equipment_id:
            equipment = self._equip_repo.find_by_id(equipment_id)
            if equipment:
                updates: dict[str, Any] = {"status": "active"}
                if breakdown_report_id:
                    # 고장 수리인 경우 고장 횟수 증가
                    failure_count = int(equipment.get("failure_count", 0)) + 1
                    updates["failure_count"] = failure_count
                self._equip_repo.update_by_id(equipment_id, updates)

        logger.info(
            "작업지시 완료: %s (공수: %.1fh, 비용: %s)",
            work_order_id,
            labor_hours,
            total_cost,
        )
        return {
            "work_order_id": work_order_id,
            "status": "completed",
            "labor_hours": labor_hours,
            "total_cost": str(total_cost),
            "equipment_id": equipment_id,
        }
