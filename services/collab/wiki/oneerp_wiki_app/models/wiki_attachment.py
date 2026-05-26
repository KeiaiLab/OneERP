"""위키 첨부파일(WikiAttachment) 문서 모델 — 위키 모듈.

위키 페이지에 첨부된 파일 메타데이터를 관리한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiAttachmentCreate(BaseModel):
    """위키 첨부파일 생성 요청 스키마."""

    page_id: str
    file_name: str = ""
    file_url: str = ""
    file_size: int = 0
    mime_type: str = ""
    uploader_id: str = ""


class WikiAttachmentUpdate(BaseModel):
    """위키 첨부파일 수정 요청 스키마."""

    file_name: str | None = None
    file_url: str | None = None


class WikiAttachment(BaseDocument):
    """위키 첨부파일 — 페이지 첨부 파일 메타데이터.

    naming prefix: WA
    """

    page_id: str = Field(default="", description="위키 페이지 ID")
    file_name: str = Field(default="", description="파일명")
    file_url: str = Field(default="", description="파일 URL")
    file_size: int = Field(default=0, description="파일 크기 (바이트)")
    mime_type: str = Field(default="", description="MIME 타입")
    uploader_id: str = Field(default="", description="업로더 ID")
