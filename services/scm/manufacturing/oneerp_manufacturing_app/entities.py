"""Manufacturing 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

15개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.bom_revision import BOMRevision, BomRevisionCreate, BomRevisionUpdate
from .models.bom_tree import BOMTree, BomTreeCreate, BomTreeUpdate
from .models.by_product import ByProduct, ByProductCreate, ByProductUpdate
from .models.capacity_plan import CapacityPlan, CapacityPlanCreate, CapacityPlanUpdate
from .models.demand_forecast import (
    DemandForecast,
    DemandForecastCreate,
    DemandForecastUpdate,
)
from .models.downtime_entry import (
    DowntimeEntry,
    DowntimeEntryCreate,
    DowntimeEntryUpdate,
)
from .models.engineering_change_order import (
    EngineeringChangeOrder,
    EngineeringChangeOrderCreate,
    EngineeringChangeOrderUpdate,
)
from .models.engineering_document import (
    EngineeringDocument,
    EngineeringDocumentCreate,
    EngineeringDocumentUpdate,
)
from .models.mrp_run import MRPRun, MrpRunCreate, MrpRunUpdate
from .models.oee_metric import OeeMetric, OeeMetricCreate, OeeMetricUpdate
from .models.process_loss import ProcessLoss, ProcessLossCreate, ProcessLossUpdate
from .models.production_variance_analysis import (
    ProductionVarianceAnalysis,
    ProductionVarianceAnalysisCreate,
    ProductionVarianceAnalysisUpdate,
)
from .models.routing import Routing, RoutingCreate, RoutingUpdate
from .models.subcontracting_order import (
    SubcontractingOrder,
    SubcontractingOrderCreate,
    SubcontractingOrderUpdate,
)
from .models.supply_plan import SupplyPlan, SupplyPlanCreate, SupplyPlanUpdate

# --- 마스터 데이터 ---

ROUTING = EntityMeta(
    collection="routings",
    prefix="RTNG",
    api_path="/api/v1/routings",
    tag="공정 경로",
    resource="routing",
    model=Routing,
    create_schema=RoutingCreate,
    update_schema=RoutingUpdate,
    archetype="master",
    not_found_message="공정 경로를 찾을 수 없습니다",
)

BOM_REVISION = EntityMeta(
    collection="bom_revisions",
    prefix="BOMR",
    api_path="/api/v1/bom-revisions",
    tag="BOM 개정",
    resource="bom_revision",
    model=BOMRevision,
    create_schema=BomRevisionCreate,
    update_schema=BomRevisionUpdate,
    archetype="master",
    not_found_message="BOM 개정을 찾을 수 없습니다",
)

BOM_TREE = EntityMeta(
    collection="bom_trees",
    prefix="BOMT",
    api_path="/api/v1/bom-trees",
    tag="BOM 트리",
    resource="bom_tree",
    model=BOMTree,
    create_schema=BomTreeCreate,
    update_schema=BomTreeUpdate,
    archetype="master",
    not_found_message="BOM 트리를 찾을 수 없습니다",
)

ENGINEERING_DOCUMENT = EntityMeta(
    collection="engineering_documents",
    prefix="EDOC",
    api_path="/api/v1/engineering-documents",
    tag="설계 문서",
    resource="engineering_document",
    model=EngineeringDocument,
    create_schema=EngineeringDocumentCreate,
    update_schema=EngineeringDocumentUpdate,
    archetype="master",
    not_found_message="설계 문서를 찾을 수 없습니다",
)

# --- 트랜잭션 ---

DEMAND_FORECAST = EntityMeta(
    collection="demand_forecasts",
    prefix="DFST",
    api_path="/api/v1/demand-forecasts",
    tag="수요 예측",
    resource="demand_forecast",
    model=DemandForecast,
    create_schema=DemandForecastCreate,
    update_schema=DemandForecastUpdate,
    archetype="transaction",
    not_found_message="수요 예측을 찾을 수 없습니다",
)

SUPPLY_PLAN = EntityMeta(
    collection="supply_plans",
    prefix="SPLAN",
    api_path="/api/v1/supply-plans",
    tag="공급 계획",
    resource="supply_plan",
    model=SupplyPlan,
    create_schema=SupplyPlanCreate,
    update_schema=SupplyPlanUpdate,
    archetype="transaction",
    not_found_message="공급 계획을 찾을 수 없습니다",
)

CAPACITY_PLAN = EntityMeta(
    collection="capacity_plans",
    prefix="CPLAN",
    api_path="/api/v1/capacity-plans",
    tag="생산능력 계획",
    resource="capacity_plan",
    model=CapacityPlan,
    create_schema=CapacityPlanCreate,
    update_schema=CapacityPlanUpdate,
    archetype="transaction",
    not_found_message="생산능력 계획을 찾을 수 없습니다",
)

MRP_RUN = EntityMeta(
    collection="mrp_runs",
    prefix="MRP",
    api_path="/api/v1/mrp-runs",
    tag="MRP 실행",
    resource="mrp_run",
    model=MRPRun,
    create_schema=MrpRunCreate,
    update_schema=MrpRunUpdate,
    archetype="transaction",
    not_found_message="MRP 실행을 찾을 수 없습니다",
)

SUBCONTRACTING_ORDER = EntityMeta(
    collection="subcontracting_orders",
    prefix="SUBC",
    api_path="/api/v1/subcontracting-orders",
    tag="외주 가공 주문",
    resource="subcontracting_order",
    model=SubcontractingOrder,
    create_schema=SubcontractingOrderCreate,
    update_schema=SubcontractingOrderUpdate,
    archetype="transaction",
    not_found_message="외주 가공 주문을 찾을 수 없습니다",
)

PROCESS_LOSS = EntityMeta(
    collection="process_losses",
    prefix="PLSS",
    api_path="/api/v1/process-losses",
    tag="공정 손실",
    resource="process_loss",
    model=ProcessLoss,
    create_schema=ProcessLossCreate,
    update_schema=ProcessLossUpdate,
    archetype="transaction",
    not_found_message="공정 손실을 찾을 수 없습니다",
)

BY_PRODUCT = EntityMeta(
    collection="by_products",
    prefix="BYPD",
    api_path="/api/v1/by-products",
    tag="부산물",
    resource="by_product",
    model=ByProduct,
    create_schema=ByProductCreate,
    update_schema=ByProductUpdate,
    archetype="transaction",
    not_found_message="부산물을 찾을 수 없습니다",
)

DOWNTIME_ENTRY = EntityMeta(
    collection="downtime_entries",
    prefix="DWNT",
    api_path="/api/v1/downtime-entries",
    tag="비가동 기록",
    resource="downtime_entry",
    model=DowntimeEntry,
    create_schema=DowntimeEntryCreate,
    update_schema=DowntimeEntryUpdate,
    archetype="transaction",
    not_found_message="비가동 기록을 찾을 수 없습니다",
)

OEE_METRIC = EntityMeta(
    collection="oee_metrics",
    prefix="OEE",
    api_path="/api/v1/oee-metrics",
    tag="OEE 지표",
    resource="oee_metric",
    model=OeeMetric,
    create_schema=OeeMetricCreate,
    update_schema=OeeMetricUpdate,
    archetype="transaction",
    not_found_message="OEE 지표를 찾을 수 없습니다",
)

ENGINEERING_CHANGE_ORDER = EntityMeta(
    collection="engineering_change_orders",
    prefix="ECO",
    api_path="/api/v1/engineering-change-orders",
    tag="설계 변경 지시",
    resource="engineering_change_order",
    model=EngineeringChangeOrder,
    create_schema=EngineeringChangeOrderCreate,
    update_schema=EngineeringChangeOrderUpdate,
    archetype="transaction",
    not_found_message="설계 변경 지시를 찾을 수 없습니다",
)

PRODUCTION_VARIANCE_ANALYSIS = EntityMeta(
    collection="production_variance_analyses",
    prefix="PVA",
    api_path="/api/v1/production-variance-analyses",
    tag="생산 차이 분석",
    resource="production_variance_analysis",
    model=ProductionVarianceAnalysis,
    create_schema=ProductionVarianceAnalysisCreate,
    update_schema=ProductionVarianceAnalysisUpdate,
    archetype="transaction",
    not_found_message="생산 차이 분석을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    ROUTING,
    BOM_REVISION,
    BOM_TREE,
    ENGINEERING_DOCUMENT,
    # 트랜잭션
    DEMAND_FORECAST,
    SUPPLY_PLAN,
    CAPACITY_PLAN,
    MRP_RUN,
    SUBCONTRACTING_ORDER,
    PROCESS_LOSS,
    BY_PRODUCT,
    DOWNTIME_ENTRY,
    OEE_METRIC,
    ENGINEERING_CHANGE_ORDER,
    PRODUCTION_VARIANCE_ANALYSIS,
]
