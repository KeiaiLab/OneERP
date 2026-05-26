# MANUFACTURING 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: MANUFACTURING 서비스 ERD
---
erDiagram
    BOM {
        string item_code
        string item_name
        number quantity
        array items
        boolean is_active
        boolean is_default
    }
    BOMRevision {
        string status
        string bom_id
        number revision_no
        string change_description
        date effective_date
    }
    BOMTree {
        string parent_bom_id
        string child_item_code
        number qty
        number level
        string uom
    }
    ByProduct {
        string work_order_id
        string item_code
        number qty
        string warehouse_id
    }
    CapacityPlan {
        string status
        string workstation_id
        string period
        number available_hours
        number planned_hours
        number utilization_rate
    }
    DemandForecast {
        string status
        string item_code
        number forecast_qty
        string period
        string forecast_type
        number confidence_level
    }
    DowntimeEntry {
        string workstation_id
        string start_time
        string end_time
        number duration_minutes
        string reason
    }
    EngineeringChangeOrder {
        string status
        string change_title
        array affected_items
        string reason
        date effective_date
    }
    EngineeringDocument {
        string status
        string document_title
        string document_type
        string item_code
        string version
        string file_path
    }
    JobCard {
        string work_order
        string operation
        string workstation
        string employee_id
        string status
        number planned_time
        number actual_time
    }
    MRPRun {
        string status
        string forecast_id
        date run_date
        number generated_purchase_requests
        number generated_work_orders
    }
    OeeMetric {
        string workstation_id
        string period
        number availability
        number performance
        number quality_rate
        number oee
    }
    Operation {
        string operation_name
        string workstation
        number time_in_mins
        string description
        boolean is_active
    }
    ProcessLoss {
        string work_order_id
        string item_code
        number expected_qty
        number actual_qty
        number loss_qty
        number loss_percentage
    }
    ProductionCost {
        string item_code
        string item_name
        number material_cost
        number labour_cost
        number overhead_cost
        number total_cost
        string work_order
    }
    ProductionPlan {
        date planned_start
        date planned_end
        string status
        array items
    }
    ProductionVarianceAnalysis {
        string status
        string work_order_id
        number planned_cost
        number actual_cost
        number variance
        number variance_percentage
    }
    Routing {
        string routing_name
        string item_code
        array operations
        number total_time_minutes
    }
    SubcontractingOrder {
        string status
        string supplier_id
        string item_code
        number qty
        date expected_delivery
        number total_cost
    }
    SupplyPlan {
        string status
        string item_code
        number planned_qty
        string source_type
        date planned_start
        date planned_end
    }
    WorkOrder {
        string production_item
        string bom_ref
        number qty
        date planned_start_date
        string status
        string warehouse
    }
    Workstation {
        string workstation_name
        number production_capacity
        number hourly_rate
        boolean is_active
    }
```
