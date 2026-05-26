"""지식 분류(KnowledgeCategory) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class KnowledgeCategoryCreate(BaseModel):
    """지식 분류 생성 요청 스키마."""

    category_name: str
    parent_id: str = ""
    description: str = ""
    is_active: bool = True


class KnowledgeCategoryUpdate(BaseModel):
    """지식 분류 수정 요청 스키마."""

    category_name: str | None = None
    parent_id: str | None = None
    description: str | None = None
    is_active: bool | None = None


class KnowledgeCategory(BaseDocument):
    """지식 분류 문서."""

    category_name: str = ""
    parent_id: str = ""
    description: str = ""
    is_active: bool = True
