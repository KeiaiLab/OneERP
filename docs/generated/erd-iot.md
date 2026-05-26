# IoT 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: IoT 서비스 ERD
---
erDiagram
    IoTDevice {
        string device_name
        string device_type
        string protocol
        string location
        string ip_address
        string firmware_version
        number polling_interval
        string status
    }

    IoTDataPoint {
        string device_id
        string metric_name
        number value
        string unit
        datetime timestamp
        string quality
    }

    IoTAlert {
        string device_id
        string data_point_id
        string alert_type
        string severity
        string message
        datetime triggered_at
        string acknowledged_by
        string status
    }

    BarcodeConfiguration {
        string barcode_type
        string prefix
        array ai_codes
        string label_template
        boolean auto_generate
    }

    IoTDevice ||--o{ IoTDataPoint : "device_id"
    IoTDevice ||--o{ IoTAlert : "device_id"
    IoTDataPoint ||--o{ IoTAlert : "data_point_id"
```
