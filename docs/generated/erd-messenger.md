# Messenger 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Messenger 서비스 ERD
---
erDiagram
    Channel {
        string channel_name
        string channel_type
        string description
        array members
        string owner_id
        string status
        array pinned_message_ids
    }

    Message {
        string channel_id
        string sender_id
        string content
        string message_type
        string status
        string parent_message_id
        array mentions
        number thread_count
    }

    Thread {
        string channel_id
        string root_message_id
        array participants
        number reply_count
        string last_reply_at
    }

    Notification {
        string user_id
        string notification_type
        string title
        string body
        string reference_id
        string channel_id
        boolean is_read
    }

    Bookmark {
        string user_id
        string message_id
        string channel_id
        string note
    }

    UserPresence {
        string user_id
        string status
        string status_message
        datetime last_seen_at
    }

    Channel ||--o{ Message : "메시지전송"
    Channel ||--o{ Thread : "스레드"
    Message ||--o| Thread : "루트메시지"
    Message ||--o{ Bookmark : "북마크"
    Channel ||--o{ Notification : "알림발생"
    Message }o--|| UserPresence : "발신자상태"
```
