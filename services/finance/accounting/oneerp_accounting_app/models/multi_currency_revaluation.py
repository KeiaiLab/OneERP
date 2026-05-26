"""다통화 일괄 재평가(MultiCurrencyRevaluation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class MultiCurrencyRevaluationStatus(StrEnum):
    """다통화 일괄 재평가 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class MultiCurrencyRevaluationCreate(BaseModel):
    """다통화 일괄 재평가 생성 요청 스키마."""

    revaluation_date: date | None = None
    base_currency: str = "KRW"
    accounts_revalued: int = 0
    total_gain_loss: Decimal = Decimal(0)


class MultiCurrencyRevaluationUpdate(BaseModel):
    """다통화 일괄 재평가 수정 요청 스키마."""

    revaluation_date: date | None = None
    base_currency: str | None = None
    accounts_revalued: int | None = None
    total_gain_loss: Decimal | None = None


class MultiCurrencyRevaluation(BaseDocument):
    """다통화 일괄 재평가 문서."""

    status: MultiCurrencyRevaluationStatus = Field(
        default=MultiCurrencyRevaluationStatus.DRAFT,
        description="다통화 일괄 재평가 상태",
    )
    revaluation_date: date | None = None
    base_currency: str = "KRW"
    accounts_revalued: int = 0
    total_gain_loss: Decimal = Decimal(0)
