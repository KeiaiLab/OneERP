"""안전 교육(SafetyTraining) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class TrainingType(StrEnum):
    """교육 유형."""

    REGULAR = "regular"
    SPECIAL = "special"
    NEW_HIRE = "new_hire"
    SUPERVISOR = "supervisor"


class TrainingStatus(StrEnum):
    """교육 상태."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SafetyTrainingCreate(BaseModel):
    """안전 교육 생성 요청 스키마."""

    training_name: str
    training_type: TrainingType
    legal_basis: str
    target_employees: list[str]
    scheduled_date: date
    duration_hours: Decimal
    instructor: str | None = None
    completion_records: list[dict[str, Any]] | None = None
    status: TrainingStatus = TrainingStatus.PLANNED


class SafetyTrainingUpdate(BaseModel):
    """안전 교육 수정 요청 스키마."""

    training_name: str | None = None
    training_type: TrainingType | None = None
    legal_basis: str | None = None
    target_employees: list[str] | None = None
    scheduled_date: date | None = None
    duration_hours: Decimal | None = None
    instructor: str | None = None
    completion_records: list[dict[str, Any]] | None = None
    status: TrainingStatus | None = None


class SafetyTraining(BaseDocument):
    """안전 교육 문서."""

    training_name: str = ""
    training_type: TrainingType = TrainingType.REGULAR
    legal_basis: str = ""
    target_employees: list[str] | None = None
    scheduled_date: date | None = None
    duration_hours: Decimal = Decimal(0)
    instructor: str | None = None
    completion_records: list[dict[str, Any]] | None = None
    status: TrainingStatus = TrainingStatus.PLANNED
