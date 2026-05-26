"""비가동 기록(DowntimeEntry) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DowntimeEntryCreate(BaseModel):
    """비가동 기록 생성 요청 스키마."""

    workstation_id: str
    start_time: str = ""
    end_time: str = ""
    duration_minutes: Decimal = Decimal(0)
    reason: str = ""


class DowntimeEntryUpdate(BaseModel):
    """비가동 기록 수정 요청 스키마."""

    workstation_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_minutes: Decimal | None = None
    reason: str | None = None


class DowntimeEntry(BaseDocument):
    """비가동 기록 문서."""

    workstation_id: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_minutes: Decimal = Decimal(0)
    reason: str = ""
