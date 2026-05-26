"""법인 간 청구(IntercompanyBilling) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class IntercompanyBillingStatus(StrEnum):
    """법인 간 청구 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class IntercompanyBillingCreate(BaseModel):
    """법인 간 청구 생성 요청 스키마."""

    from_company: str
    to_company: str
    billing_date: date | None = None
    total_amount: Decimal = Decimal(0)
    description: str = ""


class IntercompanyBillingUpdate(BaseModel):
    """법인 간 청구 수정 요청 스키마."""

    from_company: str | None = None
    to_company: str | None = None
    billing_date: date | None = None
    total_amount: Decimal | None = None
    description: str | None = None


class IntercompanyBilling(BaseDocument):
    """법인 간 청구 문서."""

    status: IntercompanyBillingStatus = Field(
        default=IntercompanyBillingStatus.DRAFT,
        description="법인 간 청구 상태",
    )
    from_company: str = ""
    to_company: str = ""
    billing_date: date | None = None
    total_amount: Decimal = Decimal(0)
    description: str = ""
