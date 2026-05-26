"""배송 건(Shipment) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class ShipAddress(BaseModel):
    """배송지 주소 정보."""

    name: str = ""
    address: str = ""
    zipcode: str = ""
    lat: float | None = None
    lng: float | None = None
    phone: str = ""
    contact_name: str = ""


class ShipmentItem(BaseModel):
    """배송 품목."""

    item_code: str = ""
    item_name: str = ""
    qty: float = 0
    weight_kg: float = 0
    volume_cbm: float = 0


class ShipmentCreate(BaseModel):
    """배송 건 생성 요청."""

    delivery_note_id: str | None = None
    sales_order_id: str | None = None
    ship_from: ShipAddress
    ship_to: ShipAddress
    items: list[ShipmentItem]
    expected_pickup: datetime | None = None
    expected_delivery: datetime | None = None
    special_instructions: str | None = None
    delivery_condition_id: str | None = None
    is_return: bool = False
    company: str = ""


class ShipmentUpdate(BaseModel):
    """배송 건 수정 요청."""

    ship_from: ShipAddress | None = None
    ship_to: ShipAddress | None = None
    items: list[ShipmentItem] | None = None
    expected_pickup: datetime | None = None
    expected_delivery: datetime | None = None
    special_instructions: str | None = None
    delivery_condition_id: str | None = None
    company: str | None = None


class Shipment(BaseDocument):
    """배송 건 — 개별 배송 실행 단위.

    naming prefix: SHP
    """

    shipment_no: str = Field(default="", description="배송번호")
    delivery_note_id: str | None = Field(default=None, description="출하 문서 참조")
    sales_order_id: str | None = Field(default=None, description="판매주��� 참조")
    carrier_id: str | None = Field(default=None, description="배정 운송사")
    vehicle_id: str | None = Field(default=None, description="배정 차량")
    delivery_order_id: str | None = Field(default=None, description="배차 지시 참조")
    route_id: str | None = Field(default=None, description="배송 경로")
    ship_from: ShipAddress = Field(default_factory=ShipAddress, description="출발지")
    ship_to: ShipAddress = Field(default_factory=ShipAddress, description="도착지")
    expected_pickup: datetime | None = Field(default=None, description="예상 픽업 일시")
    expected_delivery: datetime | None = Field(default=None, description="예상 배송 일시")
    actual_pickup: datetime | None = Field(default=None, description="실제 픽업 일시")
    actual_delivery: datetime | None = Field(default=None, description="실제 배송 일시")
    tracking_no: str | None = Field(default=None, description="운송장 번호")
    status: str = Field(default="draft", description="배송 상태")
    items: list[ShipmentItem] = Field(default_factory=list, description="배송 품목")
    total_weight_kg: float = Field(default=0.0, description="총 중량")
    total_volume_cbm: float = Field(default=0.0, description="총 용적")
    total_packages: int = Field(default=0, description="총 포장 수")
    special_instructions: str | None = Field(default=None, description="특수 배송 요청")
    delivery_condition_id: str | None = Field(default=None, description="거래처 배송 조건")
    freight_amount: float = Field(default=0.0, description="운임 금액")
    pod_id: str | None = Field(default=None, description="POD 참조")
    is_return: bool = Field(default=False, description="반품 배송 여부")
    return_shipment_id: str | None = Field(default=None, description="반품 참조")
    company: str = Field(default="", description="회사")
