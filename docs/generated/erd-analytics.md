# ANALYTICS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: ANALYTICS 서비스 ERD
---
erDiagram
    CarbonEmission {
        string scope
        string source
        number emission_amount
        string unit
        string period
    }
    ComplianceChecklist {
        string status
        string checklist_name
        string regulation
        array items
        boolean is_completed
    }
    ComplianceReport {
        string status
        string report_name
        string regulation
        string period
        number findings
        boolean is_compliant
    }
    CustomReport {
        string report_name
        string report_type
        string data_source
        string query
        boolean is_public
    }
    Dashboard {
        string dashboard_name
        string description
        boolean is_public
        string owner
    }
    DashboardWidget {
        string dashboard_id
        string widget_type
        string title
        string data_source
        number position
    }
    DataSource {
        string status
        string source_name
        string source_type
        string connection_info
        boolean is_active
    }
    ESGDisclosure {
        string status
        string disclosure_title
        string framework
        string period
        string content
        boolean is_published
    }
    ESGMetric {
        string metric_name
        string category
        number value
        string unit
        string period
        number target_value
    }
    InternalControl {
        string status
        string control_name
        string control_type
        string responsible
        string frequency
        boolean is_active
    }
    KPIDefinition {
        string kpi_name
        string description
        string formula
        string unit
        number target_value
        boolean is_active
    }
    KPISnapshot {
        string kpi_id
        string period
        number actual_value
        number target_value
        number achievement_rate
    }
    RegulatorySandbox {
        string status
        string sandbox_name
        string regulation
        date start_date
        date end_date
        string description
    }
    RiskAssessment {
        string status
        string risk_name
        string category
        number likelihood
        number impact
        number risk_score
    }
    SustainabilityReport {
        string status
        string report_title
        string period
        string framework
        string content
        boolean is_published
    }
    WasteManagement {
        string waste_type
        number quantity
        string unit
        string disposal_method
        date disposal_date
    }
```
