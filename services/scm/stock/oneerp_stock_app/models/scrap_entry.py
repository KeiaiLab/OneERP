"""폐기 처리(ScrapEntry) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ScrapEntryStatus(StrEnum):
    """폐기 처리 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class ScrapEntryCreate(BaseModel):
    """폐기 처리 생성 요청 스키마."""

    item_code: str
    warehouse_id: str
    qty: Decimal = Decimal(0)
    reason: str = ""
    scrap_date: date | None = None


class ScrapEntryUpdate(BaseModel):
    """폐기 처리 수정 요청 스키마."""

    item_code: str | None = None
    warehouse_id: str | None = None
    qty: Decimal | None = None
    reason: str | None = None
    scrap_date: date | None = None


class ScrapEntry(BaseDocument):
    """폐기 처리 문서."""

    status: ScrapEntryStatus = Field(
        default=ScrapEntryStatus.DRAFT,
        description="폐기 처리 상태",
    )
    item_code: str = ""
    warehouse_id: str = ""
    qty: Decimal = Decimal(0)
    reason: str = ""
    scrap_date: date | None = None
