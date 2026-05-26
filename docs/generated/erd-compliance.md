# Compliance 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Compliance 서비스 ERD
---
erDiagram
    InternalControl {
        string control_id
        string name
        string control_type
        string risk_area
        string frequency
        string responsible
        string status
    }

    ComplianceChecklist {
        string name
        string internal_control
        string period
        array items
        string completed_by
        string reviewed_by
        string status
    }

    ComplianceReport {
        string report_type
        string period
        string overall_rating
        string prepared_by
        string approved_by
        string status
        string company
    }

    RiskAssessment {
        string risk_name
        string risk_category
        number likelihood
        number impact
        number risk_score
        string mitigation
        string owner
        string status
    }

    AuditTrail {
        string entity_type
        string entity_id
        string action
        string user
        datetime timestamp
        string ip_address
    }

    DataPrivacyRecord {
        string processing_purpose
        string data_subjects
        string retention_period
        string legal_basis
        boolean transfer_to_third_party
        date dpo_review_date
        string status
    }

    RegulatorySandbox {
        string sandbox_type
        string project_name
        date approval_date
        date expiry_date
        string regulatory_body
        array exempted_regulations
        string status
    }

    InternalControl ||--o{ ComplianceChecklist : "verified_by"
    InternalControl ||--o{ ComplianceReport : "reported_in"
    RiskAssessment }o--|| InternalControl : "mitigated_by"
```
