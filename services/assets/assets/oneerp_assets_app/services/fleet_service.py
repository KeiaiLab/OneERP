"""차량/설비 관리 서비스 — 차량 배정, 운행기록, 정비 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-016: 차량 존재 확인 (assign_vehicle 시)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class FleetService:
    """차량 관리 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._vehicle_repo = Repository("vehicles", tenant_id=tenant_id)
        self._assignment_repo = Repository("vehicle_assignments", tenant_id=tenant_id)
        self._log_repo = Repository("vehicle_logs", tenant_id=tenant_id)
        self._fuel_repo = Repository("fuel_entries", tenant_id=tenant_id)
        self._maint_repo = Repository("vehicle_maintenances", tenant_id=tenant_id)

    def assign_vehicle(
        self,
        vehicle_id: str,
        employee: str,
        from_date: Any,
        to_date: Any,
    ) -> dict[str, Any]:
        """차량을 직원에게 배정한다."""
        vehicle = self._vehicle_repo.find_by_id(vehicle_id)
        if not vehicle:
            raise_not_found(f"차량 '{vehicle_id}'을 찾을 수 없습니다")

        assignment_id = generate_name("VA", tenant_id=self._tenant_id)
        self._assignment_repo.insert(
            {
                "_id": assignment_id,
                "vehicle": vehicle_id,
                "employee": employee,
                "from_date": from_date,
                "to_date": to_date,
                "status": "active",
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("차량 배정: %s (%s)", vehicle_id, assignment_id)
        return {"assignment_id": assignment_id, "vehicle": vehicle_id, "employee": employee}

    def record_trip(
        self,
        vehicle_id: str,
        driver: str,
        distance_km: float,
        purpose: str = "",
    ) -> dict[str, Any]:
        """운행 기록을 저장한다."""
        log_id = generate_name("VL", tenant_id=self._tenant_id)
        self._log_repo.insert(
            {
                "_id": log_id,
                "vehicle": vehicle_id,
                "driver": driver,
                "distance_km": distance_km,
                "purpose": purpose,
                "tenant_id": self._tenant_id,
            }
        )
        return {"log_id": log_id, "distance_km": distance_km}

    def get_vehicle_summary(
        self,
        vehicle_id: str,
    ) -> dict[str, Any]:
        """차량의 운행/주유/정비 요약을 조회한다."""
        logs = self._log_repo.find_many({"vehicle": vehicle_id}, limit=10000)
        fuel = self._fuel_repo.find_many({"vehicle": vehicle_id}, limit=10000)
        maint = self._maint_repo.find_many({"vehicle": vehicle_id}, limit=10000)

        total_distance = sum(float(entry.get("distance_km", 0)) for entry in logs)
        total_fuel_cost = sum(float(f.get("amount", 0)) for f in fuel)
        total_maint_cost = sum(float(m.get("cost", 0)) for m in maint)

        return {
            "vehicle_id": vehicle_id,
            "total_trips": len(logs),
            "total_distance_km": round(total_distance, 1),
            "total_fuel_cost": round(total_fuel_cost, 2),
            "total_maintenance_cost": round(total_maint_cost, 2),
            "cost_per_km": round((total_fuel_cost + total_maint_cost) / total_distance, 2)
            if total_distance > 0
            else 0.0,
        }
