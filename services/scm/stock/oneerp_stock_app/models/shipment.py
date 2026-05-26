"""출하(Shipment) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ShipmentStatus(StrEnum):
    """출하 상태."""

    DRAFT = "draft"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"


class ShipmentCreate(BaseModel):
    """출하 생성 요청 스키마."""

    carrier_id: str = ""
    route_id: str = ""
    tracking_no: str = ""
    ship_date: date | None = None
    estimated_delivery: date | None = None
    total_weight: Decimal = Decimal(0)


class ShipmentUpdate(BaseModel):
    """출하 수정 요청 스키마."""

    carrier_id: str | None = None
    route_id: str | None = None
    tracking_no: str | None = None
    ship_date: date | None = None
    estimated_delivery: date | None = None
    total_weight: Decimal | None = None


class Shipment(BaseDocument):
    """출하 문서."""

    status: ShipmentStatus = Field(
        default=ShipmentStatus.DRAFT,
        description="출하 상태",
    )
    carrier_id: str = ""
    route_id: str = ""
    tracking_no: str = ""
    ship_date: date | None = None
    estimated_delivery: date | None = None
    total_weight: Decimal = Decimal(0)
