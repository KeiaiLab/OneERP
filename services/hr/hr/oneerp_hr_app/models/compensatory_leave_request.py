"""대체 휴가 신청(CompensatoryLeaveRequest) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CompensatoryLeaveRequestStatus(StrEnum):
    """보상휴가 신청 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class CompensatoryLeaveRequestCreate(BaseModel):
    """대체 휴가 신청 생성 요청 스키마."""

    employee_id: str
    work_date: date | None = None
    leave_date: date | None = None
    reason: str = ""


class CompensatoryLeaveRequestUpdate(BaseModel):
    """대체 휴가 신청 수정 요청 스키마."""

    employee_id: str | None = None
    work_date: date | None = None
    leave_date: date | None = None
    reason: str | None = None
    status: CompensatoryLeaveRequestStatus | None = None


class CompensatoryLeaveRequest(BaseDocument):
    """대체 휴가 신청 문서."""

    status: CompensatoryLeaveRequestStatus = Field(
        default=CompensatoryLeaveRequestStatus.DRAFT,
        description="보상휴가 신청 상태",
    )
    employee_id: str = ""
    work_date: date | None = None
    leave_date: date | None = None
    reason: str = ""
