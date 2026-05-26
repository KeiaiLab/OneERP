# Fleet 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Fleet 서비스 ERD
---
erDiagram
    Vehicle {
        string vehicle_no
        string vehicle_name
        string make
        string model
        number year
        string fuel_type
        date acquisition_date
        number acquisition_cost
    }

    VehicleAssignment {
        string vehicle
        string employee
        string department
        date start_date
        date end_date
        string assignment_type
        string status
    }

    VehicleLog {
        string vehicle
        string driver
        date log_date
        number start_odometer
        number end_odometer
        number distance
        string purpose
    }

    VehicleMaintenance {
        string vehicle
        string maintenance_type
        date maintenance_date
        string description
        number cost
        string vendor
        date next_due_date
        string status
    }

    FuelEntry {
        string vehicle
        date entry_date
        string fuel_type
        number quantity
        number amount
        number odometer
        number fuel_efficiency
        string gas_station
    }

    Vehicle ||--o{ VehicleAssignment : "vehicle"
    Vehicle ||--o{ VehicleLog : "vehicle"
    Vehicle ||--o{ VehicleMaintenance : "vehicle"
    Vehicle ||--o{ FuelEntry : "vehicle"
```
