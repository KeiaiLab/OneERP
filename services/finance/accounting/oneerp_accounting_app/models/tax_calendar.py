"""세무 일정 관리(TaxCalendar) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-KTAX-006: 원천세 신고 기한 (매월 10일)
- BR-KTAX-014: 세무 일정 자동 생성 (부가세 4회 + 원천세 12회 + 법인세 1회)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class TaxCalendarCreate(BaseModel):
    """세무 일정 생성 요청 스키마."""

    tax_type: str
    due_date: date | None = None
    period: str = ""
    description: str = ""
    is_completed: bool = False


class TaxCalendarUpdate(BaseModel):
    """세무 일정 수정 요청 스키마."""

    tax_type: str | None = None
    due_date: date | None = None
    period: str | None = None
    description: str | None = None
    is_completed: bool | None = None


class TaxCalendar(BaseDocument):
    """세무 일정 문서."""

    tax_type: str = ""
    due_date: date | None = None
    period: str = ""
    description: str = ""
    is_completed: bool = False
