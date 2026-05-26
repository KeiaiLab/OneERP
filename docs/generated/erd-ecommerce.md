# ECommerce 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: ECommerce 서비스 ERD
---
erDiagram
    ECommerceChannel {
        string channel_code
        string channel_name
        string platform
        string sync_frequency
        boolean is_active
        string warehouse_id
        string price_list_id
    }

    MarketplaceOrder {
        string channel_id
        string external_order_id
        string customer_name
        array items
        number total_amount
        string status
        string sales_order_id
        datetime synced_at
    }

    DropShipOrder {
        string sales_order_id
        string supplier_id
        array items
        string shipping_address
        string status
        string tracking_number
    }

    ECommerceChannel ||--o{ MarketplaceOrder : "receives"
    MarketplaceOrder ||--o| DropShipOrder : "fulfilled_by"
```
