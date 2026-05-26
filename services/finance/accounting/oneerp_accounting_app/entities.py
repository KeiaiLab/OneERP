"""Accounting 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

49개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 7개 엔티티(accounts, cost_centers, journal_entries,
accounts_receivable, accounts_payable, general_ledger_entries, etax_invoices)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta
from oneerp_core.events.schemas import EventType

from .models.accounting_dimension import (
    AccountingDimension,
    AccountingDimensionCreate,
    AccountingDimensionUpdate,
)
from .models.accounting_dimension_value import (
    AccountingDimensionValue,
    AccountingDimensionValueCreate,
    AccountingDimensionValueUpdate,
)
from .models.accounting_period import (
    AccountingPeriod,
    AccountingPeriodCreate,
    AccountingPeriodUpdate,
)
from .models.activity_based_costing_rule import (
    ActivityBasedCostingRule,
    ActivityBasedCostingRuleCreate,
    ActivityBasedCostingRuleUpdate,
)
from .models.bank_account import (
    BankAccount,
    BankAccountCreate,
    BankAccountUpdate,
)
from .models.bank_reconciliation import (
    BankReconciliation,
    BankReconciliationCreate,
    BankReconciliationUpdate,
)
from .models.bank_statement_import import (
    BankStatementImport,
    BankStatementImportCreate,
    BankStatementImportUpdate,
)
from .models.bank_transaction import (
    BankTransaction,
    BankTransactionCreate,
    BankTransactionUpdate,
)
from .models.budget_transfer import (
    BudgetTransfer,
    BudgetTransferCreate,
    BudgetTransferUpdate,
)
from .models.budget_version import (
    BudgetVersion,
    BudgetVersionCreate,
    BudgetVersionUpdate,
)
from .models.cash_flow_forecast import (
    CashFlowForecast,
    CashFlowForecastCreate,
    CashFlowForecastUpdate,
)
from .models.consolidation_entry import (
    ConsolidationEntry,
    ConsolidationEntryCreate,
    ConsolidationEntryUpdate,
)
from .models.consolidation_group import (
    ConsolidationGroup,
    ConsolidationGroupCreate,
    ConsolidationGroupUpdate,
)
from .models.currency_exchange import (
    CurrencyExchange,
    CurrencyExchangeCreate,
    CurrencyExchangeUpdate,
)
from .models.deferred_expense_entry import (
    DeferredExpenseEntry,
    DeferredExpenseEntryCreate,
    DeferredExpenseEntryUpdate,
)
from .models.deferred_revenue_entry import (
    DeferredRevenueEntry,
    DeferredRevenueEntryCreate,
    DeferredRevenueEntryUpdate,
)
from .models.dunning import Dunning, DunningCreate, DunningUpdate
from .models.elimination_entry import (
    EliminationEntry,
    EliminationEntryCreate,
    EliminationEntryUpdate,
)
from .models.exchange_rate_revaluation import (
    ExchangeRateRevaluation,
    ExchangeRateRevaluationCreate,
    ExchangeRateRevaluationUpdate,
)
from .models.financial_ratio_report import (
    FinancialRatioReport,
    FinancialRatioReportCreate,
    FinancialRatioReportUpdate,
)
from .models.fiscal_year import FiscalYear, FiscalYearCreate, FiscalYearUpdate
from .models.fund_transfer import (
    FundTransfer,
    FundTransferCreate,
    FundTransferUpdate,
)
from .models.hedging_instrument import (
    HedgingInstrument,
    HedgingInstrumentCreate,
    HedgingInstrumentUpdate,
)
from .models.hedging_relationship import (
    HedgingRelationship,
    HedgingRelationshipCreate,
    HedgingRelationshipUpdate,
)
from .models.intercompany_billing import (
    IntercompanyBilling,
    IntercompanyBillingCreate,
    IntercompanyBillingUpdate,
)
from .models.intercompany_transaction import (
    IntercompanyTransaction,
    IntercompanyTransactionCreate,
    IntercompanyTransactionUpdate,
)
from .models.kifrs_mapping import KIFRSMapping, KIFRSMappingCreate, KIFRSMappingUpdate
from .models.lease_contract import (
    LeaseContract,
    LeaseContractCreate,
    LeaseContractUpdate,
)
from .models.lease_payment_schedule import (
    LeasePaymentSchedule,
    LeasePaymentScheduleCreate,
    LeasePaymentScheduleUpdate,
)
from .models.letter_of_credit import (
    LetterOfCredit,
    LetterOfCreditCreate,
    LetterOfCreditUpdate,
)
from .models.loan_application import (
    LoanApplication,
    LoanApplicationCreate,
    LoanApplicationUpdate,
)
from .models.loan_repayment_schedule import (
    LoanRepaymentSchedule,
    LoanRepaymentScheduleCreate,
    LoanRepaymentScheduleUpdate,
)
from .models.multi_currency_revaluation import (
    MultiCurrencyRevaluation,
    MultiCurrencyRevaluationCreate,
    MultiCurrencyRevaluationUpdate,
)
from .models.payment_entry import PaymentEntry, PaymentEntryCreate, PaymentEntryUpdate
from .models.payment_order import (
    PaymentOrder,
    PaymentOrderCreate,
    PaymentOrderUpdate,
)
from .models.payment_reconciliation import (
    PaymentReconciliation,
    PaymentReconciliationCreate,
    PaymentReconciliationUpdate,
)
from .models.payment_terms_template import (
    PaymentTermsTemplate,
    PaymentTermsTemplateCreate,
    PaymentTermsTemplateUpdate,
)
from .models.period_closing_voucher import (
    PeriodClosingVoucher,
    PeriodClosingVoucherCreate,
    PeriodClosingVoucherUpdate,
)
from .models.profit_center import (
    ProfitCenter,
    ProfitCenterCreate,
    ProfitCenterUpdate,
)
from .models.revenue_recognition_entry import (
    RevenueRecognitionEntry,
    RevenueRecognitionEntryCreate,
    RevenueRecognitionEntryUpdate,
)
from .models.revenue_recognition_rule import (
    RevenueRecognitionRule,
    RevenueRecognitionRuleCreate,
    RevenueRecognitionRuleUpdate,
)
from .models.segment_report import (
    SegmentReport,
    SegmentReportCreate,
    SegmentReportUpdate,
)
from .models.severance_reserve import (
    SeveranceReserve,
    SeveranceReserveCreate,
    SeveranceReserveUpdate,
)
from .models.tax_calendar import (
    TaxCalendar,
    TaxCalendarCreate,
    TaxCalendarUpdate,
)
from .models.tax_rule import TaxRule, TaxRuleCreate, TaxRuleUpdate
from .models.terms_and_conditions import (
    TermsAndConditions,
    TermsAndConditionsCreate,
    TermsAndConditionsUpdate,
)
from .models.vat_return import VATReturn, VATReturnCreate, VATReturnUpdate

# --- 마스터 데이터 (submit/cancel 없음) ---

ACCOUNTING_PERIOD = EntityMeta(
    collection="accounting_periods",
    prefix="APD",
    api_path="/api/v1/accounting-periods",
    tag="회계기간",
    resource="accounting_period",
    model=AccountingPeriod,
    create_schema=AccountingPeriodCreate,
    update_schema=AccountingPeriodUpdate,
    archetype="master",
    not_found_message="회계기간을 찾을 수 없습니다",
)

FISCAL_YEAR = EntityMeta(
    collection="fiscal_years",
    prefix="FY",
    api_path="/api/v1/fiscal-years",
    tag="회계연도",
    resource="fiscal_year",
    model=FiscalYear,
    create_schema=FiscalYearCreate,
    update_schema=FiscalYearUpdate,
    archetype="master",
    not_found_message="회계연도를 찾을 수 없습니다",
)

CURRENCY_EXCHANGE = EntityMeta(
    collection="currency_exchanges",
    prefix="CXR",
    api_path="/api/v1/currency-exchanges",
    tag="환율",
    resource="currency_exchange",
    model=CurrencyExchange,
    create_schema=CurrencyExchangeCreate,
    update_schema=CurrencyExchangeUpdate,
    archetype="master",
    not_found_message="환율을 찾을 수 없습니다",
)

KIFRS_MAPPING = EntityMeta(
    collection="kifrs_mappings",
    prefix="KIFRS",
    api_path="/api/v1/kifrs-mappings",
    tag="K-IFRS 매핑",
    resource="kifrs_mapping",
    model=KIFRSMapping,
    create_schema=KIFRSMappingCreate,
    update_schema=KIFRSMappingUpdate,
    archetype="master",
    not_found_message="K-IFRS 매핑을 찾을 수 없습니다",
)

TAX_RULE = EntityMeta(
    collection="tax_rules",
    prefix="TXR",
    api_path="/api/v1/tax-rules",
    tag="세금규칙",
    resource="tax_rule",
    model=TaxRule,
    create_schema=TaxRuleCreate,
    update_schema=TaxRuleUpdate,
    archetype="master",
    not_found_message="세금규칙을 찾을 수 없습니다",
)

CONSOLIDATION_GROUP = EntityMeta(
    collection="consolidation_groups",
    prefix="CGRP",
    api_path="/api/v1/consolidation-groups",
    tag="연결 대상 그룹",
    resource="consolidation_group",
    model=ConsolidationGroup,
    create_schema=ConsolidationGroupCreate,
    update_schema=ConsolidationGroupUpdate,
    archetype="master",
    not_found_message="연결 대상 그룹을 찾을 수 없습니다",
)

BANK_ACCOUNT = EntityMeta(
    collection="bank_accounts",
    prefix="BACC",
    api_path="/api/v1/bank-accounts",
    tag="은행계좌",
    resource="bank_account",
    model=BankAccount,
    create_schema=BankAccountCreate,
    update_schema=BankAccountUpdate,
    archetype="master",
    not_found_message="은행계좌를 찾을 수 없습니다",
)

PROFIT_CENTER = EntityMeta(
    collection="profit_centers",
    prefix="PC",
    api_path="/api/v1/profit-centers",
    tag="수익센터",
    resource="profit_center",
    model=ProfitCenter,
    create_schema=ProfitCenterCreate,
    update_schema=ProfitCenterUpdate,
    archetype="master",
    not_found_message="수익센터를 찾을 수 없습니다",
)

ACCOUNTING_DIMENSION = EntityMeta(
    collection="accounting_dimensions",
    prefix="ADIM",
    api_path="/api/v1/accounting-dimensions",
    tag="회계 차원",
    resource="accounting_dimension",
    model=AccountingDimension,
    create_schema=AccountingDimensionCreate,
    update_schema=AccountingDimensionUpdate,
    archetype="master",
    not_found_message="회계 차원을 찾을 수 없습니다",
)

ACCOUNTING_DIMENSION_VALUE = EntityMeta(
    collection="accounting_dimension_values",
    prefix="ADIMV",
    api_path="/api/v1/accounting-dimension-values",
    tag="회계 차원 값",
    resource="accounting_dimension_value",
    model=AccountingDimensionValue,
    create_schema=AccountingDimensionValueCreate,
    update_schema=AccountingDimensionValueUpdate,
    archetype="master",
    not_found_message="회계 차원 값을 찾을 수 없습니다",
)

TAX_CALENDAR = EntityMeta(
    collection="tax_calendars",
    prefix="TCAL",
    api_path="/api/v1/tax-calendars",
    tag="세금 일정",
    resource="tax_calendar",
    model=TaxCalendar,
    create_schema=TaxCalendarCreate,
    update_schema=TaxCalendarUpdate,
    archetype="master",
    not_found_message="세금 일정을 찾을 수 없습니다",
)

TERMS_AND_CONDITIONS = EntityMeta(
    collection="terms_and_conditions",
    prefix="TNC",
    api_path="/api/v1/terms-and-conditions",
    tag="약관",
    resource="terms_and_conditions",
    model=TermsAndConditions,
    create_schema=TermsAndConditionsCreate,
    update_schema=TermsAndConditionsUpdate,
    archetype="master",
    not_found_message="약관을 찾을 수 없습니다",
)

PAYMENT_TERMS_TEMPLATE = EntityMeta(
    collection="payment_terms_templates",
    prefix="PTT",
    api_path="/api/v1/payment-terms-templates",
    tag="결제 조건 템플릿",
    resource="payment_terms_template",
    model=PaymentTermsTemplate,
    create_schema=PaymentTermsTemplateCreate,
    update_schema=PaymentTermsTemplateUpdate,
    archetype="master",
    not_found_message="결제 조건 템플릿을 찾을 수 없습니다",
)

REVENUE_RECOGNITION_RULE = EntityMeta(
    collection="revenue_recognition_rules",
    prefix="RRR",
    api_path="/api/v1/revenue-recognition-rules",
    tag="수익 인식 규칙",
    resource="revenue_recognition_rule",
    model=RevenueRecognitionRule,
    create_schema=RevenueRecognitionRuleCreate,
    update_schema=RevenueRecognitionRuleUpdate,
    archetype="master",
    not_found_message="수익 인식 규칙을 찾을 수 없습니다",
)

ACTIVITY_BASED_COSTING_RULE = EntityMeta(
    collection="activity_based_costing_rules",
    prefix="ABC",
    api_path="/api/v1/activity-based-costing-rules",
    tag="활동기준원가 규칙",
    resource="activity_based_costing_rule",
    model=ActivityBasedCostingRule,
    create_schema=ActivityBasedCostingRuleCreate,
    update_schema=ActivityBasedCostingRuleUpdate,
    archetype="master",
    not_found_message="활동기준원가 규칙을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 (submit/cancel 포함) ---

BANK_RECONCILIATION = EntityMeta(
    collection="bank_reconciliations",
    prefix="BR",
    api_path="/api/v1/bank-reconciliations",
    tag="은행대사",
    resource="bank_reconciliation",
    model=BankReconciliation,
    create_schema=BankReconciliationCreate,
    update_schema=BankReconciliationUpdate,
    archetype="transaction",
    not_found_message="은행대사를 찾을 수 없습니다",
)

DUNNING = EntityMeta(
    collection="dunnings",
    prefix="DUN",
    api_path="/api/v1/dunnings",
    tag="독촉장",
    resource="dunning",
    model=Dunning,
    create_schema=DunningCreate,
    update_schema=DunningUpdate,
    archetype="transaction",
    not_found_message="독촉장을 찾을 수 없습니다",
)

PAYMENT_RECONCILIATION = EntityMeta(
    collection="payment_reconciliations",
    prefix="PREC",
    api_path="/api/v1/payment-reconciliations",
    tag="수금대사",
    resource="payment_reconciliation",
    model=PaymentReconciliation,
    create_schema=PaymentReconciliationCreate,
    update_schema=PaymentReconciliationUpdate,
    archetype="transaction",
    not_found_message="수금대사를 찾을 수 없습니다",
)

PERIOD_CLOSING_VOUCHER = EntityMeta(
    collection="period_closing_vouchers",
    prefix="PCV",
    api_path="/api/v1/period-closing-vouchers",
    tag="기간마감전표",
    resource="period_closing_voucher",
    model=PeriodClosingVoucher,
    create_schema=PeriodClosingVoucherCreate,
    update_schema=PeriodClosingVoucherUpdate,
    archetype="transaction",
    not_found_message="기간마감전표를 찾을 수 없습니다",
)

VAT_RETURN = EntityMeta(
    collection="vat_returns",
    prefix="VAT",
    api_path="/api/v1/vat-returns",
    tag="부가세 신고",
    resource="vat_return",
    model=VATReturn,
    create_schema=VATReturnCreate,
    update_schema=VATReturnUpdate,
    archetype="transaction",
    not_found_message="부가세 신고를 찾을 수 없습니다",
)

CONSOLIDATION_ENTRY = EntityMeta(
    collection="consolidation_entries",
    prefix="CENT",
    api_path="/api/v1/consolidation-entries",
    tag="연결회계 분개",
    resource="consolidation_entry",
    model=ConsolidationEntry,
    create_schema=ConsolidationEntryCreate,
    update_schema=ConsolidationEntryUpdate,
    archetype="transaction",
    not_found_message="연결회계 분개를 찾을 수 없습니다",
)

INTERCOMPANY_TRANSACTION = EntityMeta(
    collection="intercompany_transactions",
    prefix="ICT",
    api_path="/api/v1/intercompany-transactions",
    tag="내부거래",
    resource="intercompany_transaction",
    model=IntercompanyTransaction,
    create_schema=IntercompanyTransactionCreate,
    update_schema=IntercompanyTransactionUpdate,
    archetype="transaction",
    not_found_message="내부거래를 찾을 수 없습니다",
)

ELIMINATION_ENTRY = EntityMeta(
    collection="elimination_entries",
    prefix="ELIM",
    api_path="/api/v1/elimination-entries",
    tag="내부거래 제거 분개",
    resource="elimination_entry",
    model=EliminationEntry,
    create_schema=EliminationEntryCreate,
    update_schema=EliminationEntryUpdate,
    archetype="transaction",
    not_found_message="내부거래 제거 분개를 찾을 수 없습니다",
)

CASH_FLOW_FORECAST = EntityMeta(
    collection="cash_flow_forecasts",
    prefix="CFF",
    api_path="/api/v1/cash-flow-forecasts",
    tag="자금 흐름 예측",
    resource="cash_flow_forecast",
    model=CashFlowForecast,
    create_schema=CashFlowForecastCreate,
    update_schema=CashFlowForecastUpdate,
    archetype="transaction",
    not_found_message="자금 흐름 예측을 찾을 수 없습니다",
)

FUND_TRANSFER = EntityMeta(
    collection="fund_transfers",
    prefix="FTR",
    api_path="/api/v1/fund-transfers",
    tag="자금 이체",
    resource="fund_transfer",
    model=FundTransfer,
    create_schema=FundTransferCreate,
    update_schema=FundTransferUpdate,
    archetype="transaction",
    not_found_message="자금 이체를 찾을 수 없습니다",
)

LOAN_APPLICATION = EntityMeta(
    collection="loan_applications",
    prefix="LOAN",
    api_path="/api/v1/loan-applications",
    tag="대출 신청",
    resource="loan_application",
    model=LoanApplication,
    create_schema=LoanApplicationCreate,
    update_schema=LoanApplicationUpdate,
    archetype="transaction",
    not_found_message="대출 신청을 찾을 수 없습니다",
)

LOAN_REPAYMENT_SCHEDULE = EntityMeta(
    collection="loan_repayment_schedules",
    prefix="LRS",
    api_path="/api/v1/loan-repayment-schedules",
    tag="대출 상환 일정",
    resource="loan_repayment_schedule",
    model=LoanRepaymentSchedule,
    create_schema=LoanRepaymentScheduleCreate,
    update_schema=LoanRepaymentScheduleUpdate,
    archetype="transaction",
    not_found_message="대출 상환 일정을 찾을 수 없습니다",
)

SEVERANCE_RESERVE = EntityMeta(
    collection="severance_reserves",
    prefix="SVR",
    api_path="/api/v1/severance-reserves",
    tag="퇴직급여 충당금",
    resource="severance_reserve",
    model=SeveranceReserve,
    create_schema=SeveranceReserveCreate,
    update_schema=SeveranceReserveUpdate,
    archetype="transaction",
    not_found_message="퇴직급여 충당금을 찾을 수 없습니다",
)

BANK_TRANSACTION = EntityMeta(
    collection="bank_transactions",
    prefix="BTXN",
    api_path="/api/v1/bank-transactions",
    tag="은행 거래",
    resource="bank_transaction",
    model=BankTransaction,
    create_schema=BankTransactionCreate,
    update_schema=BankTransactionUpdate,
    archetype="transaction",
    not_found_message="은행 거래를 찾을 수 없습니다",
)

BANK_STATEMENT_IMPORT = EntityMeta(
    collection="bank_statement_imports",
    prefix="BSI",
    api_path="/api/v1/bank-statement-imports",
    tag="은행 거래 명세 가져오기",
    resource="bank_statement_import",
    model=BankStatementImport,
    create_schema=BankStatementImportCreate,
    update_schema=BankStatementImportUpdate,
    archetype="transaction",
    not_found_message="은행 거래 명세 가져오기를 찾을 수 없습니다",
)

PAYMENT_ORDER = EntityMeta(
    collection="payment_orders",
    prefix="PORD",
    api_path="/api/v1/payment-orders",
    tag="지급 지시",
    resource="payment_order",
    model=PaymentOrder,
    create_schema=PaymentOrderCreate,
    update_schema=PaymentOrderUpdate,
    archetype="transaction",
    not_found_message="지급 지시를 찾을 수 없습니다",
)

PAYMENT_ENTRY = EntityMeta(
    collection="payment_entries",
    prefix="PE",
    api_path="/api/v1/payment-entries",
    tag="결제 입력",
    resource="payment_entry",
    model=PaymentEntry,
    create_schema=PaymentEntryCreate,
    update_schema=PaymentEntryUpdate,
    archetype="transaction",
    submit_event_type=EventType.PAYMENT_ENTRY_SUBMITTED,
    not_found_message="결제 입력을 찾을 수 없습니다",
)

INTERCOMPANY_BILLING = EntityMeta(
    collection="intercompany_billings",
    prefix="ICB",
    api_path="/api/v1/intercompany-billings",
    tag="내부 대금 청구",
    resource="intercompany_billing",
    model=IntercompanyBilling,
    create_schema=IntercompanyBillingCreate,
    update_schema=IntercompanyBillingUpdate,
    archetype="transaction",
    not_found_message="내부 대금 청구를 찾을 수 없습니다",
)

EXCHANGE_RATE_REVALUATION = EntityMeta(
    collection="exchange_rate_revaluations",
    prefix="ERR",
    api_path="/api/v1/exchange-rate-revaluations",
    tag="환율 재평가",
    resource="exchange_rate_revaluation",
    model=ExchangeRateRevaluation,
    create_schema=ExchangeRateRevaluationCreate,
    update_schema=ExchangeRateRevaluationUpdate,
    archetype="transaction",
    not_found_message="환율 재평가를 찾을 수 없습니다",
)

DEFERRED_REVENUE_ENTRY = EntityMeta(
    collection="deferred_revenue_entries",
    prefix="DRE",
    api_path="/api/v1/deferred-revenue-entries",
    tag="이연 수익 분개",
    resource="deferred_revenue_entry",
    model=DeferredRevenueEntry,
    create_schema=DeferredRevenueEntryCreate,
    update_schema=DeferredRevenueEntryUpdate,
    archetype="transaction",
    not_found_message="이연 수익 분개를 찾을 수 없습니다",
)

DEFERRED_EXPENSE_ENTRY = EntityMeta(
    collection="deferred_expense_entries",
    prefix="DEE",
    api_path="/api/v1/deferred-expense-entries",
    tag="이연 비용 분개",
    resource="deferred_expense_entry",
    model=DeferredExpenseEntry,
    create_schema=DeferredExpenseEntryCreate,
    update_schema=DeferredExpenseEntryUpdate,
    archetype="transaction",
    not_found_message="이연 비용 분개를 찾을 수 없습니다",
)

REVENUE_RECOGNITION_ENTRY = EntityMeta(
    collection="revenue_recognition_entries",
    prefix="RREC",
    api_path="/api/v1/revenue-recognition-entries",
    tag="수익 인식 분개",
    resource="revenue_recognition_entry",
    model=RevenueRecognitionEntry,
    create_schema=RevenueRecognitionEntryCreate,
    update_schema=RevenueRecognitionEntryUpdate,
    archetype="transaction",
    not_found_message="수익 인식 분개를 찾을 수 없습니다",
)

LEASE_CONTRACT = EntityMeta(
    collection="lease_contracts",
    prefix="LSC",
    api_path="/api/v1/lease-contracts",
    tag="리스 계약",
    resource="lease_contract",
    model=LeaseContract,
    create_schema=LeaseContractCreate,
    update_schema=LeaseContractUpdate,
    archetype="transaction",
    not_found_message="리스 계약을 찾을 수 없습니다",
)

BUDGET_VERSION = EntityMeta(
    collection="budget_versions",
    prefix="BVER",
    api_path="/api/v1/budget-versions",
    tag="예산 버전",
    resource="budget_version",
    model=BudgetVersion,
    create_schema=BudgetVersionCreate,
    update_schema=BudgetVersionUpdate,
    archetype="transaction",
    not_found_message="예산 버전을 찾을 수 없습니다",
)

BUDGET_TRANSFER = EntityMeta(
    collection="budget_transfers",
    prefix="BTRF",
    api_path="/api/v1/budget-transfers",
    tag="예산 이전",
    resource="budget_transfer",
    model=BudgetTransfer,
    create_schema=BudgetTransferCreate,
    update_schema=BudgetTransferUpdate,
    archetype="transaction",
    not_found_message="예산 이전을 찾을 수 없습니다",
)

LETTER_OF_CREDIT = EntityMeta(
    collection="letters_of_credit",
    prefix="LC",
    api_path="/api/v1/letters-of-credit",
    tag="신용장",
    resource="letter_of_credit",
    model=LetterOfCredit,
    create_schema=LetterOfCreditCreate,
    update_schema=LetterOfCreditUpdate,
    archetype="transaction",
    not_found_message="신용장을 찾을 수 없습니다",
)

FINANCIAL_RATIO_REPORT = EntityMeta(
    collection="financial_ratio_reports",
    prefix="FRR",
    api_path="/api/v1/financial-ratio-reports",
    tag="재무비율 보고서",
    resource="financial_ratio_report",
    model=FinancialRatioReport,
    create_schema=FinancialRatioReportCreate,
    update_schema=FinancialRatioReportUpdate,
    archetype="transaction",
    not_found_message="재무비율 보고서를 찾을 수 없습니다",
)

SEGMENT_REPORT = EntityMeta(
    collection="segment_reports",
    prefix="SGRP",
    api_path="/api/v1/segment-reports",
    tag="부문별 보고서",
    resource="segment_report",
    model=SegmentReport,
    create_schema=SegmentReportCreate,
    update_schema=SegmentReportUpdate,
    archetype="transaction",
    not_found_message="부문별 보고서를 찾을 수 없습니다",
)

MULTI_CURRENCY_REVALUATION = EntityMeta(
    collection="multi_currency_revaluations",
    prefix="MCR",
    api_path="/api/v1/multi-currency-revaluations",
    tag="다중통화 재평가",
    resource="multi_currency_revaluation",
    model=MultiCurrencyRevaluation,
    create_schema=MultiCurrencyRevaluationCreate,
    update_schema=MultiCurrencyRevaluationUpdate,
    archetype="transaction",
    not_found_message="다중통화 재평가를 찾을 수 없습니다",
)

LEASE_PAYMENT_SCHEDULE = EntityMeta(
    collection="lease_payment_schedules",
    prefix="LPS",
    api_path="/api/v1/lease-payment-schedules",
    tag="리스 지급 일정",
    resource="lease_payment_schedule",
    model=LeasePaymentSchedule,
    create_schema=LeasePaymentScheduleCreate,
    update_schema=LeasePaymentScheduleUpdate,
    archetype="transaction",
    not_found_message="리스 지급 일정을 찾을 수 없습니다",
)

HEDGING_INSTRUMENT = EntityMeta(
    collection="hedging_instruments",
    prefix="HINST",
    api_path="/api/v1/hedging-instruments",
    tag="헤지 수단",
    resource="hedging_instrument",
    model=HedgingInstrument,
    create_schema=HedgingInstrumentCreate,
    update_schema=HedgingInstrumentUpdate,
    archetype="transaction",
    not_found_message="헤지 수단을 찾을 수 없습니다",
)

HEDGING_RELATIONSHIP = EntityMeta(
    collection="hedging_relationships",
    prefix="HREL",
    api_path="/api/v1/hedging-relationships",
    tag="헤지 관계",
    resource="hedging_relationship",
    model=HedgingRelationship,
    create_schema=HedgingRelationshipCreate,
    update_schema=HedgingRelationshipUpdate,
    archetype="transaction",
    not_found_message="헤지 관계를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
# 참고: AccountsPayable, AccountsReceivable은 커스텀 라우트(routes/)에서 관리
ENTITY_METAS = [
    # 마스터
    FISCAL_YEAR,
    CURRENCY_EXCHANGE,
    KIFRS_MAPPING,
    TAX_RULE,
    CONSOLIDATION_GROUP,
    BANK_ACCOUNT,
    PROFIT_CENTER,
    ACCOUNTING_DIMENSION,
    ACCOUNTING_DIMENSION_VALUE,
    TAX_CALENDAR,
    TERMS_AND_CONDITIONS,
    PAYMENT_TERMS_TEMPLATE,
    REVENUE_RECOGNITION_RULE,
    ACTIVITY_BASED_COSTING_RULE,
    # 트랜잭션
    BANK_RECONCILIATION,
    DUNNING,
    PAYMENT_RECONCILIATION,
    PERIOD_CLOSING_VOUCHER,
    CONSOLIDATION_ENTRY,
    INTERCOMPANY_TRANSACTION,
    ELIMINATION_ENTRY,
    CASH_FLOW_FORECAST,
    FUND_TRANSFER,
    LOAN_APPLICATION,
    LOAN_REPAYMENT_SCHEDULE,
    SEVERANCE_RESERVE,
    BANK_TRANSACTION,
    BANK_STATEMENT_IMPORT,
    PAYMENT_ORDER,
    PAYMENT_ENTRY,
    INTERCOMPANY_BILLING,
    EXCHANGE_RATE_REVALUATION,
    DEFERRED_REVENUE_ENTRY,
    DEFERRED_EXPENSE_ENTRY,
    REVENUE_RECOGNITION_ENTRY,
    LEASE_CONTRACT,
    BUDGET_VERSION,
    BUDGET_TRANSFER,
    LETTER_OF_CREDIT,
    FINANCIAL_RATIO_REPORT,
    SEGMENT_REPORT,
    MULTI_CURRENCY_REVALUATION,
    LEASE_PAYMENT_SCHEDULE,
    HEDGING_INSTRUMENT,
    HEDGING_RELATIONSHIP,
]
