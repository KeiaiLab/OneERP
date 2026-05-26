"""ESG 지표(ESGMetric) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ESGMetricCreate(BaseModel):
    """ESG 지표 생성 요청 스키마."""

    metric_name: str
    category: str = ""
    value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""
    target_value: Decimal = Decimal(0)


class ESGMetricUpdate(BaseModel):
    """ESG 지표 수정 요청 스키마."""

    metric_name: str | None = None
    category: str | None = None
    value: Decimal | None = None
    unit: str | None = None
    period: str | None = None
    target_value: Decimal | None = None


class ESGMetric(BaseDocument):
    """ESG 지표 문서."""

    metric_name: str = ""
    category: str = ""
    value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""
    target_value: Decimal = Decimal(0)
