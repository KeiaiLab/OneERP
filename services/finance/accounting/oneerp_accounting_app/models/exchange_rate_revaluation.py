"""환율 재평가(ExchangeRateRevaluation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ExchangeRateRevaluationStatus(StrEnum):
    """환율 재평가 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class ExchangeRateRevaluationCreate(BaseModel):
    """환율 재평가 생성 요청 스키마."""

    revaluation_date: date | None = None
    currency: str = ""
    old_rate: Decimal = Decimal(0)
    new_rate: Decimal = Decimal(0)
    gain_loss: Decimal = Decimal(0)


class ExchangeRateRevaluationUpdate(BaseModel):
    """환율 재평가 수정 요청 스키마."""

    revaluation_date: date | None = None
    currency: str | None = None
    old_rate: Decimal | None = None
    new_rate: Decimal | None = None
    gain_loss: Decimal | None = None


class ExchangeRateRevaluation(BaseDocument):
    """환율 재평가 문서."""

    status: ExchangeRateRevaluationStatus = Field(
        default=ExchangeRateRevaluationStatus.DRAFT,
        description="환율 재평가 상태",
    )
    revaluation_date: date | None = None
    currency: str = ""
    old_rate: Decimal = Decimal(0)
    new_rate: Decimal = Decimal(0)
    gain_loss: Decimal = Decimal(0)
