# Maintenance 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Maintenance 서비스 ERD
---
erDiagram
    Equipment {
        string equipment_name
        string equipment_code
        string category
        string location
        string status
        number purchase_cost
        string criticality
        number mtbf_hours
    }

    MaintenanceType {
        string type_name
        string type_code
        string category
        string description
        string default_priority
        number estimated_hours
    }

    WorkOrder {
        string equipment_id
        string title
        string work_order_type
        string priority
        string status
        date scheduled_date
        number total_cost
        string assigned_to
    }

    MaintenanceRecord {
        string work_order_id
        string equipment_id
        date record_date
        string maintenance_type
        string performed_by
        number labor_hours
        number material_cost
    }

    PreventiveMaintenancePlan {
        string plan_name
        string equipment_id
        string maintenance_type_id
        number interval_days
        date start_date
        boolean is_active
        date next_due_date
    }

    BreakdownReport {
        string equipment_id
        string reported_by
        string failure_mode
        string severity
        string status
        datetime reported_at
        string work_order_id
    }

    InspectionChecklist {
        string checklist_name
        string equipment_category
        string description
        array items
        boolean is_active
    }

    InspectionResult {
        string checklist_id
        string equipment_id
        date inspection_date
        string inspector
        string overall_outcome
        array item_results
    }

    MaintenanceSparePart {
        string part_name
        string part_code
        number qty_on_hand
        number reorder_level
        number unit_cost
        string warehouse_location
    }

    EquipmentAvailability {
        string equipment_id
        date period_start
        date period_end
        number operating_hours
        number downtime_hours
        number availability_rate
        number failure_count
    }

    Equipment ||--o{ WorkOrder : "작업지시 발행"
    Equipment ||--o{ BreakdownReport : "고장신고"
    Equipment ||--o{ PreventiveMaintenancePlan : "예방보전"
    Equipment ||--o{ InspectionResult : "점검결과"
    Equipment ||--o{ EquipmentAvailability : "가동율"
    WorkOrder ||--o{ MaintenanceRecord : "작업기록"
    BreakdownReport ||--o| WorkOrder : "작업지시 생성"
    PreventiveMaintenancePlan ||--o{ WorkOrder : "자동 생성"
    InspectionChecklist ||--o{ InspectionResult : "점검수행"
    MaintenanceSparePart }o--o{ WorkOrder : "자재사용"
    MaintenanceType ||--o{ PreventiveMaintenancePlan : "보전유형"
```
