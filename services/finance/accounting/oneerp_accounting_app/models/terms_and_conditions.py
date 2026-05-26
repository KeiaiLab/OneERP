"""약관 관리(TermsAndConditions) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class TermsAndConditionsCreate(BaseModel):
    """약관 생성 요청 스키마."""

    title: str
    content: str = ""
    is_active: bool = True


class TermsAndConditionsUpdate(BaseModel):
    """약관 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    is_active: bool | None = None


class TermsAndConditions(BaseDocument):
    """약관 문서."""

    title: str = ""
    content: str = ""
    is_active: bool = True
