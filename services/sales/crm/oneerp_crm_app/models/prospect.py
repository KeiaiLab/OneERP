"""잠재 고객(Prospect) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ProspectCreate(BaseModel):
    """잠재 고객 생성 요청 스키마."""

    prospect_name: str
    company: str = ""
    industry: str = ""
    source: str = ""
    estimated_value: Decimal = Decimal(0)
    notes: str = ""


class ProspectUpdate(BaseModel):
    """잠재 고객 수정 요청 스키마."""

    prospect_name: str | None = None
    company: str | None = None
    industry: str | None = None
    source: str | None = None
    estimated_value: Decimal | None = None
    notes: str | None = None


class Prospect(BaseDocument):
    """잠재 고객 문서."""

    prospect_name: str = ""
    company: str = ""
    industry: str = ""
    source: str = ""
    estimated_value: Decimal = Decimal(0)
    notes: str = ""
