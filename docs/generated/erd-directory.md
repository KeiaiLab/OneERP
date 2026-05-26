# Directory 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Directory 서비스 ERD
---
erDiagram
    Organization {
        string org_code
        string org_name
        string org_name_en
        string parent_org_id
        string representative
        string business_number
        string address
        string status
    }

    OrgUnit {
        string org_id
        string unit_code
        string unit_name
        string unit_type
        string parent_unit_id
        string head_employee_id
        string cost_center
        string status
    }

    Position {
        string org_unit_id
        string position_code
        string position_title
        string grade
        number headcount
        number filled_count
        string status
    }

    EmployeeDirectory {
        string employee_id
        string employee_name
        string org_unit_id
        string position_id
        string designation
        string email
        boolean is_primary
        string status
    }

    OrgChartSnapshot {
        string org_id
        date snapshot_date
        string description
        array tree_data
        number total_units
        number total_employees
    }

    Organization ||--o{ OrgUnit : "contains"
    OrgUnit ||--o{ Position : "defines"
    OrgUnit ||--o{ EmployeeDirectory : "belongs_to"
    Position ||--o{ EmployeeDirectory : "assigned_to"
    Organization ||--o{ OrgChartSnapshot : "snapshot_of"
```
