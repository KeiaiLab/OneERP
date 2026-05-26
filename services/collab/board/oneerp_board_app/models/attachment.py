"""첨부파일(Attachment) 문서 모델.

엔티티 정의: L2-spec 1.4
- BR-BRD-007: 첨부파일 용량/수 검증
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AttachmentCreate(BaseModel):
    """첨부파일 생성 요청 스키마."""

    post_id: str
    file_name: str
    file_key: str
    file_size: int
    mime_type: str
    file_extension: str
    checksum: str
    thumbnail_key: str | None = None
    uploaded_by: str = ""


class AttachmentUpdate(BaseModel):
    """첨부파일 수정 요청 스키마."""

    thumbnail_key: str | None = None


class Attachment(BaseDocument):
    """첨부파일 문서.

    BR-BRD-007: 파일 크기는 board.max_attachment_size_mb 이하,
    게시글당 파일 수는 board.max_attachments_per_post 이하.
    """

    post_id: str = ""
    file_name: str = ""
    file_key: str = ""
    file_size: int = 0
    mime_type: str = ""
    file_extension: str = ""
    checksum: str = ""
    thumbnail_key: str | None = None
    download_count: int = 0
    uploaded_by: str = ""
    deleted_at: str | None = None
