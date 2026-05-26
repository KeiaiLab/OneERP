# CLM 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: CLM 서비스 ERD
---
erDiagram
    Contract {
        string contract_name
        string contract_type
        string party_type
        string party_id
        date start_date
        date end_date
        number contract_value
        string currency
    }

    ContractTemplate {
        string template_name
        string contract_type
        string template_body
        array variables
        boolean approval_required
    }

    ContractRenewal {
        string contract_id
        date renewal_date
        date new_end_date
        number new_value
        number price_change_pct
        string approved_by
        string status
    }

    ContractTemplate ||--o{ Contract : "generates"
    Contract ||--o{ ContractRenewal : "renewed_by"
```
