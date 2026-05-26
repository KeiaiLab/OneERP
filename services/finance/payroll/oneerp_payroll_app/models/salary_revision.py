"""급여 조정(SalaryRevision) 문서 모델.

L2 비즈니스 룰: BR-PAY-020 (급여조정 이력 관리).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class SalaryRevisionStatus(StrEnum):
    """급여 조정 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPLIED = "applied"


class SalaryRevisionCreate(BaseModel):
    """급여 조정 생성 요청 스키마."""

    employee_id: str
    effective_date: date | None = None
    current_salary: Decimal = Decimal(0)
    revised_salary: Decimal = Decimal(0)
    revision_percentage: Decimal = Decimal(0)
    reason: str = ""


class SalaryRevisionUpdate(BaseModel):
    """급여 조정 수정 요청 스키마."""

    employee_id: str | None = None
    effective_date: date | None = None
    current_salary: Decimal | None = None
    revised_salary: Decimal | None = None
    revision_percentage: Decimal | None = None
    reason: str | None = None
    status: SalaryRevisionStatus | None = None


class SalaryRevision(BaseDocument):
    """급여 조정 문서."""

    status: SalaryRevisionStatus = Field(
        default=SalaryRevisionStatus.DRAFT,
        description="급여 조정 상태",
    )
    employee_id: str = ""
    effective_date: date | None = None
    current_salary: Decimal = Decimal(0)
    revised_salary: Decimal = Decimal(0)
    revision_percentage: Decimal = Decimal(0)
    reason: str = ""
