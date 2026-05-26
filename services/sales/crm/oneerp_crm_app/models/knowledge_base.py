"""지식베이스(KnowledgeBase) 문서 모델 — Support 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KnowledgeBaseCreate(BaseModel):
    """지식베이스 생성 요청 스키마."""

    title: str
    content: str = ""
    category: str = ""
    is_published: bool = False


class KnowledgeBaseUpdate(BaseModel):
    """지식베이스 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    category: str | None = None
    is_published: bool | None = None


class KnowledgeBase(BaseDocument):
    """지식베이스 문서 — Support 지식베이스 마스터.

    naming prefix: KB
    """

    title: str = ""
    content: str = ""
    category: str = ""
    is_published: bool = False
