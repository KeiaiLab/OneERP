"""TCO(Total Cost of Ownership) 분석 서비스."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class TcoService:
    """차량별 총소유비용(TCO) 분석 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._vehicle_repo = Repository("vehicles", tenant_id=tenant_id)
        self._fuel_repo = Repository("fuel_entries", tenant_id=tenant_id)
        self._maintenance_repo = Repository("vehicle_maintenances", tenant_id=tenant_id)

    def calculate_tco(self, vehicle_id: str) -> dict[str, Any]:
        """차량의 TCO를 계산한다.

        TCO = 취득가액 + 유류비 합계 + 정비비 합계.
        """
        vehicle = self._vehicle_repo.find_by_id(vehicle_id)
        if not vehicle:
            logger.warning("TCO 계산 실패: 차량 %s 없음", vehicle_id)
            return {"error": "차량을 찾을 수 없습니다"}

        acquisition_cost = Decimal(str(vehicle.get("acquisition_cost", 0)))

        # 유류비 합산
        fuel_entries = self._fuel_repo.find_many(
            query={"vehicle": vehicle_id},
        )
        total_fuel_cost = sum(Decimal(str(entry.get("amount", 0))) for entry in fuel_entries)

        # 정비비 합산
        maintenance_entries = self._maintenance_repo.find_many(
            query={"vehicle": vehicle_id},
        )
        total_maintenance_cost = sum(
            Decimal(str(entry.get("cost", 0))) for entry in maintenance_entries
        )

        tco = acquisition_cost + total_fuel_cost + total_maintenance_cost

        logger.info(
            "TCO 계산 완료: 차량=%s, 취득=%s, 유류=%s, 정비=%s, 합계=%s",
            vehicle_id,
            acquisition_cost,
            total_fuel_cost,
            total_maintenance_cost,
            tco,
        )

        return {
            "vehicle_id": vehicle_id,
            "vehicle_name": vehicle.get("vehicle_name", ""),
            "acquisition_cost": str(acquisition_cost),
            "total_fuel_cost": str(total_fuel_cost),
            "total_maintenance_cost": str(total_maintenance_cost),
            "tco": str(tco),
        }
