# Wiki 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: Wiki 서비스 ERD
---
erDiagram
    WikiSpace {
        string name
        string description
        string visibility
        string owner_id
        number page_count
    }

    WikiPage {
        string title
        string content
        string space_id
        string parent_page_id
        string author_id
        string status
        number version
        number view_count
    }

    WikiPageRevision {
        string page_id
        number version
        string title
        string content
        string editor_id
        string change_summary
    }

    WikiComment {
        string page_id
        string author_id
        string content
        string parent_comment_id
    }

    WikiAttachment {
        string page_id
        string file_name
        string file_url
        number file_size
        string mime_type
        string uploader_id
    }

    WikiTemplate {
        string name
        string description
        string content
        string category
    }

    WikiSpace ||--o{ WikiPage : "공간 내 페이지"
    WikiPage ||--o{ WikiPageRevision : "수정 이력"
    WikiPage ||--o{ WikiComment : "댓글"
    WikiPage ||--o{ WikiAttachment : "첨부파일"
    WikiPage ||--o| WikiPage : "상위-하위 페이지"
```
