"""Stock 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

18개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티는 routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.atp_check import AtpCheck, AtpCheckCreate, AtpCheckUpdate
from .models.bin_location import BinLocation, BinLocationCreate, BinLocationUpdate
from .models.carrier import Carrier, CarrierCreate, CarrierUpdate
from .models.cycle_count import CycleCount, CycleCountCreate, CycleCountUpdate
from .models.freight_cost import FreightCost, FreightCostCreate, FreightCostUpdate
from .models.hazardous_material import (
    HazardousMaterial,
    HazardousMaterialCreate,
    HazardousMaterialUpdate,
)
from .models.inventory_count_sheet import (
    InventoryCountSheet,
    InventoryCountSheetCreate,
    InventoryCountSheetUpdate,
)
from .models.item_attribute import (
    ItemAttribute,
    ItemAttributeCreate,
    ItemAttributeUpdate,
)
from .models.landed_cost_voucher_tms import (
    LandedCostVoucherTMS,
    LandedCostVoucherTmsCreate,
    LandedCostVoucherTmsUpdate,
)
from .models.putaway_rule import PutawayRule, PutawayRuleCreate, PutawayRuleUpdate
from .models.reorder import ReorderLevel, ReorderLevelCreate, ReorderLevelUpdate
from .models.route import Route, RouteCreate, RouteUpdate
from .models.safety_stock_rule import (
    SafetyStockRule,
    SafetyStockRuleCreate,
    SafetyStockRuleUpdate,
)
from .models.scrap_entry import ScrapEntry, ScrapEntryCreate, ScrapEntryUpdate
from .models.serial_batch_bundle import (
    SerialBatchBundle,
    SerialBatchBundleCreate,
    SerialBatchBundleUpdate,
)
from .models.shipment import Shipment, ShipmentCreate, ShipmentUpdate

# StockLedgerEntry는 커스텀 라우터(routes/stock_ledger_entries.py)에서 직접 관리
from .models.tracking_update import (
    TrackingUpdate,
    TrackingUpdateCreate,
    TrackingUpdateUpdate,
)
from .models.uom_conversion import (
    UomConversion,
    UomConversionCreate,
    UomConversionUpdate,
)
from .models.wave_picking import WavePicking, WavePickingCreate, WavePickingUpdate

# --- 마스터 데이터 ---

BIN_LOCATION = EntityMeta(
    collection="bin_locations",
    prefix="BLOC",
    api_path="/api/v1/bin-locations",
    tag="적치 위치",
    resource="bin_location",
    model=BinLocation,
    create_schema=BinLocationCreate,
    update_schema=BinLocationUpdate,
    archetype="master",
    not_found_message="적치 위치를 찾을 수 없습니다",
)

PUTAWAY_RULE = EntityMeta(
    collection="putaway_rules",
    prefix="PTWY",
    api_path="/api/v1/putaway-rules",
    tag="적치 규칙",
    resource="putaway_rule",
    model=PutawayRule,
    create_schema=PutawayRuleCreate,
    update_schema=PutawayRuleUpdate,
    archetype="master",
    not_found_message="적치 규칙을 찾을 수 없습니다",
)

CARRIER = EntityMeta(
    collection="carriers",
    prefix="CAR",
    api_path="/api/v1/carriers",
    tag="운송사",
    resource="carrier",
    model=Carrier,
    create_schema=CarrierCreate,
    update_schema=CarrierUpdate,
    archetype="master",
    not_found_message="운송사를 찾을 수 없습니다",
)

ROUTE = EntityMeta(
    collection="routes",
    prefix="RTE",
    api_path="/api/v1/routes",
    tag="운송 경로",
    resource="route",
    model=Route,
    create_schema=RouteCreate,
    update_schema=RouteUpdate,
    archetype="master",
    not_found_message="운송 경로를 찾을 수 없습니다",
)

SAFETY_STOCK_RULE = EntityMeta(
    collection="safety_stock_rules",
    prefix="SSR",
    api_path="/api/v1/safety-stock-rules",
    tag="안전재고 규칙",
    resource="safety_stock_rule",
    model=SafetyStockRule,
    create_schema=SafetyStockRuleCreate,
    update_schema=SafetyStockRuleUpdate,
    archetype="master",
    not_found_message="안전재고 규칙을 찾을 수 없습니다",
)

UOM_CONVERSION = EntityMeta(
    collection="uom_conversions",
    prefix="UOMC",
    api_path="/api/v1/uom-conversions",
    tag="단위 변환",
    resource="uom_conversion",
    model=UomConversion,
    create_schema=UomConversionCreate,
    update_schema=UomConversionUpdate,
    archetype="master",
    not_found_message="단위 변환을 찾을 수 없습니다",
)

ITEM_ATTRIBUTE = EntityMeta(
    collection="item_attributes",
    prefix="IATTR",
    api_path="/api/v1/item-attributes",
    tag="품목 속성",
    resource="item_attribute",
    model=ItemAttribute,
    create_schema=ItemAttributeCreate,
    update_schema=ItemAttributeUpdate,
    archetype="master",
    not_found_message="품목 속성을 찾을 수 없습니다",
)

HAZARDOUS_MATERIAL = EntityMeta(
    collection="hazardous_materials",
    prefix="HAZM",
    api_path="/api/v1/hazardous-materials",
    tag="위험물",
    resource="hazardous_material",
    model=HazardousMaterial,
    create_schema=HazardousMaterialCreate,
    update_schema=HazardousMaterialUpdate,
    archetype="master",
    not_found_message="위험물을 찾을 수 없습니다",
)

FREIGHT_COST = EntityMeta(
    collection="freight_costs",
    prefix="FRGT",
    api_path="/api/v1/freight-costs",
    tag="화물 운송비",
    resource="freight_cost",
    model=FreightCost,
    create_schema=FreightCostCreate,
    update_schema=FreightCostUpdate,
    archetype="master",
    not_found_message="화물 운송비를 찾을 수 없습니다",
)

# --- 트랜잭션 ---

WAVE_PICKING = EntityMeta(
    collection="wave_pickings",
    prefix="WAVE",
    api_path="/api/v1/wave-pickings",
    tag="웨이브 피킹",
    resource="wave_picking",
    model=WavePicking,
    create_schema=WavePickingCreate,
    update_schema=WavePickingUpdate,
    archetype="transaction",
    not_found_message="웨이브 피킹을 찾을 수 없습니다",
)

SHIPMENT = EntityMeta(
    collection="shipments",
    prefix="SHIP",
    api_path="/api/v1/shipments",
    tag="출하",
    resource="shipment",
    model=Shipment,
    create_schema=ShipmentCreate,
    update_schema=ShipmentUpdate,
    archetype="transaction",
    not_found_message="출하를 찾을 수 없습니다",
)

TRACKING_UPDATE = EntityMeta(
    collection="tracking_updates",
    prefix="TRKU",
    api_path="/api/v1/tracking-updates",
    tag="배송 추적 업데이트",
    resource="tracking_update",
    model=TrackingUpdate,
    create_schema=TrackingUpdateCreate,
    update_schema=TrackingUpdateUpdate,
    archetype="transaction",
    not_found_message="배송 추적 업데이트를 찾을 수 없습니다",
)

SERIAL_BATCH_BUNDLE = EntityMeta(
    collection="serial_batch_bundles",
    prefix="SBB",
    api_path="/api/v1/serial-batch-bundles",
    tag="시리얼/배치 번들",
    resource="serial_batch_bundle",
    model=SerialBatchBundle,
    create_schema=SerialBatchBundleCreate,
    update_schema=SerialBatchBundleUpdate,
    archetype="transaction",
    not_found_message="시리얼/배치 번들을 찾을 수 없습니다",
)

CYCLE_COUNT = EntityMeta(
    collection="cycle_counts",
    prefix="CCNT",
    api_path="/api/v1/cycle-counts",
    tag="순환 재고 조사",
    resource="cycle_count",
    model=CycleCount,
    create_schema=CycleCountCreate,
    update_schema=CycleCountUpdate,
    archetype="transaction",
    not_found_message="순환 재고 조사를 찾을 수 없습니다",
)

INVENTORY_COUNT_SHEET = EntityMeta(
    collection="inventory_count_sheets",
    prefix="ICS",
    api_path="/api/v1/inventory-count-sheets",
    tag="재고 실사 시트",
    resource="inventory_count_sheet",
    model=InventoryCountSheet,
    create_schema=InventoryCountSheetCreate,
    update_schema=InventoryCountSheetUpdate,
    archetype="transaction",
    not_found_message="재고 실사 시트를 찾을 수 없습니다",
)

SCRAP_ENTRY = EntityMeta(
    collection="scrap_entries",
    prefix="SCRP",
    api_path="/api/v1/scrap-entries",
    tag="폐기 처리",
    resource="scrap_entry",
    model=ScrapEntry,
    create_schema=ScrapEntryCreate,
    update_schema=ScrapEntryUpdate,
    archetype="transaction",
    not_found_message="폐기 처리를 찾을 수 없습니다",
)

LANDED_COST_VOUCHER_TMS = EntityMeta(
    collection="landed_cost_voucher_tms",
    prefix="LCVT",
    api_path="/api/v1/landed-cost-voucher-tms",
    tag="운송비 배부",
    resource="landed_cost_voucher_tms",
    model=LandedCostVoucherTMS,
    create_schema=LandedCostVoucherTmsCreate,
    update_schema=LandedCostVoucherTmsUpdate,
    archetype="transaction",
    not_found_message="운송비 배부를 찾을 수 없습니다",
)

ATP_CHECK = EntityMeta(
    collection="atp_checks",
    prefix="ATP",
    api_path="/api/v1/atp-checks",
    tag="ATP 조회",
    resource="atp_check",
    model=AtpCheck,
    create_schema=AtpCheckCreate,
    update_schema=AtpCheckUpdate,
    archetype="transaction",
    not_found_message="ATP 조회를 찾을 수 없습니다",
)

REORDER_LEVEL = EntityMeta(
    collection="reorder_levels",
    prefix="ROL",
    api_path="/api/v1/reorder-levels",
    tag="리오더 규칙",
    resource="reorder_level",
    model=ReorderLevel,
    create_schema=ReorderLevelCreate,
    update_schema=ReorderLevelUpdate,
    archetype="master",
    not_found_message="리오더 규칙을 찾을 수 없습니다",
)

# --- 시스템 원장 ---
# STOCK_LEDGER_ENTRY는 voucher_no 필터가 필요하여 커스텀 라우터(routes/stock_ledger_entries.py)로 관리

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    BIN_LOCATION,
    PUTAWAY_RULE,
    CARRIER,
    ROUTE,
    SAFETY_STOCK_RULE,
    UOM_CONVERSION,
    ITEM_ATTRIBUTE,
    HAZARDOUS_MATERIAL,
    FREIGHT_COST,
    REORDER_LEVEL,
    # 트랜잭션
    WAVE_PICKING,
    SHIPMENT,
    TRACKING_UPDATE,
    SERIAL_BATCH_BUNDLE,
    CYCLE_COUNT,
    INVENTORY_COUNT_SHEET,
    SCRAP_ENTRY,
    LANDED_COST_VOUCHER_TMS,
    ATP_CHECK,
]
