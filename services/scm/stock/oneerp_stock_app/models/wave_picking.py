"""웨이브 피킹(WavePicking) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WavePickingStatus(StrEnum):
    """웨이브 피킹 상태."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WavePickingCreate(BaseModel):
    """웨이브 피킹 생성 요청 스키마."""

    warehouse_id: str
    sales_order_ids: list[str] = Field(default_factory=list)
    picker: str = ""
    pick_date: date | None = None


class WavePickingUpdate(BaseModel):
    """웨이브 피킹 수정 요청 스키마."""

    warehouse_id: str | None = None
    sales_order_ids: list[str] | None = None
    picker: str | None = None
    pick_date: date | None = None


class WavePicking(BaseDocument):
    """웨이브 피킹 문서."""

    status: WavePickingStatus = Field(
        default=WavePickingStatus.DRAFT,
        description="웨이브 피킹 상태",
    )
    warehouse_id: str = ""
    sales_order_ids: list[str] = Field(default_factory=list)
    picker: str = ""
    pick_date: date | None = None
