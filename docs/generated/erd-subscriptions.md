# Subscriptions 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Subscriptions 서비스 ERD
---
erDiagram
    SubscriptionPlan {
        string plan_name
        string billing_interval
        number price
        string currency
        array features
        number trial_days
        boolean is_active
    }

    Subscription {
        string customer_id
        string plan_id
        date start_date
        date end_date
        date next_billing_date
        string status
        string cancel_reason
        string company
    }

    RecurringInvoice {
        string customer_id
        string frequency
        date next_date
        string template_invoice_id
        string status
        string company
    }

    SubscriptionInvoice {
        string subscription_id
        number amount
        string sales_invoice_id
        string status
        string company
    }

    SubscriptionPlan ||--o{ Subscription : "플랜 구독"
    Subscription ||--o{ SubscriptionInvoice : "구독 청구"
    RecurringInvoice ||--o{ SubscriptionInvoice : "정기 청구"
```
