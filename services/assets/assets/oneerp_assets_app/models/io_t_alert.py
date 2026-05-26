"""IoT 경보(IoTAlert) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class IoTAlertStatus(StrEnum):
    """IoT 경보 상태."""

    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IoTAlertCreate(BaseModel):
    """IoT 경보 생성 요청 스키마."""

    device_id: str
    alert_type: str = ""
    threshold_value: Decimal = Decimal(0)
    actual_value: Decimal = Decimal(0)
    alert_date: date | None = None


class IoTAlertUpdate(BaseModel):
    """IoT 경보 수정 요청 스키마."""

    device_id: str | None = None
    alert_type: str | None = None
    threshold_value: Decimal | None = None
    actual_value: Decimal | None = None
    alert_date: date | None = None


class IoTAlert(BaseDocument):
    """IoT 경보 문서."""

    status: IoTAlertStatus = Field(
        default=IoTAlertStatus.TRIGGERED,
        description="IoT 경보 상태",
    )
    device_id: str = ""
    alert_type: str = ""
    threshold_value: Decimal = Decimal(0)
    actual_value: Decimal = Decimal(0)
    alert_date: date | None = None
