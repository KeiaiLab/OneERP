"""순환 재고 조사(CycleCount) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-STK-018: 순환재고조사 규칙 (ABC 분류별 조사 주기)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CycleCountStatus(StrEnum):
    """순환 재고 조사 상태."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CycleCountCreate(BaseModel):
    """순환 재고 조사 생성 요청 스키마."""

    warehouse_id: str
    count_date: date | None = None
    item_code: str = ""
    system_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)


class CycleCountUpdate(BaseModel):
    """순환 재고 조사 수정 요청 스키마."""

    warehouse_id: str | None = None
    count_date: date | None = None
    item_code: str | None = None
    system_qty: Decimal | None = None
    actual_qty: Decimal | None = None
    variance: Decimal | None = None


class CycleCount(BaseDocument):
    """순환 재고 조사 문서."""

    status: CycleCountStatus = Field(
        default=CycleCountStatus.DRAFT,
        description="순환 재고 조사 상태",
    )
    warehouse_id: str = ""
    count_date: date | None = None
    item_code: str = ""
    system_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)
