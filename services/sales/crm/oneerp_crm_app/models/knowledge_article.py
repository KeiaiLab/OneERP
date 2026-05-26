"""지식 베이스 문서(KnowledgeArticle) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KnowledgeArticleCreate(BaseModel):
    """지식 베이스 문서 생성 요청 스키마."""

    article_title: str
    content: str = ""
    category_id: str = ""
    author: str = ""
    is_published: bool = True


class KnowledgeArticleUpdate(BaseModel):
    """지식 베이스 문서 수정 요청 스키마."""

    article_title: str | None = None
    content: str | None = None
    category_id: str | None = None
    author: str | None = None
    is_published: bool | None = None


class KnowledgeArticle(BaseDocument):
    """지식 베이스 문서."""

    article_title: str = ""
    content: str = ""
    category_id: str = ""
    author: str = ""
    is_published: bool = True
