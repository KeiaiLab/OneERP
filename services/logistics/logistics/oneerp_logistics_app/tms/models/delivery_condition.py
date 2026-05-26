"""거래처 배송 조건(DeliveryCondition) 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    """배송 시간대."""

    start_time: str = "09:00"
    end_time: str = "18:00"


class DeliveryConditionCreate(BaseModel):
    """거래처 배송 조건 생성 요청."""

    customer_id: str
    delivery_time_window: TimeWindow | None = None
    preferred_carrier_id: str | None = None
    required_vehicle_type: str | None = None
    temperature_requirement: str = "normal"
    requires_pod: bool = True
    requires_appointment: bool = False
    unloading_available: bool = True
    special_instructions: str | None = None
    is_active: bool = True
    company: str = ""


class DeliveryConditionUpdate(BaseModel):
    """거래처 배송 조건 수정 요청."""

    delivery_time_window: TimeWindow | None = None
    preferred_carrier_id: str | None = None
    required_vehicle_type: str | None = None
    temperature_requirement: str | None = None
    requires_pod: bool | None = None
    requires_appointment: bool | None = None
    unloading_available: bool | None = None
    special_instructions: str | None = None
    is_active: bool | None = None
    company: str | None = None


class DeliveryCondition(BaseDocument):
    """거래처 배송 조건 — 거래처별 배송 요건 사전 등록.

    naming prefix: DC
    """

    customer_id: str = Field(default="", description="거래처")
    delivery_time_window: TimeWindow | None = Field(default=None, description="배송 가능 시간대")
    preferred_carrier_id: str | None = Field(default=None, description="선호 운송사")
    required_vehicle_type: str | None = Field(default=None, description="필수 차량 유형")
    temperature_requirement: str = Field(default="normal", description="온도 요건")
    requires_pod: bool = Field(default=True, description="POD 필수 여부")
    requires_appointment: bool = Field(default=False, description="사전 예약 필수 여부")
    unloading_available: bool = Field(default=True, description="하역 가능 여부")
    special_instructions: str | None = Field(default=None, description="특수 요청사항")
    is_active: bool = Field(default=True, description="활성 여부")
    company: str = Field(default="", description="회사")
