# Portal 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Portal 서비스 ERD
---
erDiagram
    PortalLayout {
        string layout_name
        string scope
        string scope_value
        number grid_columns
        number grid_row_height
        array widgets
        boolean is_locked
        string parent_layout_id
    }

    Widget {
        string widget_code
        string widget_name
        string widget_type
        string description
        number refresh_interval
        string required_permission
        string required_module
        boolean is_active
    }

    WidgetConfig {
        string widget_id
        string user_id
        boolean is_collapsed
        string custom_title
    }

    PersonalDashboard {
        string user_id
        string dashboard_name
        array widgets
        string base_layout_id
    }

    Announcement {
        string title
        string content
        string priority
        string status
        boolean is_mandatory
        datetime start_date
        datetime end_date
        number read_count
    }

    AnnouncementRead {
        string announcement_id
        string user_id
        datetime read_at
        datetime hide_until
    }

    NewsEvent {
        string title
        string content
        string event_type
        string status
        datetime event_date
        string published_by
        number view_count
    }

    SearchIndex {
        string doc_type
        string doc_id
        string title
        string content
        string module
        string url
        string required_permission
    }

    Shortcut {
        string shortcut_name
        string url
        string icon
        string color
        number sort_order
        string user_id
        number click_count
    }

    PortalLayout ||--o{ Widget : "위젯배치"
    Widget ||--o{ WidgetConfig : "개인설정"
    PortalLayout ||--o{ PersonalDashboard : "기반레이아웃"
    PersonalDashboard }o--o{ Widget : "위젯구성"
    Announcement ||--o{ AnnouncementRead : "읽음기록"
```
