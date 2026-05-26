"""IoT 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

4개 엔티티를 EntityMeta로 선언한다.
BarcodeConfiguration(마스터), IoTDevice(마스터),
IoTDataPoint(트랜잭션), IoTAlert(트랜잭션).
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.barcode_configuration import (
    BarcodeConfiguration,
    BarcodeConfigurationCreate,
    BarcodeConfigurationUpdate,
)
from .models.iot_alert import IoTAlert, IoTAlertCreate, IoTAlertUpdate
from .models.iot_data_point import IoTDataPoint, IoTDataPointCreate, IoTDataPointUpdate
from .models.iot_device import IoTDevice, IoTDeviceCreate, IoTDeviceUpdate

BARCODE_CONFIGURATION = EntityMeta(
    collection="barcode_configurations",
    prefix="BARC",
    api_path="/api/v1/barcode-configurations",
    tag="바코드 설정",
    resource="barcode_configuration",
    model=BarcodeConfiguration,
    create_schema=BarcodeConfigurationCreate,
    update_schema=BarcodeConfigurationUpdate,
    archetype="master",
    not_found_message="바코드 설정을 찾을 수 없습니다",
)

IOT_DEVICE = EntityMeta(
    collection="iot_devices",
    prefix="IOT",
    api_path="/api/v1/iot-devices",
    tag="IoT 장치",
    resource="iot_device",
    model=IoTDevice,
    create_schema=IoTDeviceCreate,
    update_schema=IoTDeviceUpdate,
    archetype="master",
    not_found_message="IoT 장치를 찾을 수 없습니다",
)

IOT_DATA_POINT = EntityMeta(
    collection="iot_data_points",
    prefix="IOTD",
    api_path="/api/v1/iot-data-points",
    tag="IoT 데이터 포인트",
    resource="iot_data_point",
    model=IoTDataPoint,
    create_schema=IoTDataPointCreate,
    update_schema=IoTDataPointUpdate,
    archetype="transaction",
    not_found_message="IoT 데이터 포인트를 찾을 수 없습니다",
)

IOT_ALERT = EntityMeta(
    collection="iot_alerts",
    prefix="IOTA",
    api_path="/api/v1/iot-alerts",
    tag="IoT 알림",
    resource="iot_alert",
    model=IoTAlert,
    create_schema=IoTAlertCreate,
    update_schema=IoTAlertUpdate,
    archetype="transaction",
    not_found_message="IoT 알림을 찾을 수 없습니다",
)

ENTITY_METAS = [
    BARCODE_CONFIGURATION,
    IOT_DEVICE,
    IOT_DATA_POINT,
    IOT_ALERT,
]
