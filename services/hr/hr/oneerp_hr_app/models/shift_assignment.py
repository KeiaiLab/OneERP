"""교대배정(ShiftAssignment) 문서 모델 — HR 모듈."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ShiftAssignmentCreate(BaseModel):
    """교대배정 생성 요청 스키마."""

    employee: str
    shift_type: str
    start_date: date | None = None
    end_date: date | None = None


class ShiftAssignmentUpdate(BaseModel):
    """교대배정 수정 요청 스키마."""

    employee: str | None = None
    shift_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ShiftAssignment(BaseDocument):
    """교대배정 문서 — HR 교대근무 배정 마스터.

    naming prefix: SHA
    """

    employee: str = ""
    shift_type: str = ""
    start_date: date | None = None
    end_date: date | None = None
