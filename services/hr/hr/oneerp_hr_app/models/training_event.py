"""교육 이벤트(TrainingEvent) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TrainingEventStatus(StrEnum):
    """교육 이벤트 상태."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TrainingEventCreate(BaseModel):
    """교육 이벤트 생성 요청 스키마."""

    event_name: str
    trainer: str = ""
    start_date: date | None = None
    end_date: date | None = None
    max_participants: int = 0
    location: str = ""


class TrainingEventUpdate(BaseModel):
    """교육 이벤트 수정 요청 스키마."""

    event_name: str | None = None
    trainer: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    max_participants: int | None = None
    location: str | None = None
    status: TrainingEventStatus | None = None


class TrainingEvent(BaseDocument):
    """교육 이벤트 문서."""

    status: TrainingEventStatus = Field(
        default=TrainingEventStatus.DRAFT,
        description="교육 이벤트 상태",
    )
    event_name: str = ""
    trainer: str = ""
    start_date: date | None = None
    end_date: date | None = None
    max_participants: int = 0
    location: str = ""
