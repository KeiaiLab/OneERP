"""TMS 서비스 이벤트 핸들러 — DELIVERY_NOTE_SUBMITTED 수신 시 배송 건 자동 생성.

Stock(Selling) 서비스가 DELIVERY_NOTE_SUBMITTED 이벤트를 발행하면,
TMS 서비스가 배송 건(Shipment)을 자동 생성한다 (SC-TMS-001).
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.events.handler_registry import EventHandlerRegistry
from oneerp_core.events.schemas import EventType
from oneerp_core.events.utils import extract_tenant_and_doc
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_logistics_app.tms.models.shipment import ShipAddress, Shipment, ShipmentItem

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()


@event_registry.on(
    EventType.DELIVERY_NOTE_SUBMITTED,
    description="출하(DeliveryNote) 제출 → 배송 건 자동 생성",
)
async def handle_delivery_note_submitted(payload: dict[str, Any], event_id: str) -> None:
    """출하(DeliveryNote) 제출 이벤트를 수신하여 배송 건을 생성한다.

    SC-TMS-001: WMS 출하 → 배송 건 자동 생성
    """
    tenant_id, doc_id = extract_tenant_and_doc(payload)
    event_data = payload.get("event", {}).get("data", {})

    # 이벤트 데이터에서 배송 정보 추출
    ship_from_data = event_data.get("ship_from", {})
    ship_to_data = event_data.get("ship_to", {})
    raw_items = event_data.get("items", [])

    # 품목 변환
    shipment_items: list[ShipmentItem] = []
    total_weight = 0.0
    for item in raw_items:
        weight = float(item.get("weight_kg", 0))
        total_weight += weight
        shipment_items.append(
            ShipmentItem(
                item_code=item.get("item_code", ""),
                item_name=item.get("item_name", ""),
                qty=float(item.get("qty", 0)),
                weight_kg=weight,
                volume_cbm=float(item.get("volume_cbm", 0)),
            )
        )

    shp_id = generate_name("SHP", tenant_id=tenant_id)
    shipment = Shipment(
        _id=shp_id,
        tenant_id=tenant_id,
        shipment_no=shp_id,
        delivery_note_id=doc_id,
        sales_order_id=event_data.get("sales_order_id"),
        ship_from=ShipAddress(**ship_from_data) if ship_from_data else ShipAddress(),
        ship_to=ShipAddress(**ship_to_data) if ship_to_data else ShipAddress(),
        items=shipment_items,
        total_weight_kg=total_weight,
        status="draft",
    )

    shp_repo = Repository("shipments", tenant_id=tenant_id)
    shp_repo.insert(shipment)

    logger.info(
        "배송 건 자동 생성 완료: delivery_note=%s, shipment=%s, event_id=%s",
        doc_id,
        shp_id,
        event_id,
    )
