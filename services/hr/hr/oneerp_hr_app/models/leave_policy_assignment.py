"""휴가 정책 할당(LeavePolicyAssignment) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LeavePolicyAssignmentStatus(StrEnum):
    """휴가 정책 배정 상태."""

    DRAFT = "draft"
    ASSIGNED = "assigned"


class LeavePolicyAssignmentCreate(BaseModel):
    """휴가 정책 할당 생성 요청 스키마."""

    employee_id: str
    leave_policy_id: str = ""
    effective_date: date | None = None


class LeavePolicyAssignmentUpdate(BaseModel):
    """휴가 정책 할당 수정 요청 스키마."""

    employee_id: str | None = None
    leave_policy_id: str | None = None
    effective_date: date | None = None
    status: LeavePolicyAssignmentStatus | None = None


class LeavePolicyAssignment(BaseDocument):
    """휴가 정책 할당 문서."""

    status: LeavePolicyAssignmentStatus = Field(
        default=LeavePolicyAssignmentStatus.DRAFT,
        description="휴가 정책 배정 상태",
    )
    employee_id: str = ""
    leave_policy_id: str = ""
    effective_date: date | None = None
