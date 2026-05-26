"""통화 기록(CallLog) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CallLogCreate(BaseModel):
    """통화 기록 생성 요청 스키마."""

    caller: str
    receiver: str = ""
    call_date: date | None = None
    duration_minutes: Decimal = Decimal(0)
    call_type: str = ""
    summary: str = ""


class CallLogUpdate(BaseModel):
    """통화 기록 수정 요청 스키마."""

    caller: str | None = None
    receiver: str | None = None
    call_date: date | None = None
    duration_minutes: Decimal | None = None
    call_type: str | None = None
    summary: str | None = None


class CallLog(BaseDocument):
    """통화 기록 문서."""

    caller: str = ""
    receiver: str = ""
    call_date: date | None = None
    duration_minutes: Decimal = Decimal(0)
    call_type: str = ""
    summary: str = ""
