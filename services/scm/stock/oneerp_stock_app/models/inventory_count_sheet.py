"""재고 실사 시트(InventoryCountSheet) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class InventoryCountSheetStatus(StrEnum):
    """재고 실사 시트 상태."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InventoryCountSheetCreate(BaseModel):
    """재고 실사 시트 생성 요청 스키마."""

    warehouse_id: str
    count_date: date | None = None
    total_items: int = 0
    counted_items: int = 0
    is_completed: bool = False


class InventoryCountSheetUpdate(BaseModel):
    """재고 실사 시트 수정 요청 스키마."""

    warehouse_id: str | None = None
    count_date: date | None = None
    total_items: int | None = None
    counted_items: int | None = None
    is_completed: bool | None = None


class InventoryCountSheet(BaseDocument):
    """재고 실사 시트 문서."""

    status: InventoryCountSheetStatus = Field(
        default=InventoryCountSheetStatus.DRAFT,
        description="재고 실사 시트 상태",
    )
    warehouse_id: str = ""
    count_date: date | None = None
    total_items: int = 0
    counted_items: int = 0
    is_completed: bool = False
