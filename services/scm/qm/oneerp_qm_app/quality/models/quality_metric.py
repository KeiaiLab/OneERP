"""품질 지표(QualityMetric) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class QualityMetricCreate(BaseModel):
    """품질 지표 생성 요청 스키마."""

    metric_name: str
    target_value: Decimal = Decimal(0)
    actual_value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""


class QualityMetricUpdate(BaseModel):
    """품질 지표 수정 요청 스키마."""

    metric_name: str | None = None
    target_value: Decimal | None = None
    actual_value: Decimal | None = None
    unit: str | None = None
    period: str | None = None


class QualityMetric(BaseDocument):
    """품질 지표 문서."""

    metric_name: str = ""
    target_value: Decimal = Decimal(0)
    actual_value: Decimal = Decimal(0)
    unit: str = ""
    period: str = ""
