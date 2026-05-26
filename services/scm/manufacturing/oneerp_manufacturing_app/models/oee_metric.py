"""OEE 지표(OeeMetric) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class OeeMetricCreate(BaseModel):
    """OEE 지표 생성 요청 스키마."""

    workstation_id: str
    period: str = ""
    availability: Decimal = Decimal(0)
    performance: Decimal = Decimal(0)
    quality_rate: Decimal = Decimal(0)
    oee: Decimal = Decimal(0)


class OeeMetricUpdate(BaseModel):
    """OEE 지표 수정 요청 스키마."""

    workstation_id: str | None = None
    period: str | None = None
    availability: Decimal | None = None
    performance: Decimal | None = None
    quality_rate: Decimal | None = None
    oee: Decimal | None = None


class OeeMetric(BaseDocument):
    """OEE 지표 문서."""

    workstation_id: str = ""
    period: str = ""
    availability: Decimal = Decimal(0)
    performance: Decimal = Decimal(0)
    quality_rate: Decimal = Decimal(0)
    oee: Decimal = Decimal(0)
