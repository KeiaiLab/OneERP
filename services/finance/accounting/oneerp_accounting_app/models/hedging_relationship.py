"""헤지 관계(HedgingRelationship) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class HedgingRelationshipStatus(StrEnum):
    """헤지 관계 상태."""

    ACTIVE = "active"
    DISCONTINUED = "discontinued"


class HedgingRelationshipCreate(BaseModel):
    """헤지 관계 생성 요청 스키마."""

    hedging_instrument_id: str
    hedged_item: str = ""
    hedge_type: str = ""
    effectiveness_ratio: Decimal = Decimal(0)
    designation_date: date | None = None


class HedgingRelationshipUpdate(BaseModel):
    """헤지 관계 수정 요청 스키마."""

    hedging_instrument_id: str | None = None
    hedged_item: str | None = None
    hedge_type: str | None = None
    effectiveness_ratio: Decimal | None = None
    designation_date: date | None = None


class HedgingRelationship(BaseDocument):
    """헤지 관계 문서."""

    status: HedgingRelationshipStatus = Field(
        default=HedgingRelationshipStatus.ACTIVE,
        description="헤지 관계 상태",
    )
    hedging_instrument_id: str = ""
    hedged_item: str = ""
    hedge_type: str = ""
    effectiveness_ratio: Decimal = Decimal(0)
    designation_date: date | None = None
