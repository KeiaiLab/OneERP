# PLM 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: PLM 서비스 ERD
---
erDiagram
    Product {
        string product_code
        string product_name
        string product_type
        string lifecycle_status
        string description
        string uom
        number weight
        string responsible_engineer
    }

    BOMVersion {
        string product_id
        string bom_type
        number version_major
        string version_label
        string status
        number base_quantity
        array items
        number total_cost
    }

    Drawing {
        string drawing_number
        string title
        string drawing_type
        string product_id
        string revision
        string status
        string file_url
        string file_format
    }

    EngChangeOrder {
        string eco_number
        string title
        string change_type
        string priority
        string status
        boolean is_emergency
        array affected_products
        date target_effective_date
    }

    EngChangeNotice {
        string ecn_number
        string eco_id
        string title
        string status
        date effective_date
        array bom_changes
        array drawing_changes
        string issued_by
    }

    Certification {
        string product_id
        string cert_type
        string cert_number
        string cert_name
        string certifying_body
        string status
        date issued_date
        date expiry_date
    }

    PartApproval {
        string part_code
        string part_name
        string manufacturer
        string manufacturer_part_number
        string status
        string request_reason
        string intended_use
    }

    Product ||--o{ BOMVersion : "BOM버전"
    Product ||--o{ Drawing : "도면관리"
    Product ||--o{ Certification : "인증관리"
    Product }o--o{ EngChangeOrder : "설계변경요청"
    EngChangeOrder ||--o| EngChangeNotice : "변경통보"
    EngChangeOrder }o--o{ BOMVersion : "BOM영향"
    EngChangeOrder }o--o{ Drawing : "도면영향"
    PartApproval }o--o{ Product : "부품승인"
```
