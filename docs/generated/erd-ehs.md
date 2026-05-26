# EHS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: EHS 서비스 ERD
---
erDiagram
    SafetyIncident {
        datetime incident_date
        string location
        string incident_type
        string severity
        string employee
        string description
        string status
        boolean reported_to_kosha
    }

    HealthCheckup {
        string employee
        string checkup_type
        date scheduled_date
        string hospital
        date completed_date
        string result_summary
        string status
    }

    HazardousMaterial {
        string material_name
        string cas_number
        array ghs_classification
        string msds_document
        string storage_conditions
        number max_storage_qty
        number current_qty
        string emergency_contact
    }

    SafetyTraining {
        string training_name
        string training_type
        string legal_basis
        array target_employees
        date scheduled_date
        number duration_hours
        string instructor
        string status
    }
```
