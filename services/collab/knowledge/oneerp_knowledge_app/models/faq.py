"""자주 묻는 질문(FAQ) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class FaqStatus(StrEnum):
    """FAQ 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FaqCreate(BaseModel):
    """FAQ 생성 요청 스키마."""

    question: str
    answer: str
    category: str | None = None
    status: FaqStatus = FaqStatus.DRAFT
    views_count: int = 0
    sort_order: int = 0


class FaqUpdate(BaseModel):
    """FAQ 수정 요청 스키마."""

    question: str | None = None
    answer: str | None = None
    category: str | None = None
    status: FaqStatus | None = None
    views_count: int | None = None
    sort_order: int | None = None


class Faq(BaseDocument):
    """FAQ 문서."""

    question: str = ""
    answer: str = ""
    category: str | None = None
    status: FaqStatus = FaqStatus.DRAFT
    views_count: int = 0
    sort_order: int = 0
