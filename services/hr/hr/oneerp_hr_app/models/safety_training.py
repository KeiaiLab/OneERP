"""안전 교육(SafetyTraining) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SafetyTrainingStatus(StrEnum):
    """안전 교육 상태."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SafetyTrainingCreate(BaseModel):
    """안전 교육 생성 요청 스키마."""

    training_name: str
    training_date: date | None = None
    trainer: str = ""
    participants: list[str] = Field(default_factory=list)
    is_mandatory: bool = True


class SafetyTrainingUpdate(BaseModel):
    """안전 교육 수정 요청 스키마."""

    training_name: str | None = None
    training_date: date | None = None
    trainer: str | None = None
    participants: list[str] | None = None
    is_mandatory: bool | None = None
    status: SafetyTrainingStatus | None = None


class SafetyTraining(BaseDocument):
    """안전 교육 문서."""

    status: SafetyTrainingStatus = Field(
        default=SafetyTrainingStatus.PLANNED,
        description="안전 교육 상태",
    )
    training_name: str = ""
    training_date: date | None = None
    trainer: str = ""
    participants: list[str] = Field(default_factory=list)
    is_mandatory: bool = True
