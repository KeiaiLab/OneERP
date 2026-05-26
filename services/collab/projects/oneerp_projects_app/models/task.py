"""작업(Task) 모델 정의."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator


class TaskPriority(StrEnum):
    """작업 우선순위."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(StrEnum):
    """작업 상태."""

    OPEN = "open"
    WORKING = "working"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseDocument):
    """작업 문서 — 프로젝트 하위 작업.

    naming prefix: TASK
    """

    subject: str
    project_ref: str | None = None
    assigned_to: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN
    start_date: date | None = None
    end_date: date | None = None
    predecessor_task_ids: list[str] = Field(default_factory=list)
    expected_time: Decimal = Decimal(0)
    actual_time: Decimal = Decimal(0)

    @model_validator(mode="after")
    def _validate_date_range(self) -> Task:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다")
        return self


class TaskCreate(BaseModel):
    """작업 생성 요청 스키마."""

    subject: str
    project_ref: str | None = None
    assigned_to: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: date | None = None
    end_date: date | None = None
    predecessor_task_ids: list[str] = Field(default_factory=list)
    expected_time: Decimal = Decimal(0)

    @model_validator(mode="after")
    def _validate_date_range(self) -> TaskCreate:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("종료일은 시작일보다 빠를 수 없습니다")
        return self


class TaskUpdate(BaseModel):
    """작업 수정 요청 스키마 — 모든 필드 선택적."""

    subject: str | None = None
    project_ref: str | None = None
    assigned_to: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    predecessor_task_ids: list[str] | None = None
    expected_time: Decimal | None = None
    actual_time: Decimal | None = None
