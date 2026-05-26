"""휴가 기간(LeavePeriod) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LeavePeriodCreate(BaseModel):
    """휴가 기간 생성 요청 스키마."""

    period_name: str
    from_date: date | None = None
    to_date: date | None = None
    is_active: bool = True


class LeavePeriodUpdate(BaseModel):
    """휴가 기간 수정 요청 스키마."""

    period_name: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    is_active: bool | None = None


class LeavePeriod(BaseDocument):
    """휴가 기간 문서."""

    period_name: str = ""
    from_date: date | None = None
    to_date: date | None = None
    is_active: bool = True
