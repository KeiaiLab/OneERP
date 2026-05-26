"""IoT 알림(IoTAlert) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class IoTAlertCreate(BaseModel):
    """IoT 알림 생성 요청 스키마."""

    device_id: str
    data_point_id: str | None = None
    alert_type: str = "threshold"
    severity: str = "info"
    message: str = ""
    triggered_at: datetime | None = None
    acknowledged_by: str = ""
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    status: str = "triggered"


class IoTAlertUpdate(BaseModel):
    """IoT 알림 수정 요청 스키마."""

    device_id: str | None = None
    data_point_id: str | None = None
    alert_type: str | None = None
    severity: str | None = None
    message: str | None = None
    triggered_at: datetime | None = None
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    status: str | None = None


class IoTAlert(BaseDocument):
    """IoT 알림 문서."""

    device_id: str = ""
    data_point_id: str | None = None
    alert_type: str = "threshold"
    severity: str = "info"
    message: str = ""
    triggered_at: datetime | None = None
    acknowledged_by: str = ""
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    status: str = "triggered"
