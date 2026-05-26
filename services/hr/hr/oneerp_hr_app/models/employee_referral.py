"""직원 추천 채용(EmployeeReferral) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeReferralStatus(StrEnum):
    """직원 추천 채용 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    HIRED = "hired"
    REJECTED = "rejected"


class EmployeeReferralCreate(BaseModel):
    """직원 추천 채용 생성 요청 스키마."""

    referrer_id: str
    applicant_name: str = ""
    job_opening_id: str = ""
    referral_date: date | None = None
    bonus_amount: Decimal = Decimal(0)


class EmployeeReferralUpdate(BaseModel):
    """직원 추천 채용 수정 요청 스키마."""

    referrer_id: str | None = None
    applicant_name: str | None = None
    job_opening_id: str | None = None
    referral_date: date | None = None
    bonus_amount: Decimal | None = None
    status: EmployeeReferralStatus | None = None


class EmployeeReferral(BaseDocument):
    """직원 추천 채용 문서."""

    status: EmployeeReferralStatus = Field(
        default=EmployeeReferralStatus.DRAFT,
        description="직원 추천 채용 상태",
    )
    referrer_id: str = ""
    applicant_name: str = ""
    job_opening_id: str = ""
    referral_date: date | None = None
    bonus_amount: Decimal = Decimal(0)
