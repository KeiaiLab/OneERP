"""공급업체평가(SupplierScorecard) 마스터 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SupplierScorecardCreate(BaseModel):
    """공급업체평가 생성 요청 스키마."""

    supplier: str
    evaluation_period: str = ""
    total_score: Decimal = Decimal(0)
    criteria: dict = {}


class SupplierScorecardUpdate(BaseModel):
    """공급업체평가 수정 요청 스키마."""

    supplier: str | None = None
    evaluation_period: str | None = None
    total_score: Decimal | None = None
    criteria: dict | None = None


class SupplierScorecard(BaseDocument):
    """공급업체평가 마스터 — 공급업체 성과를 평가.

    naming prefix: SSC
    """

    supplier: str = ""
    evaluation_period: str = ""
    total_score: Decimal = Decimal(0)
    criteria: dict = {}
