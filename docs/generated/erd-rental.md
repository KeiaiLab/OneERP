# Rental 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Rental 서비스 ERD
---
erDiagram
    RentalItem {
        string item_code
        string item_name
        string category
        number daily_rate
        number monthly_rate
        number deposit_amount
        string status
        number total_rental_count
    }

    RentalOrder {
        string customer_id
        string customer_name
        string rental_item_id
        date start_date
        date end_date
        string billing_cycle
        number total_amount
        string status
    }

    RentalReturn {
        string rental_order_id
        date return_date
        string condition
        number damage_charge
        number late_fee
        number deposit_refund
    }

    RentalInvoice {
        string rental_order_id
        string customer_id
        date invoice_date
        date due_date
        number rental_amount
        number tax_amount
        number total_amount
        string status
    }

    RentalMaintenance {
        string rental_item_id
        string maintenance_type
        date scheduled_date
        date completed_date
        number cost
        string status
        string technician
    }

    RentalItem ||--o{ RentalOrder : "렌탈주문"
    RentalOrder ||--o| RentalReturn : "반납처리"
    RentalOrder ||--o{ RentalInvoice : "청구서발행"
    RentalItem ||--o{ RentalMaintenance : "유지보수"
```
