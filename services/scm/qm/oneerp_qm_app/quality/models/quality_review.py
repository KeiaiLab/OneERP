"""품질 검토(QualityReview) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class QualityReviewCreate(BaseModel):
    """품질 검토 생성 요청 스키마."""

    review_name: str
    review_date: date | None = None
    reviewer: str = ""
    findings: str = ""
    score: Decimal = Decimal(0)


class QualityReviewUpdate(BaseModel):
    """품질 검토 수정 요청 스키마."""

    review_name: str | None = None
    review_date: date | None = None
    reviewer: str | None = None
    findings: str | None = None
    score: Decimal | None = None


class QualityReview(BaseDocument):
    """품질 검토 문서."""

    review_name: str = ""
    review_date: date | None = None
    reviewer: str = ""
    findings: str = ""
    score: Decimal = Decimal(0)
