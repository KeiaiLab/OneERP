"""생산계획(ProductionPlan) 모델 정의."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal  # noqa: TC003 — pydantic model_json_schema 런타임 필요

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class ProductionPlanItem(LineItem):
    """생산계획 라인 아이템."""

    item_code: str
    item_name: str
    planned_qty: Decimal
    bom_no: str = ""


class ProductionPlan(BaseDocument):
    """생산계획 문서 — 생산 일정 관리.

    naming prefix: PP
    """

    planned_start: date | None = None
    planned_end: date | None = None
    status: str = "draft"
    items: list[ProductionPlanItem] = []


class ProductionPlanCreate(BaseModel):
    """생산계획 생성 요청."""

    planned_start: date | None = None
    planned_end: date | None = None
    status: str = "draft"
    items: list[ProductionPlanItem] = []


class ProductionPlanUpdate(BaseModel):
    """생산계획 수정 요청."""

    planned_start: date | None = None
    planned_end: date | None = None
    status: str | None = None
    items: list[ProductionPlanItem] | None = None
