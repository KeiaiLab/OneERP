"""경쟁사 프로필(CompetitorProfile) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CompetitorProfileCreate(BaseModel):
    """경쟁사 프로필 생성 요청 스키마."""

    company_name: str
    industry: str = ""
    website: str = ""
    strengths: str = ""
    weaknesses: str = ""
    market_share: Decimal = Decimal(0)


class CompetitorProfileUpdate(BaseModel):
    """경쟁사 프로필 수정 요청 스키마."""

    company_name: str | None = None
    industry: str | None = None
    website: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    market_share: Decimal | None = None


class CompetitorProfile(BaseDocument):
    """경쟁사 프로필 문서."""

    company_name: str = ""
    industry: str = ""
    website: str = ""
    strengths: str = ""
    weaknesses: str = ""
    market_share: Decimal = Decimal(0)
