"""화물 운송비(FreightCost) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-STK-020: 화물운송비 계��� (중량/거리/단가 기반)
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class FreightCostStatus(StrEnum):
    """화물 운송비 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class FreightCostCreate(BaseModel):
    """화물 운송비 생성 요청 스키마."""

    carrier_id: str = ""
    route_id: str = ""
    base_cost: Decimal = Decimal(0)
    weight_charge: Decimal = Decimal(0)
    currency: str = "KRW"


class FreightCostUpdate(BaseModel):
    """화물 운송비 수정 요청 스키마."""

    carrier_id: str | None = None
    route_id: str | None = None
    base_cost: Decimal | None = None
    weight_charge: Decimal | None = None
    currency: str | None = None


class FreightCost(BaseDocument):
    """화물 운송비 문서."""

    status: FreightCostStatus = Field(
        default=FreightCostStatus.DRAFT,
        description="화물 운송비 상태",
    )
    carrier_id: str = ""
    route_id: str = ""
    base_cost: Decimal = Decimal(0)
    weight_charge: Decimal = Decimal(0)
    currency: str = "KRW"
