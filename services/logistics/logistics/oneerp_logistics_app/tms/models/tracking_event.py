"""배송 추적 이벤트(TrackingEvent) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class EventLocation(BaseModel):
    """이벤트 장소."""

    name: str = ""
    address: str = ""
    lat: float | None = None
    lng: float | None = None


class TrackingEventCreate(BaseModel):
    """추적 이벤트 생성 요청."""

    shipment_id: str
    event_time: datetime
    event_type: (
        str  # pickup/departure/checkpoint/arrival/delivery_attempt/delivered/failed/returned
    )
    status_code: str
    description: str
    location: EventLocation | None = None
    source: str = "manual"  # manual/carrier_api/gps/webhook
    raw_data: dict[str, Any] | None = None
    company: str = ""


class TrackingEvent(BaseDocument):
    """배송 추적 이벤트 — 배송 건 상태 변경 시계열 기록.

    naming prefix: TE
    불변 문서.
    """

    shipment_id: str = Field(default="", description="배송 건")
    event_time: datetime | None = Field(default=None, description="이벤트 발생 시간")
    event_type: str = Field(default="", description="이벤트 유형")
    status_code: str = Field(default="", description="상태 코드")
    description: str = Field(default="", description="상태 설명")
    location: EventLocation | None = Field(default=None, description="이벤트 장소")
    source: str = Field(default="manual", description="데이터 소스")
    raw_data: dict[str, Any] | None = Field(default=None, description="API 원본 데이터")
    company: str = Field(default="", description="회사")
