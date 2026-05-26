from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for relative in (
    "core",
    "services/scm/buying",
    "services/hr/hr",
    "services/scm/manufacturing",
    "services/sales/selling",
    "services/collab/knowledge",
    "services/finance/accounting",
    "services/sales/crm",
    "services/assets/assets",
    "services/finance/payroll",
    "services/finance/expenses",
    "services/collab/projects",
):
    path = str(ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)


MODEL_TARGETS = [
    ("oneerp_buying_app.models.request_for_quotation", "RequestForQuotationCreate"),
    ("oneerp_buying_app.models.supplier_quotation", "SupplierQuotationCreate"),
    ("oneerp_hr_app.models.employee", "EmployeeCreate"),
    ("oneerp_hr_app.models.leave_balance", "LeaveBalanceCreate"),
    ("oneerp_hr_app.routes.attendances", "AttendanceCheckInRequest"),
    ("oneerp_manufacturing_app.models.work_order", "WorkOrderCreate"),
    ("oneerp_manufacturing_app.models.production_plan", "ProductionPlanCreate"),
    ("oneerp_manufacturing_app.models.job_card", "JobCardCreate"),
    ("oneerp_selling_app.models.quotation", "QuotationCreate"),
    ("oneerp_selling_app.models.price_list", "PriceListCreate"),
    ("oneerp_knowledge_app.models.knowledge_article", "KnowledgeArticleCreate"),
    ("oneerp_accounting_app.models.budget_transfer", "BudgetTransferCreate"),
    ("oneerp_accounting_app.models.fiscal_year", "FiscalYearCreate"),
    ("oneerp_accounting_app.models.etax_invoice", "ETaxInvoiceCreate"),
    ("oneerp_accounting_app.models.dunning", "DunningCreate"),
    ("oneerp_crm_app.models.activity", "ActivityCreate"),
    ("oneerp_crm_app.models.opportunity", "OpportunityCreate"),
    ("oneerp_assets_app.models.asset", "AssetCreate"),
    ("oneerp_assets_app.models.depreciation", "DepreciationEntryCreate"),
    ("oneerp_payroll_app.models.salary_slip", "SalarySlipCreate"),
    ("oneerp_payroll_app.models.payroll_entry", "PayrollEntryCreate"),
    ("oneerp_expenses_app.models.expense_claim", "ExpenseClaimCreate"),
    ("oneerp_projects_app.models.task", "TaskCreate"),
    ("oneerp_projects_app.models.timesheet", "TimesheetCreate"),
]


def test_runtime_request_models_build_schema_without_pydantic_user_error() -> None:
    for module_name, class_name in MODEL_TARGETS:
        model = getattr(import_module(module_name), class_name)
        schema = model.model_json_schema()
        assert schema["type"] == "object"
