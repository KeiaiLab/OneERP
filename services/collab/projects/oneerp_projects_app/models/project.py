"""프로젝트(Project) 모델 정의.

L2 비즈니스 룰: BR-PROJ-001 (프로젝트명 필수), BR-PROJ-002 (종료일>=시작일),
BR-PROJ-003 (초안만 삭제), BR-PROJ-004 (완료율 0~100).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, model_validator


class ProjectStatus(StrEnum):
    """프로젝트 상태."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(BaseDocument):
    """프로젝트 문서 — 프로젝트 관리.

    naming prefix: PROJ
    """

    project_name: str
    status: ProjectStatus = ProjectStatus.OPEN
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    percent_complete: Decimal = Decimal(0)
    company: str = ""
    cost_center: str = ""
    customer: str = ""
    project_manager: str = ""
    budget: Decimal = Decimal(0)
    template_id: str = ""
    generated_task_count: int = 0

    @model_validator(mode="after")
    def _validate_fields(self) -> Project:
        if (
            self.expected_start_date is not None
            and self.expected_end_date is not None
            and self.expected_end_date < self.expected_start_date
        ):
            raise ValueError("예상 종료일은 예상 시작일보다 빠를 수 없습니다")
        if self.percent_complete < 0 or self.percent_complete > 100:
            raise ValueError("프로젝트 완료율은 0에서 100 사이여야 합니다")
        return self


class ProjectCreate(BaseModel):
    """프로젝트 생성 요청 스키마."""

    project_name: str
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    company: str = ""
    cost_center: str = ""
    customer: str = ""
    project_manager: str = ""
    budget: Decimal = Decimal(0)
    template_id: str = ""

    @model_validator(mode="after")
    def _validate_fields(self) -> ProjectCreate:
        if (
            self.expected_start_date is not None
            and self.expected_end_date is not None
            and self.expected_end_date < self.expected_start_date
        ):
            raise ValueError("예상 종료일은 예상 시작일보다 빠를 수 없습니다")
        return self


class ProjectUpdate(BaseModel):
    """프로젝트 수정 요청 스키마 — 모든 필드 선택적."""

    project_name: str | None = None
    status: ProjectStatus | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    percent_complete: Decimal | None = None
    company: str | None = None
    cost_center: str | None = None
    customer: str | None = None
    project_manager: str | None = None
    budget: Decimal | None = None
    template_id: str | None = None

    @model_validator(mode="after")
    def _validate_fields(self) -> ProjectUpdate:
        if (
            self.expected_start_date is not None
            and self.expected_end_date is not None
            and self.expected_end_date < self.expected_start_date
        ):
            raise ValueError("예상 종료일은 예상 시작일보다 빠를 수 없습니다")
        if self.percent_complete is not None and (
            self.percent_complete < 0 or self.percent_complete > 100
        ):
            raise ValueError("프로젝트 완료율은 0에서 100 사이여야 합니다")
        return self
