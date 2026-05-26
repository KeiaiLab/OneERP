# Marketing-Automation 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Marketing-Automation 서비스 ERD
---
erDiagram
    Campaign {
        string campaign_name
        string campaign_type
        string channel
        string status
        date start_date
        date end_date
        number budget
        number spent
    }

    AudienceSegment {
        string segment_name
        string segment_type
        string source
        string description
        boolean is_active
        number member_count
    }

    AutomationWorkflow {
        string workflow_name
        string trigger_type
        array steps
        string description
        boolean is_active
        number enrolled_count
        number completed_count
    }

    CampaignAnalytics {
        string campaign_id
        string event_type
        string recipient_id
        string channel
        datetime event_at
        number revenue_attributed
    }

    EmailTemplate {
        string template_name
        string subject
        string body_html
        string sender_name
        string sender_email
        string category
        boolean is_active
        number usage_count
    }

    Campaign ||--o{ CampaignAnalytics : "성과분석"
    Campaign }o--|| AudienceSegment : "타겟오디언스"
    Campaign ||--o{ AutomationWorkflow : "자동화연결"
    AutomationWorkflow }o--o{ EmailTemplate : "템플릿사용"
```
