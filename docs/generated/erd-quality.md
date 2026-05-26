# QUALITY 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: QUALITY 서비스 ERD
---
erDiagram
    Capa {
        string capa_type
        string problem_description
        string root_cause
        string corrective_action
        string responsible
        date due_date
        boolean is_closed
    }
    CertificateOfAnalysis {
        string item_code
        string batch_no
        date test_date
        string test_results
        boolean is_passed
        string issued_by
    }
    InspectionResult {
        string inspection_id
        string parameter
        string result
        string status
        string remarks
    }
    NonConformance {
        string title
        string description
        string severity
        string item_code
        string inspection_id
        string corrective_action
    }
    QualityAction {
        string action_name
        string action_type
        string responsible
        date due_date
        boolean is_completed
    }
    QualityGoal {
        string goal_name
        number target_value
        number current_value
        string unit
        string period
        string status
    }
    QualityInspection {
        string reference_type
        string reference_no
        string inspection_type
        string item_code
        array readings
        string result
    }
    QualityInspectionTemplate {
        string template_name
        string inspection_type
        string parameters
    }
    QualityMeeting {
        string meeting_title
        date meeting_date
        array attendees
        string agenda
        string minutes
    }
    QualityMetric {
        string metric_name
        number target_value
        number actual_value
        string unit
        string period
    }
    QualityProcedure {
        string procedure_name
        string description
        string process_owner
        string revision
        boolean is_active
    }
    QualityReview {
        string review_name
        date review_date
        string reviewer
        string findings
        number score
    }
    RmaInspection {
        string rma_id
        date inspection_date
        string inspector
        string condition
        string findings
        string disposition
    }
```
