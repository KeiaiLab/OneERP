"""위키 페이지 리비전(WikiPageRevision) 문서 모델 — 위키 모듈.

페이지 수정 이력을 버전별로 보관한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiPageRevisionCreate(BaseModel):
    """위키 페이지 리비전 생성 요청 스키마."""

    page_id: str
    version: int = 1
    title: str = ""
    content: str = ""
    editor_id: str = ""
    change_summary: str = ""


class WikiPageRevisionUpdate(BaseModel):
    """위키 페이지 리비전 수정 요청 스키마."""

    change_summary: str | None = None


class WikiPageRevision(BaseDocument):
    """위키 페이지 리비전 — 페이지 버전 스냅샷.

    naming prefix: WPR
    """

    page_id: str = Field(default="", description="위키 페이지 ID")
    version: int = Field(default=1, description="리비전 버전 번호")
    title: str = Field(default="", description="해당 버전의 제목")
    content: str = Field(default="", description="해당 버전의 본문")
    editor_id: str = Field(default="", description="편집자 ID")
    change_summary: str = Field(default="", description="변경 요약")
