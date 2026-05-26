"""운임 단가(FreightRate) 모���."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class FreightRateCreate(BaseModel):
    """운임 단가 생성 요청."""

    carrier_id: str
    route_id: str | None = None
    rate_type: str  # base/weight/volume/distance/flat
    vehicle_type: str | None = None
    weight_min_kg: float = 0
    weight_max_kg: float = 999999
    base_amount: float
    per_kg_amount: float = 0
    per_km_amount: float = 0
    fuel_surcharge_rate: float = 0
    currency: str = "KRW"
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True
    company: str = ""


class FreightRateUpdate(BaseModel):
    """운임 단가 수정 요청."""

    carrier_id: str | None = None
    route_id: str | None = None
    rate_type: str | None = None
    vehicle_type: str | None = None
    weight_min_kg: float | None = None
    weight_max_kg: float | None = None
    base_amount: float | None = None
    per_kg_amount: float | None = None
    per_km_amount: float | None = None
    fuel_surcharge_rate: float | None = None
    currency: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool | None = None
    company: str | None = None


class FreightRate(BaseDocument):
    """운임 단가 마스터 — 운송사별/경로별/중량구간별 운임 단가.

    naming prefix: FR
    """

    carrier_id: str = Field(default="", description="운송사")
    route_id: str | None = Field(default=None, description="경로")
    rate_type: str = Field(default="", description="단가 유형")
    vehicle_type: str | None = Field(default=None, description="차량 유형")
    weight_min_kg: float = Field(default=0, description="중량 하한 (kg)")
    weight_max_kg: float = Field(default=999999, description="중량 상한 (kg)")
    base_amount: float = Field(default=0, description="기본 금액 (원)")
    per_kg_amount: float = Field(default=0, description="kg당 추가 금액")
    per_km_amount: float = Field(default=0, description="km당 추가 금액")
    fuel_surcharge_rate: float = Field(default=0, description="유류할증률")
    currency: str = Field(default="KRW", description="통화")
    effective_from: date | None = Field(default=None, description="적용 시작일")
    effective_to: date | None = Field(default=None, description="적용 종료일")
    is_active: bool = Field(default=True, description="활성 여부")
    company: str = Field(default="", description="회사")
