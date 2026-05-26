# STOCK 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: STOCK 서비스 ERD
---
erDiagram
    Batch {
        string batch_id
        string item_code
        date manufacturing_date
        date expiry_date
        string supplier_ref
        string status
    }
    BatchCreate {
        string item_code
        date manufacturing_date
        date expiry_date
        string supplier_ref
    }
    BOM {
        string item_code
        string item_name
        number quantity
        string items
        boolean is_active
        boolean is_default
    }
    Item {
        string item_code
        string item_name
        string item_group
        string stock_uom
        boolean is_stock_item
        boolean has_batch_no
        boolean has_serial_no
        string valuation_method
        string default_warehouse
    }
    ItemGroup {
        string group_name
        string parent_group
        boolean is_group
    }
    ItemPrice {
        string item_code
        string price_list
        number price
        string currency
        number min_qty
    }
    ItemVariant {
        string item_code
        string variant_of
        string attributes
    }
    JobCard {
        string work_order
        string operation
        string workstation
        string employee
        string status
        number planned_time
        number actual_time
        date started_at
        date completed_at
    }
    Operation {
        string operation_name
        string workstation
        number time_in_mins
        string description
        boolean is_active
    }
    PackingSlip {
        string delivery_note
        string items
    }
    PickList {
        string purpose
        string items
    }
    ProductionPlan {
        date planned_start
        date planned_end
        string status
        string items
    }
    ReorderLevel {
        string item_code
        string warehouse
        number reorder_level
        number reorder_qty
        string material_request_type
    }
    SerialNo {
        string serial_no
        string item_code
        string item_name
        string status
        string warehouse
        date purchase_date
        date delivery_date
    }
    StockEntry {
        string entry_id
        string entry_type
        string posting_date
        string items
        string remarks
    }
    StockLedgerEntry {
        string item_code
        string warehouse
        date posting_date
        number qty_change
        number valuation_rate
        number balance_qty
        number balance_value
        string voucher_type
        string voucher_no
        string batch_no
    }
    StockReconciliation {
        date posting_date
        string purpose
        string items
    }
    Warehouse {
        string warehouse_name
        string warehouse_type
        string parent_warehouse
        boolean is_group
        boolean is_active
        string company
    }
    WorkOrder {
        string production_item
        string bom_ref
        number qty
        date planned_start_date
        date planned_end_date
        date actual_start_date
        date actual_end_date
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
