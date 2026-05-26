# Calendar 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Calendar 서비스 ERD
---
erDiagram
    Calendar {
        string name
        string description
        string owner_id
        string visibility
        string color
        string timezone
        string status
    }

    CalendarEvent {
        string calendar_id
        string title
        string event_type
        datetime start_dt
        datetime end_dt
        boolean all_day
        string location
        string status
    }

    Invitee {
        string event_id
        string user_id
        string user_name
        string email
        boolean is_required
        string response_status
    }

    Reminder {
        string event_id
        number minutes_before
        string method
        boolean is_sent
    }

    Resource {
        string name
        string resource_type
        string description
        number capacity
        string location
        string status
    }

    ResourceBooking {
        string event_id
        string resource_id
        datetime start_dt
        datetime end_dt
        string booked_by
        string status
    }

    Holiday {
        string name
        date holiday_date
        string description
        boolean is_annual
        string country
    }

    Calendar ||--o{ CalendarEvent : "contains"
    CalendarEvent ||--o{ Invitee : "has"
    CalendarEvent ||--o{ Reminder : "has"
    CalendarEvent ||--o{ ResourceBooking : "books"
    Resource ||--o{ ResourceBooking : "reserved_by"
```
