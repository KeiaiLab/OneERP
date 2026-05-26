"""문서 공유(DocumentShare) 모델 — 내부/외부 문서 공유 관리.

BR-DOC-013: 외부 공유 링크 만료일 필수, 최대 90일.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class ShareType(StrEnum):
    """공유 유형."""

    USER = "user"
    DEPARTMENT = "department"
    EXTERNAL_LINK = "external_link"


class SharePermission(StrEnum):
    """공유 권한 수준."""

    VIEWER = "viewer"
    COMMENTER = "commenter"
    EDITOR = "editor"


class DocumentShareCreate(BaseModel):
    """문서 공유 생성 요청 스키마."""

    document_id: str = Field(description="문서 참조 ID")
    share_type: ShareType = Field(description="공유 유형")
    target_user: str | None = Field(default=None, description="대상 사용자")
    target_department: str | None = Field(default=None, description="대상 부서")
    permission: SharePermission = Field(default=SharePermission.VIEWER, description="권한 수준")
    expires_at: datetime | None = Field(default=None, description="만료일")
    password: str | None = Field(default=None, description="외부 링크 암호")
    max_downloads: int | None = Field(default=None, ge=1, description="최대 다운로드 횟수")


class DocumentShareUpdate(BaseModel):
    """문서 공유 수정 요청 스키마."""

    permission: SharePermission | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    max_downloads: int | None = None


class DocumentShare(BaseDocument):
    """문서 공유 엔티티.

    문서의 공유 설정을 관리한다. 내부 사용자 지정 및 외부 링크 공유를 지원한다.
    """

    document_id: str = ""
    share_type: ShareType = ShareType.USER
    target_user: str | None = None
    target_department: str | None = None
    permission: SharePermission = SharePermission.VIEWER
    external_link_token: str | None = None
    external_link_password: str | None = None
    expires_at: datetime | None = None
    max_downloads: int | None = None
    download_count: int = 0
    is_active: bool = True
    shared_by: str = ""
