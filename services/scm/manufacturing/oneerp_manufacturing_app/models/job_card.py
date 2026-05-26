"""작업카드(JobCard) 모델 정의."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class JobCard(BaseDocument):
    """작업카드 문서 — 개별 공정 작업 추적.

    naming prefix: JC
    """

    work_order: str = ""
    operation: str = ""
    workstation: str = ""
    employee_id: str = Field(default="", alias="employee")
    status: str = "open"
    planned_time: Decimal = Decimal(0)
    actual_time: Decimal = Decimal(0)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobCardCreate(BaseModel):
    """작업카드 생성 요청."""

    work_order: str = ""
    operation: str = ""
    workstation: str = ""
    employee_id: str = ""
    status: str = "open"
    planned_time: Decimal = Decimal(0)
    actual_time: Decimal = Decimal(0)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobCardUpdate(BaseModel):
    """작업카드 수정 요청."""

    work_order: str | None = None
    operation: str | None = None
    workstation: str | None = None
    employee_id: str | None = None
    status: str | None = None
    planned_time: Decimal | None = None
    actual_time: Decimal | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
