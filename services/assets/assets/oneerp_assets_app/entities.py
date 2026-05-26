"""Assets 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

21개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티(자산, 감가상각 등)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.asset_impairment import (
    AssetImpairment,
    AssetImpairmentCreate,
    AssetImpairmentUpdate,
)
from .models.asset_insurance import (
    AssetInsurance,
    AssetInsuranceCreate,
    AssetInsuranceUpdate,
)
from .models.asset_maintenance_plan import (
    AssetMaintenancePlan,
    AssetMaintenancePlanCreate,
    AssetMaintenancePlanUpdate,
)
from .models.asset_repair import AssetRepair, AssetRepairCreate, AssetRepairUpdate
from .models.asset_revaluation import (
    AssetRevaluation,
    AssetRevaluationCreate,
    AssetRevaluationUpdate,
)
from .models.asset_value_adjustment import (
    AssetValueAdjustment,
    AssetValueAdjustmentCreate,
    AssetValueAdjustmentUpdate,
)
from .models.depreciation_comparison import (
    DepreciationComparison,
    DepreciationComparisonCreate,
    DepreciationComparisonUpdate,
)
from .models.equipment_downtime import (
    EquipmentDowntime,
    EquipmentDowntimeCreate,
    EquipmentDowntimeUpdate,
)
from .models.fuel_entry import FuelEntry, FuelEntryCreate, FuelEntryUpdate
from .models.io_t_alert import IoTAlert, IoTAlertCreate, IoTAlertUpdate
from .models.io_t_data_point import (
    IoTDataPoint,
    IoTDataPointCreate,
    IoTDataPointUpdate,
)
from .models.io_t_device import IoTDevice, IoTDeviceCreate, IoTDeviceUpdate
from .models.maintenance_log import (
    MaintenanceLog,
    MaintenanceLogCreate,
    MaintenanceLogUpdate,
)
from .models.maintenance_request import (
    MaintenanceRequest,
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
)
from .models.maintenance_schedule import (
    MaintenanceSchedule,
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
)
from .models.maintenance_visit import (
    MaintenanceVisit,
    MaintenanceVisitCreate,
    MaintenanceVisitUpdate,
)
from .models.spare_part import SparePart, SparePartCreate, SparePartUpdate
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

# --- 트랜잭션 문서 ---

ASSET_REPAIR = EntityMeta(
    collection="asset_repairs",
    prefix="ARPR",
    api_path="/api/v1/asset-repairs",
    tag="자산수리",
    resource="asset_repair",
    model=AssetRepair,
    create_schema=AssetRepairCreate,
    update_schema=AssetRepairUpdate,
    archetype="transaction",
    not_found_message="자산 수리를 찾을 수 없습니다",
)

ASSET_VALUE_ADJUSTMENT = EntityMeta(
    collection="asset_value_adjustments",
    prefix="AVA",
    api_path="/api/v1/asset-value-adjustments",
    tag="자산가치조정",
    resource="asset_value_adjustment",
    model=AssetValueAdjustment,
    create_schema=AssetValueAdjustmentCreate,
    update_schema=AssetValueAdjustmentUpdate,
    archetype="transaction",
    not_found_message="자산 가치 조정을 찾을 수 없습니다",
)

ASSET_REVALUATION = EntityMeta(
    collection="asset_revaluations",
    prefix="ARVAL",
    api_path="/api/v1/asset-revaluations",
    tag="자산재평가",
    resource="asset_revaluation",
    model=AssetRevaluation,
    create_schema=AssetRevaluationCreate,
    update_schema=AssetRevaluationUpdate,
    archetype="transaction",
    not_found_message="자산 재평가를 찾을 수 없습니다",
)

ASSET_IMPAIRMENT = EntityMeta(
    collection="asset_impairments",
    prefix="AIMP",
    api_path="/api/v1/asset-impairments",
    tag="자산손상",
    resource="asset_impairment",
    model=AssetImpairment,
    create_schema=AssetImpairmentCreate,
    update_schema=AssetImpairmentUpdate,
    archetype="transaction",
    not_found_message="자산 손상을 찾을 수 없습니다",
)

ASSET_INSURANCE = EntityMeta(
    collection="asset_insurances",
    prefix="AINS",
    api_path="/api/v1/asset-insurances",
    tag="자산보험",
    resource="asset_insurance",
    model=AssetInsurance,
    create_schema=AssetInsuranceCreate,
    update_schema=AssetInsuranceUpdate,
    archetype="master",
    not_found_message="자산 보험을 찾을 수 없습니다",
)

MAINTENANCE_REQUEST = EntityMeta(
    collection="maintenance_requests",
    prefix="MREQ",
    api_path="/api/v1/maintenance-requests",
    tag="유지보수요청",
    resource="maintenance_request",
    model=MaintenanceRequest,
    create_schema=MaintenanceRequestCreate,
    update_schema=MaintenanceRequestUpdate,
    archetype="transaction",
    not_found_message="유지보수 요청을 찾을 수 없습니다",
)

MAINTENANCE_VISIT = EntityMeta(
    collection="maintenance_visits",
    prefix="MVIS",
    api_path="/api/v1/maintenance-visits",
    tag="유지보수방문",
    resource="maintenance_visit",
    model=MaintenanceVisit,
    create_schema=MaintenanceVisitCreate,
    update_schema=MaintenanceVisitUpdate,
    archetype="transaction",
    not_found_message="유지보수 방문을 찾을 수 없습니다",
)

VEHICLE_ASSIGNMENT = EntityMeta(
    collection="vehicle_assignments",
    prefix="VASN",
    api_path="/api/v1/vehicle-assignments",
    tag="차량배정",
    resource="vehicle_assignment",
    model=VehicleAssignment,
    create_schema=VehicleAssignmentCreate,
    update_schema=VehicleAssignmentUpdate,
    archetype="transaction",
    not_found_message="차량 배정을 찾을 수 없습니다",
)

VEHICLE_MAINTENANCE = EntityMeta(
    collection="vehicle_maintenances",
    prefix="VMNT",
    api_path="/api/v1/vehicle-maintenances",
    tag="차량유지보수",
    resource="vehicle_maintenance",
    model=VehicleMaintenance,
    create_schema=VehicleMaintenanceCreate,
    update_schema=VehicleMaintenanceUpdate,
    archetype="transaction",
    not_found_message="차량 유지보수를 찾을 수 없습니다",
)

MAINTENANCE_SCHEDULE = EntityMeta(
    collection="maintenance_schedules",
    prefix="MSCH",
    api_path="/api/v1/maintenance-schedules",
    tag="유지보수일정",
    resource="maintenance_schedule",
    model=MaintenanceSchedule,
    create_schema=MaintenanceScheduleCreate,
    update_schema=MaintenanceScheduleUpdate,
    archetype="master",
    not_found_message="유지보수 일정을 찾을 수 없습니다",
)

MAINTENANCE_LOG = EntityMeta(
    collection="maintenance_logs",
    prefix="MLOG",
    api_path="/api/v1/maintenance-logs",
    tag="유지보수로그",
    resource="maintenance_log",
    model=MaintenanceLog,
    create_schema=MaintenanceLogCreate,
    update_schema=MaintenanceLogUpdate,
    archetype="transaction",
    not_found_message="유지보수 로그를 찾을 수 없습니다",
)

ASSET_MAINTENANCE_PLAN = EntityMeta(
    collection="asset_maintenance_plans",
    prefix="AMP",
    api_path="/api/v1/asset-maintenance-plans",
    tag="자산유지보수계획",
    resource="asset_maintenance_plan",
    model=AssetMaintenancePlan,
    create_schema=AssetMaintenancePlanCreate,
    update_schema=AssetMaintenancePlanUpdate,
    archetype="master",
    not_found_message="자산 유지보수 계획을 찾을 수 없습니다",
)

EQUIPMENT_DOWNTIME = EntityMeta(
    collection="equipment_downtimes",
    prefix="EQDT",
    api_path="/api/v1/equipment-downtimes",
    tag="장비비가동",
    resource="equipment_downtime",
    model=EquipmentDowntime,
    create_schema=EquipmentDowntimeCreate,
    update_schema=EquipmentDowntimeUpdate,
    archetype="transaction",
    not_found_message="장비 비가동을 찾을 수 없습니다",
)

DEPRECIATION_COMPARISON = EntityMeta(
    collection="depreciation_comparisons",
    prefix="DCMP",
    api_path="/api/v1/depreciation-comparisons",
    tag="감가상각비교",
    resource="depreciation_comparison",
    model=DepreciationComparison,
    create_schema=DepreciationComparisonCreate,
    update_schema=DepreciationComparisonUpdate,
    archetype="transaction",
    not_found_message="감가상각 비교를 찾을 수 없습니다",
)

SPARE_PART = EntityMeta(
    collection="spare_parts",
    prefix="SPRP",
    api_path="/api/v1/spare-parts",
    tag="예비부품",
    resource="spare_part",
    model=SparePart,
    create_schema=SparePartCreate,
    update_schema=SparePartUpdate,
    archetype="master",
    not_found_message="예비 부품을 찾을 수 없습니다",
)

VEHICLE_LOG = EntityMeta(
    collection="vehicle_logs",
    prefix="VLOG",
    api_path="/api/v1/vehicle-logs",
    tag="차량운행일지",
    resource="vehicle_log",
    model=VehicleLog,
    create_schema=VehicleLogCreate,
    update_schema=VehicleLogUpdate,
    archetype="transaction",
    not_found_message="차량 운행 일지를 찾을 수 없습니다",
)

VEHICLE = EntityMeta(
    collection="vehicles",
    prefix="VEH",
    api_path="/api/v1/vehicles",
    tag="차량",
    resource="vehicle",
    model=Vehicle,
    create_schema=VehicleCreate,
    update_schema=VehicleUpdate,
    archetype="master",
    not_found_message="차량을 찾을 수 없습니다",
)

FUEL_ENTRY = EntityMeta(
    collection="fuel_entries",
    prefix="FUEL",
    api_path="/api/v1/fuel-entries",
    tag="연료입력",
    resource="fuel_entry",
    model=FuelEntry,
    create_schema=FuelEntryCreate,
    update_schema=FuelEntryUpdate,
    archetype="transaction",
    not_found_message="연료 입력을 찾을 수 없습니다",
)

# --- IoT ---

IOT_DEVICE = EntityMeta(
    collection="iot_devices",
    prefix="IOTD",
    api_path="/api/v1/iot-devices",
    tag="IoT 디바이스",
    resource="iot_device",
    model=IoTDevice,
    create_schema=IoTDeviceCreate,
    update_schema=IoTDeviceUpdate,
    archetype="master",
    not_found_message="IoT 디바이스를 찾을 수 없습니다",
)

IOT_ALERT = EntityMeta(
    collection="iot_alerts",
    prefix="IOTA",
    api_path="/api/v1/iot-alerts",
    tag="IoT 경보",
    resource="iot_alert",
    model=IoTAlert,
    create_schema=IoTAlertCreate,
    update_schema=IoTAlertUpdate,
    archetype="transaction",
    not_found_message="IoT 경보를 찾을 수 없습니다",
)

IOT_DATA_POINT = EntityMeta(
    collection="iot_data_points",
    prefix="IOTDP",
    api_path="/api/v1/iot-data-points",
    tag="IoT 데이터 포인트",
    resource="iot_data_point",
    model=IoTDataPoint,
    create_schema=IoTDataPointCreate,
    update_schema=IoTDataPointUpdate,
    archetype="transaction",
    not_found_message="IoT 데이터 포인트를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    VEHICLE,
    ASSET_INSURANCE,
    MAINTENANCE_SCHEDULE,
    ASSET_MAINTENANCE_PLAN,
    SPARE_PART,
    # 트랜잭션
    ASSET_REPAIR,
    ASSET_VALUE_ADJUSTMENT,
    ASSET_REVALUATION,
    ASSET_IMPAIRMENT,
    MAINTENANCE_REQUEST,
    MAINTENANCE_VISIT,
    VEHICLE_ASSIGNMENT,
    VEHICLE_MAINTENANCE,
    MAINTENANCE_LOG,
    EQUIPMENT_DOWNTIME,
    DEPRECIATION_COMPARISON,
    VEHICLE_LOG,
    FUEL_ENTRY,
    IOT_DEVICE,
    IOT_ALERT,
    IOT_DATA_POINT,
]
