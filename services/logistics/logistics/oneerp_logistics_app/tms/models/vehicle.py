"""차량(Vehicle) 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    """��량 생성 요청."""

    vehicle_no: str
    vehicle_type: str  # truck_1t/truck_2_5t/truck_5t/truck_11t/truck_25t/wing_body/refrigerated/frozen/motorcycle
    carrier_id: str | None = None
    max_weight_kg: float
    max_volume_cbm: float | None = None
    temperature_type: str = "normal"  # normal/refrigerated/frozen
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_license_no: str | None = None
    gps_device_id: str | None = None
    status: str = "available"
    company: str = ""


class VehicleUpdate(BaseModel):
    """차량 ��정 요청."""

    vehicle_no: str | None = None
    vehicle_type: str | None = None
    carrier_id: str | None = None
    max_weight_kg: float | None = None
    max_volume_cbm: float | None = None
    temperature_type: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_license_no: str | None = None
    gps_device_id: str | None = None
    status: str | None = None
    company: str | None = None


class Vehicle(BaseDocument):
    """차량 마스터 — 운송 차량 정보.

    naming prefix: VHC
    """

    vehicle_no: str = Field(default="", description="차량번호")
    vehicle_type: str = Field(default="", description="차량 유형")
    carrier_id: str | None = Field(default=None, description="소속 운송사 (null=자차)")
    max_weight_kg: float = Field(default=0.0, description="최대 적재량 (kg)")
    max_volume_cbm: float | None = Field(default=None, description="최대 적재 용적 (m3)")
    temperature_type: str = Field(default="normal", description="온도 유형")
    driver_name: str | None = Field(default=None, description="운전자명")
    driver_phone: str | None = Field(default=None, description="운전자 연락처")
    driver_license_no: str | None = Field(default=None, description="운전면허번호")
    gps_device_id: str | None = Field(default=None, description="GPS 단말기 ID")
    status: str = Field(default="available", description="차량 상태")
    company: str = Field(default="", description="회사")
