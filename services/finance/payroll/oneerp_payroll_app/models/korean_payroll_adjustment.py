"""한국 급여 조정(KoreanPayrollAdjustment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class KoreanPayrollAdjustmentStatus(StrEnum):
    """한국 급여 정산 조정 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPLIED = "applied"


class KoreanPayrollAdjustmentCreate(BaseModel):
    """한국 급여 조정 생성 요청 스키마."""

    employee_id: str
    adjustment_type: str = ""
    adjustment_date: date | None = None
    amount: Decimal = Decimal(0)
    reason: str = ""


class KoreanPayrollAdjustmentUpdate(BaseModel):
    """한국 급여 조정 수정 요청 스키마."""

    employee_id: str | None = None
    adjustment_type: str | None = None
    adjustment_date: date | None = None
    amount: Decimal | None = None
    reason: str | None = None
    status: KoreanPayrollAdjustmentStatus | None = None


class KoreanPayrollAdjustment(BaseDocument):
    """한국 급여 조정 문서."""

    status: KoreanPayrollAdjustmentStatus = Field(
        default=KoreanPayrollAdjustmentStatus.DRAFT,
        description="한국 급여 정산 조정 상태",
    )
    employee_id: str = ""
    adjustment_type: str = ""
    adjustment_date: date | None = None
    amount: Decimal = Decimal(0)
    reason: str = ""
