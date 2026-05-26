"""수요 예측(DemandForecast) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DemandForecastStatus(StrEnum):
    """수요 예측 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class DemandForecastCreate(BaseModel):
    """수요 예측 생성 요청 스키마."""

    item_code: str
    forecast_qty: Decimal = Decimal(0)
    period: str = ""
    forecast_type: str = ""
    confidence_level: Decimal = Decimal(0)


class DemandForecastUpdate(BaseModel):
    """수요 예측 수정 요청 스키마."""

    item_code: str | None = None
    forecast_qty: Decimal | None = None
    period: str | None = None
    forecast_type: str | None = None
    confidence_level: Decimal | None = None


class DemandForecast(BaseDocument):
    """수요 예측 문서."""

    status: DemandForecastStatus = Field(
        default=DemandForecastStatus.DRAFT,
        description="수요 예측 상태",
    )
    item_code: str = ""
    forecast_qty: Decimal = Decimal(0)
    period: str = ""
    forecast_type: str = ""
    confidence_level: Decimal = Decimal(0)
