"""FAQ(Faq) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class FaqCreate(BaseModel):
    """FAQ 생성 요청 스키마."""

    question: str
    answer: str = ""
    category: str = ""
    view_count: int = 0
    is_published: bool = True


class FaqUpdate(BaseModel):
    """FAQ 수정 요청 스키마."""

    question: str | None = None
    answer: str | None = None
    category: str | None = None
    view_count: int | None = None
    is_published: bool | None = None


class Faq(BaseDocument):
    """FAQ 문서."""

    question: str = ""
    answer: str = ""
    category: str = ""
    view_count: int = 0
    is_published: bool = True
