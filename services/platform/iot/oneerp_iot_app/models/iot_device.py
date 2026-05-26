"""IoT 장치(IoTDevice) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class IoTDeviceCreate(BaseModel):
    """IoT 장치 생성 요청 스키마."""

    device_name: str
    device_type: str = "sensor"
    protocol: str = "mqtt"
    location: str = ""
    ip_address: str = ""
    firmware_version: str = ""
    polling_interval: int = 60
    alert_rules: list[dict[str, Any]] = []
    last_heartbeat: datetime | None = None
    status: str = "active"


class IoTDeviceUpdate(BaseModel):
    """IoT 장치 수정 요청 스키마."""

    device_name: str | None = None
    device_type: str | None = None
    protocol: str | None = None
    location: str | None = None
    ip_address: str | None = None
    firmware_version: str | None = None
    polling_interval: int | None = None
    alert_rules: list[dict[str, Any]] | None = None
    last_heartbeat: datetime | None = None
    status: str | None = None


class IoTDevice(BaseDocument):
    """IoT 장치 문서."""

    device_name: str = ""
    device_type: str = "sensor"
    protocol: str = "mqtt"
    location: str = ""
    ip_address: str = ""
    firmware_version: str = ""
    polling_interval: int = 60
    alert_rules: list[dict[str, Any]] = []
    last_heartbeat: datetime | None = None
    status: str = "active"
