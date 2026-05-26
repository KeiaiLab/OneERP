# BUYING 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: BUYING 서비스 ERD
---
erDiagram
    BuyerApprovalMatrix {
        string item_group
        number min_amount
        number max_amount
        string approver
        boolean is_active
    }
    LandedCostVoucher {
        string receipt_document
        date posting_date
        string items
        number total
    }
    MaterialRequest {
        string request_type
        date required_date
        string items
        number total_qty
    }
    PurchaseAnalytics {
        string period
        string item_code
        string supplier
        number total_qty
        number total_amount
    }
    PurchaseInvoice {
        string supplier_id
        string supplier_name
        date posting_date
        date due_date
        string items
        string taxes
        number grand_total
        number outstanding_amount
        string etax_invoice_ref
    }
    PurchaseOrder {
        string supplier_id
        string supplier_name
        date transaction_date
        string items
        number total
        number grand_total
    }
    PurchaseReceipt {
        string supplier
        string supplier_name
        date posting_date
        string items
        number total_qty
        number total_amount
        string warehouse
    }
    PurchaseReturn {
        string supplier
        date return_date
        string reason
        string items
        number total
    }
    RequestForQuotation {
        date transaction_date
        string suppliers
        string items
    }
    Supplier {
        string supplier_name
        string supplier_type
        string tax_id
        string default_currency
        string payment_terms
        string address
        string contact
    }
    SupplierGroup {
        string group_name
        string parent_group
    }
    SupplierQuotation {
        string supplier
        string supplier_name
        date transaction_date
        date valid_till
        string items
        number total
        number grand_total
    }
    SupplierScorecard {
        string supplier
        string evaluation_period
        number total_score
        string criteria
    }
```
