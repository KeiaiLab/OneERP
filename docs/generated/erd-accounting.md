# ACCOUNTING 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: ACCOUNTING 서비스 ERD
---
erDiagram
    Account {
        string account_name
        string account_type
        string parent_account
        boolean is_group
        string currency
    }
    AccountingPeriod {
        string period_name
        date start_date
        date end_date
        string company
        string status
    }
    AccountsPayable {
        string supplier
        number outstanding_amount
        date due_date
        string aging_bucket
        string invoice_id
    }
    AccountsReceivable {
        string customer
        number outstanding_amount
        date due_date
        string aging_bucket
        string invoice_id
    }
    BankReconciliation {
        string bank_account
        date from_date
        date to_date
        number bank_balance
        number system_balance
        number difference
    }
    Budget {
        string fiscal_year
        string cost_center
        number budget_amount
        number actual_amount
        string items
    }
    CostCenter {
        string cost_center_name
        string parent_cost_center
        boolean is_group
        string company
    }
    CurrencyExchange {
        string from_currency
        string to_currency
        number exchange_rate
        date exchange_date
        boolean for_buying
        boolean for_selling
    }
    Dunning {
        string customer
        number outstanding_amount
        number dunning_level
        date dunning_date
        number dunning_fee
    }
    ETaxInvoice {
        string invoice_ref
        date issue_date
        string supplier_or_customer
        number supply_amount
        number tax_amount
        string nts_confirmation_no
        string transmission_status
    }
    FiscalYear {
        string year_name
        date start_date
        date end_date
        string company
        boolean is_closed
    }
    GeneralLedgerEntry {
        string account
        number debit
        number credit
        date posting_date
        string voucher_type
        string voucher_id
        string party_type
        string party
        string cost_center
        string remarks
    }
    JournalEntry {
        date posting_date
        string voucher_type
        number total_debit
        number total_credit
        string items
        string remark
    }
    KIFRSMapping {
        string k_ifrs_account
        string local_account
        string mapping_type
        date effective_date
        boolean is_active
    }
    PaymentReconciliation {
        string party_type
        string party
        string receivable_payable_account
        date from_date
        date to_date
    }
    PeriodClosingVoucher {
        string fiscal_year
        string closing_account
        date posting_date
        string remarks
    }
    TaxRule {
        string tax_type
        number tax_rate
        string conditions
        number priority
        boolean is_active
    }
    VATReturn {
        string period
        number tax_amount
        date filing_date
        string status
        number output_tax
        number input_tax
        number net_tax
    }
```
