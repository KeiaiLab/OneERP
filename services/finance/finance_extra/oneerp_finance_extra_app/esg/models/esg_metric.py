"""ESG 지표(ESGMetric) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ESGMetricCreate(BaseModel):
    """ESG 지표 생성 요청 스키마."""

    metric_code: str
    metric_name: str
    category: str = ""
    unit: str = ""
    target_value: Decimal = Decimal(0)
    description: str = ""
    is_mandatory: bool = False
    regulation_reference: str = ""


class ESGMetricUpdate(BaseModel):
    """ESG 지표 수정 요청 스키마."""

    metric_code: str | None = None
    metric_name: str | None = None
    category: str | None = None
    unit: str | None = None
    target_value: Decimal | None = None
    description: str | None = None
    is_mandatory: bool | None = None
    regulation_reference: str | None = None


class ESGMetric(BaseDocument):
    """ESG 지표 문서."""

    metric_code: str = ""
    metric_name: str = ""
    category: str = ""
    unit: str = ""
    target_value: Decimal = Decimal(0)
    description: str = ""
    is_mandatory: bool = False
    regulation_reference: str = ""
