# TMS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: TMS 서비스 ERD
---
erDiagram
    Carrier {
        string carrier_name
        string carrier_type
        string business_no
        string contact_name
        number performance_score
        boolean is_active
    }

    Vehicle {
        string vehicle_no
        string vehicle_type
        string carrier_id
        number max_weight_kg
        string temperature_type
        string status
        string driver_name
    }

    Route {
        string route_name
        number distance_km
        number estimated_minutes
        string preferred_carrier_id
        string region_group
        boolean is_active
    }

    Shipment {
        string shipment_no
        string carrier_id
        string vehicle_id
        string tracking_no
        string status
        number total_weight_kg
        number freight_amount
        boolean is_return
    }

    DeliveryOrder {
        string order_no
        date dispatch_date
        string carrier_id
        string vehicle_id
        number total_shipments
        string status
        string dispatch_method
    }

    TrackingEvent {
        string shipment_id
        datetime event_time
        string event_type
        string status_code
        string description
        string source
    }

    ProofOfDelivery {
        string shipment_id
        datetime delivery_time
        string receiver_name
        string delivery_status
        string signature_image_url
    }

    ReturnShipment {
        string return_no
        string original_shipment_id
        string return_reason
        string carrier_id
        string status
        number freight_amount
        datetime expected_pickup
    }

    FreightRate {
        string carrier_id
        string route_id
        string rate_type
        number base_amount
        number per_kg_amount
        date effective_from
        boolean is_active
    }

    FreightSettlement {
        string settlement_no
        string carrier_id
        date period_from
        date period_to
        number total_amount
        string status
        string currency
    }

    DeliveryCondition {
        string customer_id
        string temperature_requirement
        boolean requires_pod
        boolean requires_appointment
        boolean is_active
        string preferred_carrier_id
    }

    Carrier ||--o{ Vehicle : "보유 차량"
    Carrier ||--o{ Shipment : "운송 수행"
    Carrier ||--o{ FreightRate : "운임 단가"
    Carrier ||--o{ FreightSettlement : "운임 정산"
    Carrier ||--o{ DeliveryOrder : "배차 배정"
    Route ||--o{ Shipment : "경로 배정"
    DeliveryOrder ||--o{ Shipment : "배차 포함"
    Shipment ||--o{ TrackingEvent : "추적 이벤트"
    Shipment ||--o| ProofOfDelivery : "배송 증빙"
    Shipment ||--o| ReturnShipment : "반품 운송"
```
