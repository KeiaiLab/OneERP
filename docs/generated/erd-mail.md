# Mail 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Mail 서비스 ERD
---
erDiagram
    MailMessage {
        string subject
        string body
        string sender_id
        array recipients
        string priority
        string status
        boolean is_reply
        boolean is_forward
    }

    MailFolder {
        string name
        string owner_id
        string parent_folder_id
        string color
        number depth
        boolean is_system
        number message_count
        number unread_count
    }

    MailTemplate {
        string template_name
        string subject_template
        string body_template
        string category
        array variables
        boolean is_active
        number usage_count
    }

    MailRecipientStatus {
        string message_id
        string user_id
        string status
        string folder
        boolean is_starred
        boolean is_deleted
        string read_at
    }

    MailAutoRule {
        string rule_name
        string owner_id
        array conditions
        array actions
        number priority_order
        boolean is_active
        number applied_count
    }

    MailDistributionList {
        string list_name
        string description
        array members
        string owner_id
        boolean is_active
        number member_count
    }

    MailMessage ||--o{ MailRecipientStatus : "message_id"
    MailFolder ||--o{ MailFolder : "parent_folder_id"
    MailFolder ||--o{ MailMessage : "folder"
    MailAutoRule ||--o{ MailFolder : "move_to_folder"
```
