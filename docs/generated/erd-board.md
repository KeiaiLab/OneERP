# Board 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Board 서비스 ERD
---
erDiagram
    Board {
        string board_name
        string board_type
        string scope
        string description
        array categories
        boolean is_active
        boolean allow_comments
        number sort_order
    }

    Post {
        string board_id
        string title
        string content
        string author_id
        string status
        boolean is_pinned
        number view_count
        number comment_count
    }

    Comment {
        string post_id
        string parent_id
        number depth
        string author_id
        string content
        boolean is_anonymous
        number like_count
    }

    Attachment {
        string post_id
        string file_name
        string file_key
        number file_size
        string mime_type
        string checksum
        number download_count
    }

    ReadConfirmation {
        string post_id
        string user_id
        string status
        datetime read_at
        number reminder_count
        datetime last_reminded_at
    }

    PopupNotice {
        string title
        string content
        string priority
        datetime start_at
        datetime end_at
        boolean is_active
        string show_frequency
        number confirmed_count
    }

    BoardPermission {
        string board_id
        string grantee_type
        string grantee_id
        string permission
        boolean is_active
        string granted_by
    }

    PostLike {
        string post_id
        string user_id
    }

    PostBookmark {
        string post_id
        string user_id
    }

    PostReport {
        string post_id
        string reporter_id
        string reason
        string description
        string status
        string reviewed_by
    }

    AuditLog {
        string entity_type
        string entity_id
        string action
        string actor_id
        string actor_ip
    }

    AutoPostRule {
        string rule_name
        string source_event
        string target_board_id
        string title_template
        string content_template
        boolean is_must_read
        boolean is_active
    }

    Board ||--o{ Post : "contains"
    Board ||--o{ BoardPermission : "has"
    Board ||--o{ AutoPostRule : "triggers"
    Post ||--o{ Comment : "has"
    Post ||--o{ Attachment : "has"
    Post ||--o{ ReadConfirmation : "requires"
    Post ||--o{ PostLike : "receives"
    Post ||--o{ PostBookmark : "receives"
    Post ||--o{ PostReport : "receives"
    Post ||--o| PopupNotice : "promoted_to"
```
