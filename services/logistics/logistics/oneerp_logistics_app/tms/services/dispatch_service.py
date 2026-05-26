"""배차 서비스 — 수동/자동 배차, 상태 전이, 검증 로직."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import OneERPError
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 배송 건 상태 전이 허용 맵
SHIPMENT_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"pending", "cancelled"},
    "pending": {"dispatched", "draft"},
    "dispatched": {"picked_up", "cancelled"},
    "picked_up": {"in_transit"},
    "in_transit": {"out_for_delivery", "failed"},
    "out_for_delivery": {"delivered", "failed"},
    "failed": {"dispatched", "returned"},
    "delivered": set(),
    "returned": set(),
    "cancelled": set(),
}

# 배차 지시 상태 전이 허용 맵
DO_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"in_progress", "cancelled"},
    "in_progress": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


class DispatchService:
    """배차 비즈니스 로직.

    배차 생성/확정, 상태 전이, 차량/운송사 검증을 처리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._shipment_repo = Repository("shipments", tenant_id=tenant_id)
        self._do_repo = Repository("delivery_orders", tenant_id=tenant_id)
        self._carrier_repo = Repository("carriers", tenant_id=tenant_id)
        self._vehicle_repo = Repository("vehicles", tenant_id=tenant_id)
        self._condition_repo = Repository("delivery_conditions", tenant_id=tenant_id)

    def validate_carrier(self, carrier_id: str) -> dict[str, Any]:
        """운송사 유효성을 검증한다 (BR-TMS-003).

        Returns:
            운송사 문서

        Raises:
            OneERPError: 운송사 미존재 또는 비활성
        """
        carrier = self._carrier_repo.find_by_id(carrier_id)
        if not carrier:
            raise OneERPError(
                status_code=404,
                error="ERR-TMS-021",
                detail=f"운송사를 찾을 수 없습니다: {carrier_id}",
            )
        if not carrier.get("is_active", False):
            raise OneERPError(
                status_code=422,
                error="ERR-TMS-103",
                detail="비활성 운송사입니다",
            )
        return carrier

    def validate_vehicle(
        self,
        vehicle_id: str,
        total_weight_kg: float = 0,
        temperature_requirement: str = "normal",
        overweight_warning_rate: float = 0.1,
    ) -> dict[str, Any]:
        """차량 유효성을 검증한다 (BR-TMS-002/004/009).

        Returns:
            차량 문서

        Raises:
            OneERPError: 차량 미존재/비가용/적재량 초과/온도 불일치
        """
        vehicle = self._vehicle_repo.find_by_id(vehicle_id)
        if not vehicle:
            raise OneERPError(
                status_code=404,
                error="ERR-TMS-022",
                detail=f"차량을 찾을 수 없습니다: {vehicle_id}",
            )

        # BR-TMS-004: 가용 상태 검증
        v_status = vehicle.get("status", "")
        if v_status != "available":
            raise OneERPError(
                status_code=422,
                error="ERR-TMS-104",
                detail=f"차량이 가용 상태가 아닙니다 (현재: {v_status})",
            )

        # BR-TMS-002: 적재량 검증
        max_weight = float(vehicle.get("max_weight_kg", 0))
        if max_weight > 0 and total_weight_kg > 0:
            overflow_ratio = (total_weight_kg - max_weight) / max_weight if max_weight > 0 else 0
            if overflow_ratio > overweight_warning_rate:
                raise OneERPError(
                    status_code=422,
                    error="ERR-TMS-102",
                    detail=(f"차량 적재량 초과 (적재: {total_weight_kg}kg, 한도: {max_weight}kg)"),
                )
            if overflow_ratio > 0:
                logger.warning(
                    "차량 적재량 경고 (적재: %skg, 한도: %skg, 초과율: %.1f%%)",
                    total_weight_kg,
                    max_weight,
                    overflow_ratio * 100,
                )

        # BR-TMS-009: 온도 차량 매칭
        if temperature_requirement != "normal":
            v_temp = vehicle.get("temperature_type", "normal")
            if v_temp != temperature_requirement:
                raise OneERPError(
                    status_code=422,
                    error="ERR-TMS-106",
                    detail="냉장/냉동 차량이 필요합니다",
                )

        return vehicle

    def validate_shipments_for_dispatch(self, shipment_ids: list[str]) -> list[dict[str, Any]]:
        """배차 대상 배송 건을 검증한다 (BR-TMS-012).

        Returns:
            배송 건 목록

        Raises:
            OneERPError: 배송 건 미존재/이미 배차됨
        """
        shipments = []
        for sid in shipment_ids:
            shp = self._shipment_repo.find_by_id(sid)
            if not shp:
                raise OneERPError(
                    status_code=404,
                    error="ERR-TMS-020",
                    detail=f"배송 건을 찾을 수 없습니다: {sid}",
                )
            status = shp.get("status", "")
            do_id = shp.get("delivery_order_id")
            if do_id and status not in ("draft", "cancelled"):
                raise OneERPError(
                    status_code=422,
                    error="ERR-TMS-107",
                    detail="이미 배차된 배송 건입니다",
                )
            shipments.append(shp)
        return shipments

    def validate_shipment_transition(self, current_status: str, target_status: str) -> None:
        """배송 건 상태 전이 유효성을 검증한다.

        Raises:
            OneERPError: 허용되지 않는 상태 전이
        """
        allowed = SHIPMENT_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise OneERPError(
                status_code=422,
                error="ERR-TMS-109",
                detail=f"상태 전이가 허용되지 않습니다: {current_status} → {target_status}",
            )

    def validate_do_transition(self, current_status: str, target_status: str) -> None:
        """배차 지시 상태 전이 유효성을 검증한다.

        Raises:
            OneERPError: 허용되지 않는 상태 전이
        """
        allowed = DO_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise OneERPError(
                status_code=422,
                error="ERR-TMS-109",
                detail=f"상태 전이가 허용되지 않습니다: {current_status} → {target_status}",
            )

    def check_pod_required(self, shipment: dict[str, Any]) -> bool:
        """배송 증빙(POD) 필수 여부를 확인한다 (BR-TMS-007).

        Returns:
            POD 필수 여부
        """
        condition_id = shipment.get("delivery_condition_id")
        if not condition_id:
            return False

        condition = self._condition_repo.find_by_id(condition_id)
        if not condition:
            return False

        return bool(condition.get("requires_pod", True))

    def get_temperature_requirement(self, shipment: dict[str, Any]) -> str:
        """배송 건의 온도 요건을 조회한다.

        Returns:
            온도 요건 (normal/refrigerated/frozen)
        """
        condition_id = shipment.get("delivery_condition_id")
        if not condition_id:
            return "normal"

        condition = self._condition_repo.find_by_id(condition_id)
        if not condition:
            return "normal"

        return condition.get("temperature_requirement", "normal")

    def group_shipments_by_route(
        self, shipments: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """배송 건을 경로(출발지→도착지) 기준으로 그룹핑한다.

        BR-TMS-017: 자동 배차 시 지역 그룹핑

        Returns:
            {route_key: [shipments]} 딕셔너리
        """
        groups: dict[str, list[dict[str, Any]]] = {}
        for shp in shipments:
            ship_from = shp.get("ship_from", {})
            ship_to = shp.get("ship_to", {})
            from_key = ship_from.get("address", "") if isinstance(ship_from, dict) else ""
            to_key = ship_to.get("address", "") if isinstance(ship_to, dict) else ""
            route_key = f"{from_key}→{to_key}"
            if route_key not in groups:
                groups[route_key] = []
            groups[route_key].append(shp)
        return groups
