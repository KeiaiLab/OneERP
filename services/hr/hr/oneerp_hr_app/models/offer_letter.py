"""채용 제안서(OfferLetter) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class OfferLetterStatus(StrEnum):
    """입사 제안서 상태."""

    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class OfferLetterCreate(BaseModel):
    """채용 제안서 생성 요청 스키마."""

    applicant_id: str
    designation: str = ""
    department_id: str = ""
    annual_salary: Decimal = Decimal(0)
    offer_date: date | None = None
    valid_until: date | None = None


class OfferLetterUpdate(BaseModel):
    """채용 제안서 수정 요청 스키마."""

    applicant_id: str | None = None
    designation: str | None = None
    department_id: str | None = None
    annual_salary: Decimal | None = None
    offer_date: date | None = None
    valid_until: date | None = None
    status: OfferLetterStatus | None = None


class OfferLetter(BaseDocument):
    """채용 제안서 문서."""

    status: OfferLetterStatus = Field(
        default=OfferLetterStatus.DRAFT,
        description="입사 제안서 상태",
    )
    applicant_id: str = ""
    designation: str = ""
    department_id: str = ""
    annual_salary: Decimal = Decimal(0)
    offer_date: date | None = None
    valid_until: date | None = None
