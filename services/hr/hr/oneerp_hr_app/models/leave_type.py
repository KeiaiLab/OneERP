"""휴가유형(LeaveType) 문서 모델 — HR 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LeaveTypeCreate(BaseModel):
    """휴가유형 생성 요청 스키마."""

    leave_type_name: str
    max_leaves_allowed: int = 0
    is_carry_forward: bool = False
    is_paid: bool = True


class LeaveTypeUpdate(BaseModel):
    """휴가유형 수정 요청 스키마."""

    leave_type_name: str | None = None
    max_leaves_allowed: int | None = None
    is_carry_forward: bool | None = None
    is_paid: bool | None = None


class LeaveType(BaseDocument):
    """휴가유형 문서 — HR 휴가유형 마스터.

    naming prefix: LVTP
    """

    leave_type_name: str = ""
    max_leaves_allowed: int = 0
    is_carry_forward: bool = False
    is_paid: bool = True
