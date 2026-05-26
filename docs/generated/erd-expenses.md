# EXPENSES 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: EXPENSES 서비스 ERD
---
erDiagram
    CorporateCard {
        string card_number
        string employee
        string card_type
        number credit_limit
        boolean is_active
    }
    CorporateCardTransaction {
        string card_number
        date transaction_date
        string merchant
        number amount
    }
    ExpenseClaim {
        string employee
        date posting_date
        number total_amount
        string approval_status
        string items
    }
    ExpenseType {
        string expense_type_name
        string account
        string description
    }
    TravelRequest {
        string employee
        string purpose
        date departure_date
        date return_date
        string destination
        number estimated_cost
    }
```
