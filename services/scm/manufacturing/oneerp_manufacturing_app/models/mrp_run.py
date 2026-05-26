"""MRP 실행(MrpRun) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class MRPRunStatus(StrEnum):
    """MRP 실행 상태."""

    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    APPLIED = "applied"


class MrpRunCreate(BaseModel):
    """MRP 실행 생성 요청 스키마."""

    forecast_id: str = ""
    run_date: date | None = None
    generated_purchase_requests: int = 0
    generated_work_orders: int = 0


class MrpRunUpdate(BaseModel):
    """MRP 실행 수정 요청 스키마."""

    forecast_id: str | None = None
    run_date: date | None = None
    generated_purchase_requests: int | None = None
    generated_work_orders: int | None = None


class MRPRun(BaseDocument):
    """MRP 실행 문서."""

    status: MRPRunStatus = Field(
        default=MRPRunStatus.DRAFT,
        description="MRP 실행 상태",
    )
    forecast_id: str = ""
    run_date: date | None = None
    generated_purchase_requests: int = 0
    generated_work_orders: int = 0
