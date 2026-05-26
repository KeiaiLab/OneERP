# RPA 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: RPA 서비스 ERD
---
erDiagram
    RPATask {
        string task_type
        string status
        string device_id
        number priority
        datetime started_at
        datetime completed_at
        number retry_count
        string error_message
    }

    RPAResult {
        string task_id
        string step_name
        boolean success
        string screenshot_url
        number duration_ms
        string error
    }

    RPATask ||--o{ RPAResult : "단계 결과"
```
