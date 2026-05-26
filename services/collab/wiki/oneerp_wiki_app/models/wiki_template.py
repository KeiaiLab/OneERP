"""위키 템플릿(WikiTemplate) 문서 모델 — 위키 모듈.

자주 사용하는 페이지 구조를 템플릿으로 저장한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiTemplateCreate(BaseModel):
    """위키 템플릿 생성 요청 스키마."""

    name: str
    description: str = ""
    content: str = ""
    category: str = ""


class WikiTemplateUpdate(BaseModel):
    """위키 템플릿 수정 요청 스키마."""

    name: str | None = None
    description: str | None = None
    content: str | None = None
    category: str | None = None


class WikiTemplate(BaseDocument):
    """위키 템플릿 — 재사용 가능한 페이지 골격.

    naming prefix: WT
    """

    name: str = Field(default="", description="템플릿 이름")
    description: str = Field(default="", description="템플릿 설명")
    content: str = Field(default="", description="마크다운 템플릿 본문")
    category: str = Field(default="", description="템플릿 분류")
