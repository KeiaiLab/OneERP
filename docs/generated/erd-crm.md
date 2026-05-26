# CRM 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: CRM 서비스 ERD
---
erDiagram
    Activity {
        string activity_type
        date activity_date
        string party_type
        string party
        string description
        string assigned_to
    }
    Appointment {
        string title
        string customer_id
        date scheduled_date
        string location
        string agenda
        string assigned_to
    }
    CallLog {
        string caller
        string receiver
        date call_date
        number duration_minutes
        string call_type
        string summary
    }
    Campaign {
        string campaign_name
        date start_date
        date end_date
        string status
        string description
    }
    CompetitorProfile {
        string company_name
        string industry
        string website
        string strengths
        string weaknesses
        number market_share
    }
    Contract {
        string status
        string contract_title
        string counterparty
        date start_date
        date end_date
        number contract_value
        string currency
    }
    ContractRenewal {
        string status
        string contract_id
        date renewal_date
        date new_end_date
        number revised_value
        string reason
    }
    CustomerSegment {
        string segment_name
        string criteria
        number customer_count
        string description
    }
    EmailCampaign {
        string campaign_name
        string subject
        date send_date
        number recipient_count
        number open_rate
        number click_rate
    }
    EventRegistration {
        string event_name
        string participant_name
        string email
        date registration_date
        boolean is_attended
    }
    Faq {
        string question
        string answer
        string category
        number view_count
        boolean is_published
    }
    Issue {
        string subject
        string description
        string customer_id
        string priority
        string status
        string assigned_to
    }
    IssueType {
        string issue_type_name
        string description
        string priority
    }
    KnowledgeArticle {
        string article_title
        string content
        string category_id
        string author
        boolean is_published
    }
    KnowledgeBase {
        string title
        string content
        string category
        boolean is_published
    }
    KnowledgeCategory {
        string category_name
        string parent_id
        string description
        boolean is_active
    }
    Lead {
        string lead_name
        string company_name
        string email
        string phone
        string source
        string status
    }
    LeadScoring {
        string lead_id
        number score
        string scoring_criteria
        date last_updated
    }
    LoyaltyPoint {
        string customer_id
        number points_earned
        number points_redeemed
        number balance
        date expiry_date
    }
    MarketingAutomationRule {
        string rule_name
        string trigger_event
        string action
        number delay_hours
        boolean is_active
    }
    MarketingList {
        string list_name
        string description
        number member_count
        boolean is_active
    }
    Newsletter {
        string newsletter_name
        string subject
        string content
        date send_date
        number subscriber_count
    }
    Opportunity {
        string lead_ref
        string customer_id
        string opportunity_type
        number expected_amount
        number probability
        date close_date
        string status
    }
    Prospect {
        string prospect_name
        string company
        string industry
        string source
        number estimated_value
        string notes
    }
    SalesPipeline {
        string stage
        number deal_count
        number total_value
        string period
    }
    ServiceContract {
        string customer_id
        string contract_type
        date start_date
        date end_date
        number contract_value
        boolean is_active
    }
    ServiceLevelAgreement {
        string sla_name
        string entity_type
        number response_time
        number resolution_time
        string priority
        boolean is_active
    }
    ServiceOrder {
        string customer_id
        string service_type
        string description
        string priority
        date scheduled_date
        number total_cost
    }
    ServiceTechnician {
        string technician_name
        string employee_id
        string specialization
        boolean is_available
        number rating
    }
    ServiceVisit {
        string service_order_id
        date visit_date
        string technician_id
        string work_done
        number duration_hours
        string customer_feedback
    }
    SLAFulfillment {
        string sla
        number total_issues
        number fulfilled
        number breached
        number fulfillment_rate
    }
    SmsCampaign {
        string campaign_name
        string message
        date send_date
        number recipient_count
        number delivery_rate
    }
    Survey {
        string survey_name
        string description
        date start_date
        date end_date
        number response_count
        boolean is_active
    }
    SurveyResponse {
        string survey_id
        string respondent
        date response_date
        string answers
        number score
    }
    TerritoryManagement {
        string territory_name
        string manager_id
        string region
        number customer_count
        number target_revenue
    }
    WarrantyClaim {
        string customer_id
        string item_code
        date claim_date
        string issue_description
        string serial_no
        boolean is_resolved
    }
    WarrantyPeriod {
        string item_code
        number warranty_months
        date start_date
        date end_date
        string terms
    }
```
