"""리드 스코어링(LeadScoring) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class LeadScoringCreate(BaseModel):
    """리드 스코어링 생성 요청 스키마."""

    lead_id: str
    score: Decimal = Decimal(0)
    scoring_criteria: str = ""
    last_updated: date | None = None


class LeadScoringUpdate(BaseModel):
    """리드 스코어링 수정 요청 스키마."""

    lead_id: str | None = None
    score: Decimal | None = None
    scoring_criteria: str | None = None
    last_updated: date | None = None


class LeadScoring(BaseDocument):
    """리드 스코어링 문서."""

    lead_id: str = ""
    score: Decimal = Decimal(0)
    scoring_criteria: str = ""
    last_updated: date | None = None
