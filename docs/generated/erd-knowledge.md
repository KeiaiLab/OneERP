# Knowledge 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Knowledge 서비스 ERD
---
erDiagram
    KnowledgeCategory {
        string category_name
        string parent_category
        string description
        number sort_order
    }

    KnowledgeArticle {
        string title
        string content
        string category
        string author
        array tags
        string status
        number views_count
        number helpfulness_rating
    }

    Faq {
        string question
        string answer
        string category
        string status
        number views_count
        number sort_order
    }

    KnowledgeCategory ||--o{ KnowledgeArticle : "category"
    KnowledgeCategory ||--o{ Faq : "category"
    KnowledgeCategory ||--o{ KnowledgeCategory : "parent_category"
```
