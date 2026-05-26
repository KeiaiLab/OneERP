"""사내 메일 폴더(MailFolder) 문서 모델.

BR-MAIL-010: 기본 폴더(inbox, sent, drafts, trash)는 삭제 불가.
BR-MAIL-011: 폴더명은 같은 사용자 내에서 중복될 수 없다.
BR-MAIL-012: 폴더 계층은 최대 3단계까지 허용한다.
"""

from __future__ import annotations

from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator

# 삭제 불가 시스템 폴더 목록
SYSTEM_FOLDERS = frozenset({"inbox", "sent", "drafts", "trash", "starred", "archive"})


class MailFolderCreate(BaseModel):
    """메일 폴더 생성 요청 스키마.

    BR-MAIL-011: 폴더명 중복 검증은 서비스에서 처리.
    BR-MAIL-012: depth 최대 3.
    """

    name: Annotated[str, Field(min_length=1, max_length=100)]
    owner_id: str = ""
    parent_folder_id: str | None = None
    color: str = ""
    description: str = ""
    depth: int = 0

    @field_validator("depth")
    @classmethod
    def _폴더_깊이_제한(cls, v: int) -> int:
        """BR-MAIL-012: 폴더 계층은 최대 3단계까지."""
        max_depth = 3
        if v > max_depth:
            msg = f"폴더 계층은 최대 {max_depth}단계까지 허용됩니다 [ERR-MAIL-012]"
            raise ValueError(msg)
        return v


class MailFolderUpdate(BaseModel):
    """메일 폴더 수정 요청 스키마."""

    name: str | None = None
    color: str | None = None
    description: str | None = None


class MailFolder(BaseDocument):
    """사내 메일 폴더 문서.

    BR-MAIL-010 ~ BR-MAIL-012 비즈니스 규칙을 적용한다.
    """

    name: str = ""
    owner_id: str = ""
    parent_folder_id: str | None = None
    color: str = ""
    description: str = ""
    depth: int = 0
    is_system: bool = False
    message_count: int = 0
    unread_count: int = 0
