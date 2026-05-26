"""IoT 데이터 포인트(IoTDataPoint) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class IoTDataPointCreate(BaseModel):
    """IoT 데이터 포인트 생성 요청 스키마."""

    device_id: str
    metric_name: str
    value: Decimal = Decimal(0)
    unit: str = ""
    timestamp: datetime | None = None
    quality: str = "good"


class IoTDataPointUpdate(BaseModel):
    """IoT 데이터 포인트 수정 요청 스키마."""

    device_id: str | None = None
    metric_name: str | None = None
    value: Decimal | None = None
    unit: str | None = None
    timestamp: datetime | None = None
    quality: str | None = None


class IoTDataPoint(BaseDocument):
    """IoT 데이터 포인트 문서."""

    device_id: str = ""
    metric_name: str = ""
    value: Decimal = Decimal(0)
    unit: str = ""
    timestamp: datetime | None = None
    quality: str = "good"
