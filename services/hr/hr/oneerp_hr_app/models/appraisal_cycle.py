"""인사 평가 주기(AppraisalCycle) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AppraisalCycleStatus(StrEnum):
    """평가 주기 상태."""

    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class AppraisalCycleCreate(BaseModel):
    """인사 평가 주기 생성 요청 스키마."""

    cycle_name: str
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True


class AppraisalCycleUpdate(BaseModel):
    """인사 평가 주기 수정 요청 스키마."""

    cycle_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    status: AppraisalCycleStatus | None = None


class AppraisalCycle(BaseDocument):
    """인사 평가 주기 문서."""

    status: AppraisalCycleStatus = Field(
        default=AppraisalCycleStatus.DRAFT,
        description="평가 주기 상태",
    )
    cycle_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
