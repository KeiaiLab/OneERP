"""TMS 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

11개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 3개 엔티티(shipments, delivery_orders, freight_settlements)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.carrier import Carrier, CarrierCreate, CarrierUpdate
from .models.delivery_condition import (
    DeliveryCondition,
    DeliveryConditionCreate,
    DeliveryConditionUpdate,
)
from .models.freight_rate import FreightRate, FreightRateCreate, FreightRateUpdate
from .models.proof_of_delivery import ProofOfDelivery, ProofOfDeliveryCreate
from .models.return_shipment import (
    ReturnShipment,
    ReturnShipmentCreate,
    ReturnShipmentUpdate,
)
from .models.route import Route, RouteCreate, RouteUpdate
from .models.tracking_event import TrackingEvent, TrackingEventCreate
from .models.vehicle import Vehicle, VehicleCreate, VehicleUpdate

# --- 마스터 데이터 ---

CARRIER = EntityMeta(
    collection="carriers",
    prefix="CRR",
    api_path="/api/v1/carriers",
    tag="운송사",
    resource="carrier",
    model=Carrier,
    create_schema=CarrierCreate,
    update_schema=CarrierUpdate,
    archetype="master",
    not_found_message="운송사를 찾을 수 없습니다",
)

VEHICLE = EntityMeta(
    collection="vehicles",
    prefix="VHC",
    api_path="/api/v1/vehicles",
    tag="차량",
    resource="vehicle",
    model=Vehicle,
    create_schema=VehicleCreate,
    update_schema=VehicleUpdate,
    archetype="master",
    not_found_message="차량을 찾을 수 없습니다",
)

ROUTE = EntityMeta(
    collection="routes",
    prefix="RTE",
    api_path="/api/v1/routes",
    tag="배송경로",
    resource="route",
    model=Route,
    create_schema=RouteCreate,
    update_schema=RouteUpdate,
    archetype="master",
    not_found_message="배송 경로를 찾을 수 없습니다",
)

FREIGHT_RATE = EntityMeta(
    collection="freight_rates",
    prefix="FR",
    api_path="/api/v1/freight-rates",
    tag="운임단가",
    resource="freight_rate",
    model=FreightRate,
    create_schema=FreightRateCreate,
    update_schema=FreightRateUpdate,
    archetype="master",
    not_found_message="운임 단가를 찾을 수 없습니다",
)

DELIVERY_CONDITION = EntityMeta(
    collection="delivery_conditions",
    prefix="DC",
    api_path="/api/v1/delivery-conditions",
    tag="거래처배송조건",
    resource="delivery_condition",
    model=DeliveryCondition,
    create_schema=DeliveryConditionCreate,
    update_schema=DeliveryConditionUpdate,
    archetype="master",
    not_found_message="거래처 배송 조건을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 (EntityMeta 자동 CRUD) ---

RETURN_SHIPMENT = EntityMeta(
    collection="return_shipments",
    prefix="RSH",
    api_path="/api/v1/return-shipments",
    tag="반품운송",
    resource="return_shipment",
    model=ReturnShipment,
    create_schema=ReturnShipmentCreate,
    update_schema=ReturnShipmentUpdate,
    archetype="transaction",
    not_found_message="반품 운송을 찾을 수 없습니다",
)

PROOF_OF_DELIVERY = EntityMeta(
    collection="proof_of_deliveries",
    prefix="POD",
    api_path="/api/v1/proof-of-deliveries",
    tag="배송증빙",
    resource="proof_of_delivery",
    model=ProofOfDelivery,
    create_schema=ProofOfDeliveryCreate,
    update_schema=ProofOfDeliveryCreate,  # POD는 불변
    archetype="transaction",
    not_found_message="배송 증빙을 찾을 수 없습니다",
)

TRACKING_EVENT = EntityMeta(
    collection="tracking_events",
    prefix="TE",
    api_path="/api/v1/tracking-events",
    tag="추적이벤트",
    resource="tracking_event",
    model=TrackingEvent,
    create_schema=TrackingEventCreate,
    update_schema=TrackingEventCreate,  # 추적 이벤트는 불변
    archetype="transaction",
    not_found_message="추적 이벤트를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    CARRIER,
    VEHICLE,
    ROUTE,
    FREIGHT_RATE,
    DELIVERY_CONDITION,
    # 트랜잭션
    RETURN_SHIPMENT,
    PROOF_OF_DELIVERY,
    TRACKING_EVENT,
]
