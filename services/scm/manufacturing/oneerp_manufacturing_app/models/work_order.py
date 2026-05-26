"""작업지시(WorkOrder) 모델 정의.

L2 비즈니스 룰: BR-MFG-006 (BOM필수), BR-MFG-008 (완료조건), BR-MFG-009/010 (수정/취소조건).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WorkOrderStatus(StrEnum):
    """작업지시 상태."""

    DRAFT = "draft"
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrder(BaseDocument):
    """작업지시 문서 — 생산 작업 관리.

    naming prefix: WO
    """

    production_item: str
    bom_ref: str
    qty: Decimal
    planned_start_date: date
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    warehouse: str = ""


class WorkOrderCreate(BaseModel):
    """작업지시 생성 요청 스키마."""

    production_item: str
    bom_ref: str
    qty: Decimal
    planned_start_date: date
    planned_end_date: date | None = None
    warehouse: str = ""


class WorkOrderUpdate(BaseModel):
    """작업지시 수정 요청 스키마 — 모든 필드 선택적."""

    production_item: str | None = None
    bom_ref: str | None = None
    qty: Decimal | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: WorkOrderStatus | None = None
    warehouse: str | None = None
