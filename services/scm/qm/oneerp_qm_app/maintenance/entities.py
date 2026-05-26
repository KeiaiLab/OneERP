"""설비보전 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

10개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티(작업지시, 고장신고 등)는
services/ 디렉토리에서 비즈니스 로직을 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.breakdown_report import (
    BreakdownReport,
    BreakdownReportCreate,
    BreakdownReportUpdate,
)
from .models.equipment import Equipment, EquipmentCreate, EquipmentUpdate
from .models.equipment_availability import (
    EquipmentAvailability,
    EquipmentAvailabilityCreate,
    EquipmentAvailabilityUpdate,
)
from .models.inspection_checklist import (
    InspectionChecklist,
    InspectionChecklistCreate,
    InspectionChecklistUpdate,
)
from .models.inspection_result import (
    InspectionResult,
    InspectionResultCreate,
    InspectionResultUpdate,
)
from .models.maintenance_record import (
    MaintenanceRecord,
    MaintenanceRecordCreate,
    MaintenanceRecordUpdate,
)
from .models.maintenance_spare_part import (
    MaintenanceSparePart,
    MaintenanceSparePartCreate,
    MaintenanceSparePartUpdate,
)
from .models.maintenance_type import (
    MaintenanceType,
    MaintenanceTypeCreate,
    MaintenanceTypeUpdate,
)
from .models.preventive_maintenance_plan import (
    PreventiveMaintenancePlan,
    PreventiveMaintenancePlanCreate,
    PreventiveMaintenancePlanUpdate,
)
from .models.work_order import WorkOrder, WorkOrderCreate, WorkOrderUpdate

# --- 마스터 문서 ---

EQUIPMENT = EntityMeta(
    collection="equipments",
    prefix="EQ",
    api_path="/api/v1/equipments",
    tag="설비",
    resource="equipment",
    model=Equipment,
    create_schema=EquipmentCreate,
    update_schema=EquipmentUpdate,
    archetype="master",
    not_found_message="설비를 찾을 수 없습니다",
)

MAINTENANCE_TYPE = EntityMeta(
    collection="maintenance_types",
    prefix="MTYPE",
    api_path="/api/v1/maintenance-types",
    tag="보전유형",
    resource="maintenance_type",
    model=MaintenanceType,
    create_schema=MaintenanceTypeCreate,
    update_schema=MaintenanceTypeUpdate,
    archetype="master",
    not_found_message="보전유형을 찾을 수 없습니다",
)

PREVENTIVE_MAINTENANCE_PLAN = EntityMeta(
    collection="preventive_maintenance_plans",
    prefix="PMP",
    api_path="/api/v1/preventive-maintenance-plans",
    tag="예방보전계획",
    resource="preventive_maintenance_plan",
    model=PreventiveMaintenancePlan,
    create_schema=PreventiveMaintenancePlanCreate,
    update_schema=PreventiveMaintenancePlanUpdate,
    archetype="master",
    not_found_message="예방보전계획을 찾을 수 없습니다",
)

MAINTENANCE_SPARE_PART = EntityMeta(
    collection="maintenance_spare_parts",
    prefix="MSP",
    api_path="/api/v1/maintenance-spare-parts",
    tag="보전예비자재",
    resource="maintenance_spare_part",
    model=MaintenanceSparePart,
    create_schema=MaintenanceSparePartCreate,
    update_schema=MaintenanceSparePartUpdate,
    archetype="master",
    not_found_message="보전예비자재를 찾을 수 없습니다",
)

INSPECTION_CHECKLIST = EntityMeta(
    collection="inspection_checklists",
    prefix="ICHK",
    api_path="/api/v1/inspection-checklists",
    tag="점검체크리스트",
    resource="inspection_checklist",
    model=InspectionChecklist,
    create_schema=InspectionChecklistCreate,
    update_schema=InspectionChecklistUpdate,
    archetype="master",
    not_found_message="점검체크리스트를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

WORK_ORDER = EntityMeta(
    collection="work_orders",
    prefix="WO",
    api_path="/api/v1/work-orders",
    tag="작업지시",
    resource="work_order",
    model=WorkOrder,
    create_schema=WorkOrderCreate,
    update_schema=WorkOrderUpdate,
    archetype="transaction",
    not_found_message="작업지시를 찾을 수 없습니다",
)

BREAKDOWN_REPORT = EntityMeta(
    collection="breakdown_reports",
    prefix="BR",
    api_path="/api/v1/breakdown-reports",
    tag="고장신고",
    resource="breakdown_report",
    model=BreakdownReport,
    create_schema=BreakdownReportCreate,
    update_schema=BreakdownReportUpdate,
    archetype="transaction",
    not_found_message="고장신고를 찾을 수 없습니다",
)

MAINTENANCE_RECORD = EntityMeta(
    collection="maintenance_records",
    prefix="MREC",
    api_path="/api/v1/maintenance-records",
    tag="보전작업기록",
    resource="maintenance_record",
    model=MaintenanceRecord,
    create_schema=MaintenanceRecordCreate,
    update_schema=MaintenanceRecordUpdate,
    archetype="transaction",
    not_found_message="보전작업기록을 찾을 수 없습니다",
)

INSPECTION_RESULT = EntityMeta(
    collection="inspection_results",
    prefix="IRES",
    api_path="/api/v1/inspection-results",
    tag="점검결과",
    resource="inspection_result",
    model=InspectionResult,
    create_schema=InspectionResultCreate,
    update_schema=InspectionResultUpdate,
    archetype="transaction",
    not_found_message="점검결과를 찾을 수 없습니다",
)

EQUIPMENT_AVAILABILITY = EntityMeta(
    collection="equipment_availabilities",
    prefix="EQAV",
    api_path="/api/v1/equipment-availabilities",
    tag="설비가동율",
    resource="equipment_availability",
    model=EquipmentAvailability,
    create_schema=EquipmentAvailabilityCreate,
    update_schema=EquipmentAvailabilityUpdate,
    archetype="transaction",
    not_found_message="설비가동율을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    EQUIPMENT,
    MAINTENANCE_TYPE,
    PREVENTIVE_MAINTENANCE_PLAN,
    MAINTENANCE_SPARE_PART,
    INSPECTION_CHECKLIST,
    # 트랜잭션
    WORK_ORDER,
    BREAKDOWN_REPORT,
    MAINTENANCE_RECORD,
    INSPECTION_RESULT,
    EQUIPMENT_AVAILABILITY,
]
