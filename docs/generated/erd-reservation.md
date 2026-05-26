# Reservation 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Reservation 서비스 ERD
---
erDiagram
    Resource {
        string name
        string resource_type
        string description
        string location
        number capacity
        string status
        string available_hours_start
        string available_hours_end
    }

    Reservation {
        string resource_id
        string title
        string requester_id
        string requester_name
        datetime start_time
        datetime end_time
        string status
        boolean checked_in
    }

    ReservationPolicy {
        string name
        string resource_type
        number max_duration_minutes
        number max_advance_days
        number cancellation_deadline_minutes
        number max_concurrent_reservations
        number auto_release_minutes
        boolean requires_approval
    }

    Resource ||--o{ Reservation : "예약생성"
    ReservationPolicy ||--o{ Resource : "정책적용"
```
