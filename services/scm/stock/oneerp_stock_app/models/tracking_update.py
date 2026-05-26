"""배송 추적 업데이트(TrackingUpdate) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class TrackingUpdateCreate(BaseModel):
    """배송 추적 업데이트 생성 요청 스키마."""

    shipment_id: str
    update_time: str = ""
    location: str = ""
    event_description: str = ""


class TrackingUpdateUpdate(BaseModel):
    """배송 추적 업데이트 수정 요청 스키마."""

    shipment_id: str | None = None
    update_time: str | None = None
    location: str | None = None
    event_description: str | None = None


class TrackingUpdate(BaseDocument):
    """배송 추적 업데이트 문서."""

    shipment_id: str = ""
    update_time: str = ""
    location: str = ""
    event_description: str = ""
