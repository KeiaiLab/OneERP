# Survey 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Survey 서비스 ERD
---
erDiagram
    Survey {
        string title
        string survey_type
        string anonymity
        string status
        datetime starts_at
        datetime ends_at
        string target_type
        number response_count
    }

    SurveyQuestion {
        string survey_id
        string question_text
        string question_type
        boolean required
        number order
        number scale_min
        number scale_max
    }

    SurveyResponse {
        string survey_id
        string respondent_id
        string respondent_department
        datetime submitted_at
        string ip_hash
    }

    SurveyTemplate {
        string name
        string category
        string description
        boolean is_system
        number usage_count
    }

    Poll {
        string title
        string poll_type
        string anonymity
        string status
        datetime ends_at
        string show_results
        number total_votes
    }

    PollVote {
        string poll_id
        string voter_id
        array selected_options
        datetime voted_at
        string voter_hash
    }

    Survey ||--o{ SurveyQuestion : "질문 포함"
    Survey ||--o{ SurveyResponse : "응답 수집"
    SurveyTemplate ||--o{ Survey : "템플릿 기반 생성"
    Poll ||--o{ PollVote : "투표 기록"
```
