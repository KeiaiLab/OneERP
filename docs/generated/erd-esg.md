# ESG 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: ESG 서비스 ERD
---
erDiagram
    SustainabilityReport {
        string report_code
        string title
        number reporting_year
        string company
        number scope_1_emissions
        number scope_2_emissions
        number scope_3_emissions
        string status
    }

    CarbonEmission {
        string emission_code
        string company
        string source_type
        string source_name
        number emission_amount
        string unit
        date measurement_date
        string facility
    }

    ESGDisclosure {
        string disclosure_code
        string title
        string disclosure_type
        string reporting_period
        string company
        string sustainability_report_id
        string status
        datetime publication_date
    }

    WasteManagement {
        string record_code
        string company
        string waste_type
        number waste_amount
        string unit
        string disposal_method
        string disposal_vendor
        date disposal_date
    }

    ESGMetric {
        string metric_code
        string metric_name
        string category
        string unit
        number target_value
        string description
        boolean is_mandatory
        string regulation_reference
    }

    SustainabilityReport ||--o{ ESGDisclosure : "sustainability_report_id"
    SustainabilityReport ||--o{ CarbonEmission : "company"
    SustainabilityReport ||--o{ WasteManagement : "company"
    ESGMetric ||--o{ CarbonEmission : "측정 기준"
```
