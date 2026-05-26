"""휴가신청(LeaveApplication) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LeaveStatus(StrEnum):
    """휴가 신청 상태."""

    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeaveApplicationCreate(BaseModel):
    """휴가 신청 생성 요청 스키마."""

    employee_id: str
    employee_name: str = ""
    leave_type: str = ""
    from_date: date
    to_date: date
    total_days: Decimal = Decimal(0)
    reason: str = ""


class LeaveApplication(BaseDocument):
    """휴가 신청 문서 — HR 휴가 관리.

    naming prefix: LA
    """

    employee_id: str = Field(default="", description="직원 ID")
    employee_name: str = Field(default="", description="직원명")
    leave_type: str = Field(default="", description="휴가 유형")
    from_date: date | None = Field(default=None, description="시작일")
    to_date: date | None = Field(default=None, description="종료일")
    total_days: Decimal = Field(default=Decimal(0), description="총 휴가 일수")
    status: LeaveStatus = Field(default=LeaveStatus.OPEN, description="승인 상태")
    reason: str = Field(default="", description="사유")
