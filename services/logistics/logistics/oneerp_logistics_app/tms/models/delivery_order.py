"""배차 지시(DeliveryOrder) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class PlannedStop(BaseModel):
    """계획 방문 순서."""

    shipment_id: str = ""
    stop_order: int = 0
    estimated_arrival: str | None = None


class DeliveryOrderCreate(BaseModel):
    """배차 지시 생성 요청."""

    dispatch_date: date
    carrier_id: str
    vehicle_id: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    shipment_ids: list[str]
    route_id: str | None = None
    planned_sequence: list[PlannedStop] | None = None
    dispatch_method: str = "manual"  # manual/auto_rule/auto_optimize
    notes: str | None = None
    company: str = ""


class DeliveryOrderUpdate(BaseModel):
    """배차 지시 수정 요청."""

    dispatch_date: date | None = None
    carrier_id: str | None = None
    vehicle_id: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    shipment_ids: list[str] | None = None
    route_id: str | None = None
    planned_sequence: list[PlannedStop] | None = None
    notes: str | None = None
    company: str | None = None


class DeliveryOrder(BaseDocument):
    """배차 지시 — 복수 배송 건의 차량/운전자 배정 단위.

    naming prefix: DO
    """

    order_no: str = Field(default="", description="배차번호")
    dispatch_date: date | None = Field(default=None, description="배차일")
    carrier_id: str = Field(default="", description="배정 운송사")
    vehicle_id: str | None = Field(default=None, description="배정 차량")
    driver_name: str | None = Field(default=None, description="운전자명")
    driver_phone: str | None = Field(default=None, description="운���자 연락처")
    shipment_ids: list[str] = Field(default_factory=list, description="포함 배송 건 ID")
    route_id: str | None = Field(default=None, description="배정 경로")
    total_weight_kg: float = Field(default=0.0, description="총 중량")
    total_volume_cbm: float = Field(default=0.0, description="총 용적")
    total_shipments: int = Field(default=0, description="배송 건 수")
    planned_sequence: list[PlannedStop] = Field(default_factory=list, description="계획 방문 순서")
    status: str = Field(default="draft", description="배차 상태")
    dispatch_method: str = Field(default="manual", description="배차 방식")
    notes: str | None = Field(default=None, description="비고")
    company: str = Field(default="", description="회사")
