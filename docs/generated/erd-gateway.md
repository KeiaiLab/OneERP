# GATEWAY 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: GATEWAY 서비스 ERD
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
    ActivityType {
        string activity_type
        number costing_rate
        number billing_rate
    }
    ApprovalAction {
        string approval_request
        string action_type
        string actor
        string comment
        date action_date
    }
    ApprovalLine {
        string template
        number sequence
        string approver_role
        string approver
        string condition
    }
    ApprovalRequest {
        string document_type
        string document_id
        string requester
        string status
        number current_step
    }
    ApprovalTemplate {
        string template_name
        string document_type
        string steps
    }
    Asset {
        string asset_name
        string asset_category
        date purchase_date
        number gross_amount
        string depreciation_method
        number useful_life_years
        number salvage_value
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
    AssetMovement {
        string asset
        string asset_name
        string from_location
        string to_location
        date movement_date
        string purpose
    }
    BusinessRegistration {
        string registration_number
        string company_name
        string representative
        string business_type
        date registration_date
    }
    Campaign {
        string campaign_name
        date start_date
        date end_date
        string status
        string description
    }
    Company {
        string company_name
        string abbr
        string default_currency
        string country
        string chart_of_accounts
        string fiscal_year_start
        string domain
    }
    Currency {
        string currency_code
        string currency_name
        string symbol
        string fraction
        number fraction_units
        boolean is_enabled
    }
    DelegationRule {
        string delegator
        string delegate
        date from_date
        date to_date
        string document_type
        boolean is_active
    }
    DepreciationEntry {
        string asset_ref
        date posting_date
        number depreciation_amount
        number accumulated_depreciation
        number remaining_value
    }
    InspectionResult {
        string inspection_id
        string parameter
        string result
        string status
        string remarks
    }
    Issue {
        string subject
        string description
        string customer_id
        string priority
        string status
        string assigned_to
        string resolution
    }
    IssueType {
        string issue_type_name
        string description
        string priority
    }
    KnowledgeBase {
        string title
        string content
        string category
        boolean is_published
    }
    Lead {
        string lead_name
        string company_name
        string email
        string phone
        string source
        string status
    }
    Milestone {
        string milestone_name
        string project
        date due_date
        string status
        string description
    }
    NamingSeries {
        string prefix
        number current_value
        string description
    }
    NonConformance {
        string title
        string description
        string severity
        string item_code
        string inspection_id
        string corrective_action
    }
    NotificationTemplate {
        string name
        string document_type
        string event
        string channel
        string subject_template
        string message_template
        string recipients_expression
    }
    NotificationRule {
        string rule_name
        string event
        string document_type
        string condition
        string recipients
        string template
        boolean is_active
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
    Project {
        string project_name
        string status
        date expected_start_date
        date expected_end_date
        date actual_start_date
        date actual_end_date
        number percent_complete
        string company
        string cost_center
    }
    QualityGoal {
        string goal_name
        number target_value
        number current_value
        string unit
        string period
        string status
    }
    QualityInspection {
        string reference_type
        string reference_no
        string inspection_type
        string item_code
        string readings
        string result
    }
    QualityInspectionTemplate {
        string template_name
        string inspection_type
        string parameters
    }
    Role {
        string role_name
        string description
        boolean is_custom
    }
    RolePermission {
        string role
        string doctype
        boolean read
        boolean write
        boolean create
        boolean delete
        boolean submit
        boolean cancel
    }
    SalesPipeline {
        string stage
        number deal_count
        number total_value
        string period
    }
    ServiceLevelAgreement {
        string sla_name
        string entity_type
        number response_time
        number resolution_time
        string priority
        boolean is_active
    }
    SLAFulfillment {
        string sla
        number total_issues
        number fulfilled
        number breached
        number fulfillment_rate
    }
    SystemSettings {
        string setting_key
        string setting_value
        string description
    }
    Task {
        string subject
        string project_ref
        string assigned_to
        string priority
        string status
        number expected_time
        number actual_time
    }
    Tenant {
        string tenant_name
        string domain
        boolean is_active
        string plan
    }
    Timesheet {
        string employee_id
        string employee_name
        date start_date
        date end_date
        number total_hours
        string time_logs
    }
    User {
        string username
        string email
        string full_name
        boolean is_active
        string role
    }
    WorkflowRule {
        string document_type
        string states
        string transitions
    }
    WorkflowDefinition {
        string workflow_name
        string document_type
        string states
        string transitions
        boolean is_active
    }
```
