"""반품 운송(ReturnShipment) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .shipment import ShipAddress

if TYPE_CHECKING:
    from datetime import datetime


class ReturnItem(BaseModel):
    """반품 품목."""

    item_code: str = ""
    item_name: str = ""
    qty: float = 0
    reason: str = ""


class ReturnShipmentCreate(BaseModel):
    """반품 운송 생성 요청."""

    original_shipment_id: str | None = None
    return_reason: str  # defective/wrong_item/customer_change/damaged/other
    return_reason_detail: str | None = None
    pickup_from: ShipAddress
    return_to: ShipAddress
    items: list[ReturnItem]
    expected_pickup: datetime | None = None
    company: str = ""


class ReturnShipmentUpdate(BaseModel):
    """반품 운송 수정 요청."""

    return_reason_detail: str | None = None
    carrier_id: str | None = None
    vehicle_id: str | None = None
    tracking_no: str | None = None
    expected_pickup: datetime | None = None
    company: str | None = None


class ReturnShipment(BaseDocument):
    """반품 운송 — 반품/회수 운송 건 관리.

    naming prefix: RSH
    """

    return_no: str = Field(default="", description="반품번호")
    original_shipment_id: str | None = Field(default=None, description="원 배송 건")
    return_reason: str = Field(default="", description="반품 사유")
    return_reason_detail: str | None = Field(default=None, description="상세 사유")
    pickup_from: ShipAddress = Field(default_factory=ShipAddress, description="회수지")
    return_to: ShipAddress = Field(default_factory=ShipAddress, description="반품 입고지")
    carrier_id: str | None = Field(default=None, description="회수 운송사")
    vehicle_id: str | None = Field(default=None, description="회수 차량")
    tracking_no: str | None = Field(default=None, description="회수 운송장 번호")
    items: list[ReturnItem] = Field(default_factory=list, description="반품 품목")
    status: str = Field(default="requested", description="반품 상태")
    expected_pickup: datetime | None = Field(default=None, description="예상 회수일시")
    actual_pickup: datetime | None = Field(default=None, description="실제 회수일시")
    actual_received: datetime | None = Field(default=None, description="실제 입고일시")
    freight_amount: float = Field(default=0, description="회수 운임")
    company: str = Field(default="", description="회사")
