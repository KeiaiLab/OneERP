# ASSETS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: ASSETS 서비스 ERD
---
erDiagram
    Asset {
        string asset_name
        string asset_category
        date purchase_date
        number gross_amount
        string depreciation_method
        number useful_life_years
        number current_value
        string status
    }
    AssetAudit {
        date audit_date
        string auditor
        string asset
        string location
        string condition
        string remarks
    }
    AssetCategory {
        string category_name
        string depreciation_method
        number useful_life_years
        number depreciation_rate
    }
    AssetDisposal {
        string asset
        string asset_name
        date disposal_date
        string disposal_method
        number sale_amount
        number book_value
        number gain_loss
    }
    AssetImpairment {
        string asset_id
        date impairment_date
        number carrying_amount
        number recoverable_amount
        number impairment_loss
    }
    AssetInsurance {
        string asset_id
        string insurer
        string policy_number
        number coverage_amount
        number premium
        date start_date
        date end_date
    }
    AssetMaintenancePlan {
        string plan_name
        string asset_category
        string frequency
        array checklist
        boolean is_active
    }
    AssetMovement {
        string asset
        string asset_name
        string from_location
        string to_location
        date movement_date
        string purpose
    }
    AssetRepair {
        string asset_id
        date repair_date
        string failure_description
        number repair_cost
        string vendor
        boolean is_completed
    }
    AssetRevaluation {
        string asset_id
        date revaluation_date
        number current_value
        number revalued_amount
        string revaluation_method
    }
    AssetValueAdjustment {
        string asset_id
        date adjustment_date
        number old_value
        number new_value
        string reason
    }
    DepreciationEntry {
        string asset_ref
        date posting_date
        number depreciation_amount
        number accumulated_depreciation
        number remaining_value
    }
    DepreciationComparison {
        string asset_id
        string method_1
        string method_2
        number amount_1
        number amount_2
        number difference
    }
    EquipmentDowntime {
        string asset_id
        date start_date
        date end_date
        number duration_hours
        string reason
        string impact
    }
    FuelEntry {
        string vehicle_id
        date fuel_date
        string fuel_type
        number quantity
        number unit_price
        number total_cost
        number odometer
    }
    IoTAlert {
        string status
        string device_id
        string alert_type
        number threshold_value
        number actual_value
        date alert_date
    }
    IoTDataPoint {
        string device_id
        string metric_name
        number value
        string unit
        string recorded_at
    }
    IoTDevice {
        string status
        string device_name
        string device_type
        string location
        string serial_number
        boolean is_active
    }
    MaintenanceLog {
        string asset_id
        date log_date
        string maintenance_type
        string description
        number cost
        string performed_by
    }
    MaintenanceRequest {
        string asset_id
        date request_date
        string description
        string priority
        string requested_by
        boolean is_resolved
    }
    MaintenanceSchedule {
        string asset_id
        string schedule_name
        string frequency
        date last_maintenance
        date next_maintenance
        boolean is_active
    }
    MaintenanceVisit {
        string maintenance_request_id
        date visit_date
        string technician
        string work_done
        number duration_hours
        number cost
    }
    SparePart {
        string part_name
        string part_code
        array compatible_assets
        number qty_on_hand
        number reorder_level
        number unit_cost
    }
    Vehicle {
        string vehicle_name
        string license_plate
        string vehicle_type
        string make
        string model
        number year
        string fuel_type
    }
    VehicleAssignment {
        string vehicle_id
        string employee_id
        date assignment_date
        date return_date
        string purpose
    }
    VehicleLog {
        string vehicle_id
        string driver_id
        date log_date
        number odometer_start
        number odometer_end
        number distance_km
        number fuel_consumed
    }
    VehicleMaintenance {
        string vehicle_id
        string maintenance_type
        date maintenance_date
        number cost
        date next_maintenance_date
    }
```
