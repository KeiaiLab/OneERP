"""사업자등록(BusinessRegistration) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class BusinessRegistrationCreate(BaseModel):
    """사업자등록 생성 요청 스키마."""

    registration_number: str
    company_name: str
    representative: str = ""
    business_type: str = ""
    registration_date: date | None = None


class BusinessRegistrationUpdate(BaseModel):
    """사업자등록 수정 요청 스키마."""

    registration_number: str | None = None
    company_name: str | None = None
    representative: str | None = None
    business_type: str | None = None
    registration_date: date | None = None


class BusinessRegistration(BaseDocument):
    """사업자등록 문서 — Setup 사업자등록 마스터.

    naming prefix: BRN
    """

    registration_number: str = ""
    company_name: str = ""
    representative: str = ""
    business_type: str = ""
    registration_date: date | None = None


_BUSINESS_REGISTRATION_TYPES = {"date": __import__("datetime").date}

BusinessRegistrationCreate.model_rebuild(_types_namespace=_BUSINESS_REGISTRATION_TYPES)
BusinessRegistrationUpdate.model_rebuild(_types_namespace=_BUSINESS_REGISTRATION_TYPES)
BusinessRegistration.model_rebuild(_types_namespace=_BUSINESS_REGISTRATION_TYPES)
