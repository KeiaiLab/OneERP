"""기회(Opportunity) 문서 모델 — CRM 영업 기회."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class OpportunityType(StrEnum):
    """기회 유형."""

    SALES = "sales"
    MAINTENANCE = "maintenance"


class OpportunityStatus(StrEnum):
    """기회 상태."""

    OPEN = "open"
    QUOTATION = "quotation"
    WON = "won"
    LOST = "lost"


class OpportunityCreate(BaseModel):
    """기회 생성 요청 스키마."""

    lead_ref: str = ""
    customer_id: str = ""
    opportunity_type: OpportunityType = OpportunityType.SALES
    expected_amount: Decimal = Decimal(0)
    probability: Decimal = Decimal(0)
    close_date: date | None = None


class OpportunityUpdate(BaseModel):
    """기회 수정 요청 스키마."""

    lead_ref: str | None = None
    customer_id: str | None = None
    opportunity_type: OpportunityType | None = None
    expected_amount: Decimal | None = None
    probability: Decimal | None = None
    close_date: date | None = None
    status: OpportunityStatus | None = None


class Opportunity(BaseDocument):
    """기회 문서 — CRM 영업 기회.

    naming prefix: OPP
    """

    lead_ref: str = ""
    customer_id: str = ""
    opportunity_type: OpportunityType = OpportunityType.SALES
    expected_amount: Decimal = Decimal(0)
    probability: Decimal = Decimal(0)
    close_date: date | None = None
    status: OpportunityStatus = OpportunityStatus.OPEN
