# Marketing 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Marketing 서비스 ERD
---
erDiagram
    MarketingList {
        string name
        string source_type
        array members
        number member_count
        string company
    }

    EmailCampaign {
        string name
        string marketing_list_id
        string subject
        string template
        datetime scheduled_date
        string status
        number sent_count
        number open_count
    }

    SMSCampaign {
        string name
        string marketing_list_id
        string message
        datetime scheduled_date
        string status
        number sent_count
        number delivery_count
    }

    EventRegistration {
        string event_name
        string event_type
        string campaign_id
        datetime date
        string venue
        number max_attendees
        string status
    }

    Survey {
        string title
        string description
        string target_audience_id
        date start_date
        date end_date
        number response_count
        string status
    }

    SurveyResponse {
        string survey_id
        string respondent_id
        array answers
        datetime submitted_at
    }

    LoyaltyProgram {
        string program_name
        array earning_rules
        array redemption_rules
        number expiry_months
        boolean is_active
        string company
    }

    LoyaltyPoint {
        string customer_id
        string program_id
        string transaction_type
        number points
        datetime transaction_date
        date expiry_date
    }

    MarketingList ||--o{ EmailCampaign : "발송대상"
    MarketingList ||--o{ SMSCampaign : "발송대상"
    Survey ||--o{ SurveyResponse : "응답수집"
    LoyaltyProgram ||--o{ LoyaltyPoint : "포인트거래"
    EmailCampaign ||--o{ EventRegistration : "캠페인연결"
```
