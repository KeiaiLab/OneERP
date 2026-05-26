# SELLING 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: SELLING 서비스 ERD
---
erDiagram
    BlanketOrder {
        string customer
        date from_date
        date to_date
        string items
        number total
    }
    Customer {
        string customer_name
        string customer_type
        string tax_id
        string default_currency
        string territory
        string address
        string contact
    }
    CustomerGroup {
        string group_name
        string parent_group
        string default_price_list
    }
    DeliveryNote {
        string customer_id
        string customer_name
        date posting_date
        string sales_order_ref
        string items
        string transporter
    }
    PaymentEntry {
        string payment_type
        string party_type
        string party
        string party_name
        number paid_amount
        number received_amount
        string reference_no
        date reference_date
        string payment_method
        string items
    }
    POSClosingEntry {
        string pos_profile
        date period_start
        date period_end
        number opening_amount
        number closing_amount
        number total_sales
        number difference
    }
    POSPaymentMethod {
        string method_name
        string payment_type
        boolean is_active
    }
    POSProfile {
        string name
        string warehouse
        string price_list
        string write_off_account
        string payments
    }
    POSReceipt {
        string transaction_id
        string receipt_data
        date printed_at
    }
    POSTransaction {
        string customer_id
        string customer_name
        string pos_profile_ref
        date posting_date
        string items
        number total
        number grand_total
        string payments
    }
    PriceList {
        string price_list_name
        string currency
        boolean selling
        boolean buying
        boolean is_active
    }
    PricingRule {
        string rule_name
        string apply_on
        string discount_type
        number discount_value
        number priority
        boolean is_active
    }
    Quotation {
        string customer_id
        string customer_name
        date transaction_date
        date valid_till
        string items
        number total
        number grand_total
    }
    SalesAnalytics {
        string period
        string item_code
        string customer
        number total_qty
        number total_amount
    }
    SalesInvoice {
        string customer_id
        string customer_name
        date posting_date
        date due_date
        string items
        string taxes
        number grand_total
        number outstanding_amount
        string etax_invoice_ref
    }
    SalesOrder {
        string customer_id
        string customer_name
        date transaction_date
        date delivery_date
        string items
        number total
        number grand_total
    }
    SalesPartner {
        string partner_name
        number commission_rate
        string territory
        string partner_type
        boolean is_active
    }
    SalesReturn {
        string customer
        date return_date
        string reason
        string items
        number total
    }
    Territory {
        string territory_name
        string parent_territory
        string territory_manager
    }
```
