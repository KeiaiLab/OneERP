"""자금 예측(CashFlowForecast) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CashFlowForecastStatus(StrEnum):
    """자금 예측 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class CashFlowForecastCreate(BaseModel):
    """자금 예측 생성 요청 스키마."""

    period: str
    expected_inflow: Decimal = Decimal(0)
    expected_outflow: Decimal = Decimal(0)
    net_flow: Decimal = Decimal(0)
    memo: str = ""


class CashFlowForecastUpdate(BaseModel):
    """자금 예측 수정 요청 스키마."""

    period: str | None = None
    expected_inflow: Decimal | None = None
    expected_outflow: Decimal | None = None
    net_flow: Decimal | None = None
    memo: str | None = None


class CashFlowForecast(BaseDocument):
    """자금 예측 문서."""

    status: CashFlowForecastStatus = Field(
        default=CashFlowForecastStatus.DRAFT,
        description="자금 예측 상태",
    )
    period: str = ""
    expected_inflow: Decimal = Decimal(0)
    expected_outflow: Decimal = Decimal(0)
    net_flow: Decimal = Decimal(0)
    memo: str = ""
