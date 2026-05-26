"""마일스톤(Milestone) 문서 모델 — Projects 모듈."""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    """마일스톤 생성 요청 스키마."""

    milestone_name: str
    project: str = ""
    due_date: date | None = None
    status: str = "pending"
    description: str = ""
    completion_criteria: str = ""
    billing_amount: Decimal = Field(default=Decimal(0), ge=0)


class MilestoneUpdate(BaseModel):
    """마일스톤 수정 요청 스키마."""

    milestone_name: str | None = None
    project: str | None = None
    due_date: date | None = None
    status: str | None = None
    description: str | None = None
    completion_criteria: str | None = None
    billing_amount: Decimal | None = Field(default=None, ge=0)


class Milestone(BaseDocument):
    """마일스톤 문서 — Projects 마일스톤 마스터.

    naming prefix: MLS
    """

    milestone_name: str = ""
    project: str = ""
    due_date: date | None = None
    status: str = "pending"
    description: str = ""
    completion_criteria: str = ""
    billing_amount: Decimal = Field(default=Decimal(0), ge=0)
    billing_id: str = ""
    completed_at: datetime | None = None
