# OneERP Accounting 서비스 (Accounting Service)

> 계정과목, 분개, 원장, 결산, 세금, 연결회계 등 재무회계 전반을 관리하는 서비스 / Manages the entire financial accounting domain including chart of accounts, journal entries, general ledger, closing, tax, and consolidation

## 도메인 개요 (Domain Overview)

Accounting 서비스는 계정과목 (Chart of Accounts) 체계 관리, 분개 (Journal Entry) 처리, 총계정원장 (General Ledger), 매출채권/매입채무 (Accounts Receivable/Payable) 관리, 은행대사 (Bank Reconciliation), 예산 관리 (Budget), 기간마감 (Period Closing), 부가세 신고 (VAT Return), 전자세금계산서 (E-Tax Invoice), 연결회계 (Consolidation), K-IFRS 매핑 등 재무회계 전 영역을 담당한다. 자금 관리 (Treasury) — 현금흐름 예측 (Cash Flow Forecast), 대출 (Loan), 리스 (Lease) — 와 헤지 회계 (Hedge Accounting)까지 포괄한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8005 |

## 엔티티 (Entities) — 54개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| AccountingPeriod | accounting_periods | 회계기간 (Accounting Period) |
| FiscalYear | fiscal_years | 회계연도 (Fiscal Year) |
| CurrencyExchange | currency_exchanges | 환율 (Currency Exchange) |
| KIFRSMapping | kifrs_mappings | K-IFRS 매핑 (K-IFRS Mapping) |
| TaxRule | tax_rules | 세금규칙 (Tax Rule) |
| ConsolidationGroup | consolidation_groups | 연결 대상 그룹 (Consolidation Group) |
| BankAccount | bank_accounts | 은행계좌 (Bank Account) |
| ProfitCenter | profit_centers | 수익센터 (Profit Center) |
| AccountingDimension | accounting_dimensions | 회계 차원 (Accounting Dimension) |
| AccountingDimensionValue | accounting_dimension_values | 회계 차원 값 (Accounting Dimension Value) |
| TaxCalendar | tax_calendars | 세금 일정 (Tax Calendar) |
| TermsAndConditions | terms_and_conditions | 약관 (Terms and Conditions) |
| PaymentTermsTemplate | payment_terms_templates | 결제 조건 템플릿 (Payment Terms Template) |
| RevenueRecognitionRule | revenue_recognition_rules | 수익 인식 규칙 (Revenue Recognition Rule) |
| ActivityBasedCostingRule | activity_based_costing_rules | 활동기준원가 규칙 (ABC Rule) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| BankReconciliation | bank_reconciliations | 은행대사 (Bank Reconciliation) |
| Budget | budgets | 예산 (Budget) |
| Dunning | dunnings | 독촉장 (Dunning) |
| ETaxInvoice | etax_invoices | 전자세금계산서 (E-Tax Invoice) |
| PaymentReconciliation | payment_reconciliations | 수금대사 (Payment Reconciliation) |
| PeriodClosingVoucher | period_closing_vouchers | 기간마감전표 (Period Closing Voucher) |
| VATReturn | vat_returns | 부가세 신고 (VAT Return) |
| ConsolidationEntry | consolidation_entries | 연결회계 분개 (Consolidation Entry) |
| IntercompanyTransaction | intercompany_transactions | 내부거래 (Intercompany Transaction) |
| EliminationEntry | elimination_entries | 내부거래 제거 분개 (Elimination Entry) |
| CashFlowForecast | cash_flow_forecasts | 자금 흐름 예측 (Cash Flow Forecast) |
| FundTransfer | fund_transfers | 자금 이체 (Fund Transfer) |
| LoanApplication | loan_applications | 대출 신청 (Loan Application) |
| LoanRepaymentSchedule | loan_repayment_schedules | 대출 상환 일정 (Loan Repayment Schedule) |
| SeveranceReserve | severance_reserves | 퇴직급여 충당금 (Severance Reserve) |
| BankTransaction | bank_transactions | 은행 거래 (Bank Transaction) |
| BankStatementImport | bank_statement_imports | 은행 거래 명세 가져오기 (Bank Statement Import) |
| PaymentOrder | payment_orders | 지급 지시 (Payment Order) |
| IntercompanyBilling | intercompany_billings | 내부 대금 청구 (Intercompany Billing) |
| ExchangeRateRevaluation | exchange_rate_revaluations | 환율 재평가 (Exchange Rate Revaluation) |
| DeferredRevenueEntry | deferred_revenue_entries | 이연 수익 분개 (Deferred Revenue Entry) |
| DeferredExpenseEntry | deferred_expense_entries | 이연 비용 분개 (Deferred Expense Entry) |
| RevenueRecognitionEntry | revenue_recognition_entries | 수익 인식 분개 (Revenue Recognition Entry) |
| LeaseContract | lease_contracts | 리스 계약 (Lease Contract) |
| BudgetVersion | budget_versions | 예산 버전 (Budget Version) |
| BudgetTransfer | budget_transfers | 예산 이전 (Budget Transfer) |
| LetterOfCredit | letters_of_credit | 신용장 (Letter of Credit) |
| FinancialRatioReport | financial_ratio_reports | 재무비율 보고서 (Financial Ratio Report) |
| SegmentReport | segment_reports | 부문별 보고서 (Segment Report) |
| MultiCurrencyRevaluation | multi_currency_revaluations | 다중통화 재평가 (Multi-Currency Revaluation) |
| LeasePaymentSchedule | lease_payment_schedules | 리스 지급 일정 (Lease Payment Schedule) |
| HedgingInstrument | hedging_instruments | 헤지 수단 (Hedging Instrument) |
| HedgingRelationship | hedging_relationships | 헤지 관계 (Hedging Relationship) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| JournalAutoService | 자동 분개 생성 | 거래 발생 시 자동 분개 (Auto Journal Entry) |
| PeriodClosingService | 기간 마감 처리 | 월/분기/연간 결산 (Period Closing) |
| BankReconciliationService | 은행대사 매칭 | 은행 거래 자동 대사 (Bank Reconciliation) |
| PaymentReconciliationService | 수금 대사 | 매출채권 수금 매칭 (Payment Reconciliation) |
| VATService | 부가세 계산/신고 | 부가가치세 관리 (VAT Management) |
| ETaxService | 전자세금계산서 발행 | 국세청 연동 (NTS E-Tax Invoice) |
| NTSApiClient | 국세청 API 호출 | 홈택스 연동 클라이언트 (HomeTax API Client) |
| ConsolidationService | 연결재무제표 작성 | 그룹사 연결회계 (Group Consolidation) |
| KIFRSService | K-IFRS 매핑 적용 | 한국채택국제회계기준 변환 (K-IFRS Conversion) |
| DunningService | 독촉장 발송 | 미수금 독촉 관리 (Dunning Management) |
| TreasuryService | 자금 관리 | 현금흐름, 대출, 이체 (Treasury Management) |
| InvoiceHandler | 송장 처리 | 매출/매입 송장 자동 처리 (Invoice Processing) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 48개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/accounts | 계정과목 관리 (Chart of Accounts) |
| CRUD | /api/v1/journal-entries | 분개 관리 (Journal Entries) |
| CRUD | /api/v1/cost-centers | 원가센터 관리 (Cost Centers) |
| CRUD | /api/v1/general-ledger-entries | 총계정원장 (General Ledger) |
| CRUD | /api/v1/accounts-receivable | 매출채권 관리 (Accounts Receivable) |
| CRUD | /api/v1/accounts-payable | 매입채무 관리 (Accounts Payable) |

## 이벤트 (Events)

### 구독 (Subscribed)
| EventType | 핸들러 (Handler) |
|-----------|-----------------|
| 회계 관련 이벤트 (Accounting Events) | events/handlers.py |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-accounting --directory services/accounting uvicorn app.main:app --port 8005
```

## 테스트 (Testing)

```bash
uv run pytest services/accounting/ -m "not integration and not e2e" -v
```
