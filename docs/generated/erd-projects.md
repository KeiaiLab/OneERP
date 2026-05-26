# PROJECTS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: PROJECTS 서비스 ERD
---
erDiagram
    ActivityType {
        string activity_type
        number costing_rate
        number billing_rate
    }
    Milestone {
        string milestone_name
        string project
        date due_date
        string status
        string description
    }
    Project {
        string project_name
        string status
        date expected_start_date
        date expected_end_date
        number percent_complete
        string company
        string cost_center
    }
    ProjectBilling {
        string project_id
        date billing_date
        number amount
        string billing_type
        boolean is_invoiced
    }
    ProjectRevenueRecognition {
        string project_id
        date recognition_date
        number recognized_amount
        number total_contract_value
        number completion_percentage
    }
    ProjectRisk {
        string project_id
        string risk_name
        string probability
        string impact
        string mitigation
        string owner
    }
    ProjectTemplate {
        string template_name
        string description
        array default_tasks
        number estimated_days
    }
    ResourceAllocation {
        string project_id
        string employee_id
        number allocation_percentage
        date start_date
        date end_date
    }
    Task {
        string subject
        string project_ref
        string assigned_to
        string priority
        string status
        number expected_time
        number actual_time
    }
    TaskTemplate {
        string template_name
        string description
        number estimated_hours
        array dependencies
    }
    Timesheet {
        string employee_id
        string employee_name
        date start_date
        date end_date
        number total_hours
        array time_logs
    }
    WbsElement {
        string project_id
        string element_code
        string element_name
        string parent_id
        number level
        number budget
    }
```
