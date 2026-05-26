"""교대 변경 요청(ShiftRequest) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ShiftRequestStatus(StrEnum):
    """교대 요청 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class ShiftRequestCreate(BaseModel):
    """교대 변경 요청 생성 요청 스키마."""

    employee_id: str
    from_shift: str = ""
    to_shift: str = ""
    request_date: date | None = None
    reason: str = ""


class ShiftRequestUpdate(BaseModel):
    """교대 변경 요청 수정 요청 스키마."""

    employee_id: str | None = None
    from_shift: str | None = None
    to_shift: str | None = None
    request_date: date | None = None
    reason: str | None = None
    status: ShiftRequestStatus | None = None


class ShiftRequest(BaseDocument):
    """교대 변경 요청 문서."""

    status: ShiftRequestStatus = Field(
        default=ShiftRequestStatus.DRAFT,
        description="교대 요청 상태",
    )
    employee_id: str = ""
    from_shift: str = ""
    to_shift: str = ""
    request_date: date | None = None
    reason: str = ""
