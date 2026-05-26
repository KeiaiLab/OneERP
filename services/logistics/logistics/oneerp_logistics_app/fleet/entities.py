"""Fleet 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

5개 엔티티를 EntityMeta로 선언한다.
TCO 보고서는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.fuel_entry import FuelEntry, FuelEntryCreate, FuelEntryUpdate
from .models.vehicle import Vehicle, VehicleCreate, VehicleUpdate
from .models.vehicle_assignment import (
    VehicleAssignment,
    VehicleAssignmentCreate,
    VehicleAssignmentUpdate,
)
from .models.vehicle_log import VehicleLog, VehicleLogCreate, VehicleLogUpdate
from .models.vehicle_maintenance import (
    VehicleMaintenance,
    VehicleMaintenanceCreate,
    VehicleMaintenanceUpdate,
)

# --- 마스터 데이터 ---

VEHICLE = EntityMeta(
    collection="vehicles",
    prefix="VH",
    api_path="/api/v1/vehicles",
    tag="차량",
    resource="vehicle",
    model=Vehicle,
    create_schema=VehicleCreate,
    update_schema=VehicleUpdate,
    archetype="master",
    not_found_message="차량을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

VEHICLE_ASSIGNMENT = EntityMeta(
    collection="vehicle_assignments",
    prefix="VHA",
    api_path="/api/v1/vehicle-assignments",
    tag="차량 배정",
    resource="vehicle_assignment",
    model=VehicleAssignment,
    create_schema=VehicleAssignmentCreate,
    update_schema=VehicleAssignmentUpdate,
    archetype="transaction",
    not_found_message="차량 배정을 찾을 수 없습니다",
)

VEHICLE_LOG = EntityMeta(
    collection="vehicle_logs",
    prefix="VHL",
    api_path="/api/v1/vehicle-logs",
    tag="운행 기록",
    resource="vehicle_log",
    model=VehicleLog,
    create_schema=VehicleLogCreate,
    update_schema=VehicleLogUpdate,
    archetype="transaction",
    not_found_message="운행 기록을 찾을 수 없습니다",
)

FUEL_ENTRY = EntityMeta(
    collection="fuel_entries",
    prefix="FE",
    api_path="/api/v1/fuel-entries",
    tag="주유 기록",
    resource="fuel_entry",
    model=FuelEntry,
    create_schema=FuelEntryCreate,
    update_schema=FuelEntryUpdate,
    archetype="transaction",
    not_found_message="주유 기록을 찾을 수 없습니다",
)

VEHICLE_MAINTENANCE = EntityMeta(
    collection="vehicle_maintenances",
    prefix="VM",
    api_path="/api/v1/vehicle-maintenances",
    tag="차량 정비",
    resource="vehicle_maintenance",
    model=VehicleMaintenance,
    create_schema=VehicleMaintenanceCreate,
    update_schema=VehicleMaintenanceUpdate,
    archetype="transaction",
    not_found_message="차량 정비를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    VEHICLE,
    # 트랜잭션
    VEHICLE_ASSIGNMENT,
    VEHICLE_LOG,
    FUEL_ENTRY,
    VEHICLE_MAINTENANCE,
]
