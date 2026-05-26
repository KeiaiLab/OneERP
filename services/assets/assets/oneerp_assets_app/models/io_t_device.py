"""IoT 디바이스(IoTDevice) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class IoTDeviceStatus(StrEnum):
    """IoT 디바이스 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class IoTDeviceCreate(BaseModel):
    """IoT 디바이스 생성 요청 스키마."""

    device_name: str
    device_type: str = ""
    location: str = ""
    serial_number: str = ""
    is_active: bool = True


class IoTDeviceUpdate(BaseModel):
    """IoT 디바이스 수정 요청 스키마."""

    device_name: str | None = None
    device_type: str | None = None
    location: str | None = None
    serial_number: str | None = None
    is_active: bool | None = None


class IoTDevice(BaseDocument):
    """IoT 디바이스 문서."""

    status: IoTDeviceStatus = Field(
        default=IoTDeviceStatus.ACTIVE,
        description="IoT 디바이스 상태",
    )
    device_name: str = ""
    device_type: str = ""
    location: str = ""
    serial_number: str = ""
    is_active: bool = True
