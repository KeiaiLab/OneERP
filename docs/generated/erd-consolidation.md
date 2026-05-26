# CONSOLIDATION 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: CONSOLIDATION 서비스 ERD
---
erDiagram
    ConsolidationEntity {
        string entity_code
        string entity_name
        string entity_type
        string country_code
        string functional_currency
        string consolidation_method
        boolean is_parent
        string status
    }
    InvestmentRelation {
        string investor_entity_id
        string investee_entity_id
        number ownership_percentage
        number voting_rights_percentage
        date acquisition_date
        number acquisition_cost
        number goodwill
        string status
    }
    EliminationRule {
        string rule_code
        string rule_name
        string elimination_type
        number priority
        boolean is_automatic
        boolean is_recurring
        string status
    }
    ConsolidationPeriod {
        string period_name
        string period_type
        date from_date
        date to_date
        string fiscal_year
        string status
        string elimination_status
        string translation_status
    }
    ConsolidatedReport {
        string report_type
        string status
        string period_id
        array line_items
        array entity_breakdowns
        array elimination_breakdowns
    }
    CurrencyTranslation {
        string period_id
        string entity_id
        string source_currency
        string target_currency
        number closing_rate
        number average_rate
        number fcta_amount
        string status
    }
    IntercompanyBalance {
        string period_id
        string entity_a_id
        string entity_b_id
        string balance_type
        number entity_a_amount
        number entity_b_amount
        number difference_amount
        string match_status
    }
```
