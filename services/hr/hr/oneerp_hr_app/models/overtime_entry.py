"""초과근무 기록(OvertimeEntry) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class OvertimeEntryStatus(StrEnum):
    """초과근무 기록 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class OvertimeEntryCreate(BaseModel):
    """초과근무 기록 생성 요청 스키마."""

    employee_id: str
    overtime_date: date | None = None
    hours: Decimal = Decimal(0)
    overtime_type: str = ""
    is_approved: bool = False


class OvertimeEntryUpdate(BaseModel):
    """초과근무 기록 수정 요청 스키마."""

    employee_id: str | None = None
    overtime_date: date | None = None
    hours: Decimal | None = None
    overtime_type: str | None = None
    is_approved: bool | None = None
    status: OvertimeEntryStatus | None = None


class OvertimeEntry(BaseDocument):
    """초과근무 기록 문서."""

    status: OvertimeEntryStatus = Field(
        default=OvertimeEntryStatus.DRAFT,
        description="초과근무 기록 상태",
    )
    employee_id: str = ""
    overtime_date: date | None = None
    hours: Decimal = Decimal(0)
    overtime_type: str = ""
    is_approved: bool = False
