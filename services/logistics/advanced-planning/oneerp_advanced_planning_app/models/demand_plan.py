"""수요계획 모델 — 수요 예측과 계획을 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class DemandPlanCreate(BaseModel):
    """수요계획 생성 요청 스키마."""

    plan_name: str
    plan_type: str = "forecast"  # forecast/consensus/statistical
    period_start: date | None = None
    period_end: date | None = None
    item_code: str = ""
    item_group: str = ""
    warehouse: str = ""
    forecast_qty: Decimal = Decimal(0)
    uom: str = ""
    forecast_method: str = "moving_average"  # moving_average/exponential/regression
    description: str = ""


class DemandPlanUpdate(BaseModel):
    """수요계획 수정 요청 스키마."""

    plan_name: str | None = None
    forecast_qty: Decimal | None = None
    actual_qty: Decimal | None = None
    status: str | None = None
    description: str | None = None


class DemandPlan(BaseDocument):
    """수요계획 문서 — 수요 예측 및 계획 정보를 저장한다."""

    plan_name: str = ""
    plan_type: str = "forecast"
    period_start: date | None = None
    period_end: date | None = None
    item_code: str = ""
    item_group: str = ""
    warehouse: str = ""
    forecast_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    uom: str = ""
    forecast_method: str = "moving_average"
    status: str = "draft"  # draft/active/approved/closed
    accuracy_percent: Decimal = Decimal(0)
    description: str = ""
