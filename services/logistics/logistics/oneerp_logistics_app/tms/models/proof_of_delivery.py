"""배송 증빙(ProofOfDelivery) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class GpsLocation(BaseModel):
    """GPS 위치 정보."""

    lat: float = 0
    lng: float = 0
    accuracy: float | None = None


class ProofOfDeliveryCreate(BaseModel):
    """배송 증빙 생성 요청."""

    shipment_id: str
    delivery_time: datetime
    receiver_name: str
    receiver_relation: str | None = None
    signature_image_url: str | None = None
    photo_urls: list[str] | None = None
    gps_location: GpsLocation | None = None
    delivery_status: str = "delivered"  # delivered/partial/refused
    notes: str | None = None
    company: str = ""


class ProofOfDelivery(BaseDocument):
    """배송 증빙 — 배송 완료 시 수령인 서명/사진 등 증빙 기록.

    naming prefix: POD
    불변 문서.
    """

    shipment_id: str = Field(default="", description="배송 건")
    delivery_time: datetime | None = Field(default=None, description="수령 일시")
    receiver_name: str = Field(default="", description="수령인명")
    receiver_relation: str | None = Field(default=None, description="수령인 관계")
    signature_image_url: str | None = Field(default=None, description="전자 서명 이미지 URL")
    photo_urls: list[str] = Field(default_factory=list, description="배송 증빙 사진 URL")
    gps_location: GpsLocation | None = Field(default=None, description="수령 장소 GPS")
    delivery_status: str = Field(default="delivered", description="수령 결과")
    notes: str | None = Field(default=None, description="비고")
    company: str = Field(default="", description="회사")
