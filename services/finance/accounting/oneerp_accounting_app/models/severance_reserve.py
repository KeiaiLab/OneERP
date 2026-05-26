"""퇴직급여충당부채(SeveranceReserve) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SeveranceReserveStatus(StrEnum):
    """퇴직급여충당부채 상태."""

    DRAFT = "draft"
    CALCULATED = "calculated"
    SUBMITTED = "submitted"


class SeveranceReserveCreate(BaseModel):
    """퇴직급여충당부채 생성 요청 스키마."""

    employee_id: str
    reserve_amount: Decimal = Decimal(0)
    calculation_date: date | None = None
    years_of_service: Decimal = Decimal(0)


class SeveranceReserveUpdate(BaseModel):
    """퇴직급여충당부채 수정 요청 스키마."""

    employee_id: str | None = None
    reserve_amount: Decimal | None = None
    calculation_date: date | None = None
    years_of_service: Decimal | None = None


class SeveranceReserve(BaseDocument):
    """퇴직급여충당부채 문서."""

    status: SeveranceReserveStatus = Field(
        default=SeveranceReserveStatus.DRAFT,
        description="퇴직급여충당부채 상태",
    )
    employee_id: str = ""
    reserve_amount: Decimal = Decimal(0)
    calculation_date: date | None = None
    years_of_service: Decimal = Decimal(0)
