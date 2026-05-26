# Documents 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Documents 서비스 ERD
---
erDiagram
    Document {
        string doc_no
        string title
        string category
        string content
        string author
        number version
        string status
        string security_level
    }

    DocumentCategory {
        string name
        string code
        string parent_category
        number depth
        string path
        string default_security_level
        boolean is_active
    }

    DocumentTemplate {
        string template_name
        string description
        string content_template
        string default_security_level
        boolean is_active
        number usage_count
    }

    DocumentVersion {
        string document_id
        number version_no
        string version_type
        string title
        string content
        string change_summary
        string changed_by
        string content_hash
    }

    DocumentSignature {
        string document_id
        number document_version
        string signer
        string signature_type
        string document_hash
        datetime signed_at
        boolean is_valid
    }

    DocumentShare {
        string document_id
        string share_type
        string target_user
        string permission
        datetime expires_at
        boolean is_active
        string shared_by
    }

    DocumentAuditLog {
        string document_id
        string action
        string actor
        string actor_ip
        datetime timestamp
    }

    RetentionPolicy {
        string policy_name
        string description
        number retention_years
        number retention_months
        string action_on_expiry
        boolean requires_approval
        string legal_basis
    }

    DocumentCategory ||--o{ Document : "classifies"
    DocumentTemplate ||--o{ Document : "generates"
    Document ||--o{ DocumentVersion : "versioned_by"
    Document ||--o{ DocumentSignature : "signed_by"
    Document ||--o{ DocumentShare : "shared_via"
    Document ||--o{ DocumentAuditLog : "audited_by"
    RetentionPolicy ||--o{ Document : "governs"
```
