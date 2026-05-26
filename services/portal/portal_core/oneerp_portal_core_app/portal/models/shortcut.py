"""바로가기(Shortcut) 문서 모델.

BR-PTL-003: 사용자당 최대 20개 바로가기 제한.
"""

from __future__ import annotations

import re

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator

_URL_PATTERN = re.compile(r"^(https?://|/)")


class ShortcutCreate(BaseModel):
    """바로가기 생성 요청 스키마."""

    shortcut_name: str = Field(min_length=1, max_length=50, description="바로가기 이름")
    url: str = Field(min_length=1, max_length=500, description="대상 URL")
    icon: str = Field(default="link", description="아이콘 이름")
    color: str = Field(default="#1976D2", description="아이콘 색상")
    sort_order: int = Field(default=0, ge=0, description="정렬 순서")
    user_id: str = Field(default="", description="사용자 ID (서버에서 설정)")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """URL 형식 검증 — 절대 URL 또는 루트 상대 경로만 허용."""
        if not _URL_PATTERN.match(v):
            msg = f"유효한 URL이 아닙니다: {v} (http://, https://, / 로 시작해야 합니다)"
            raise ValueError(msg)
        return v


class ShortcutUpdate(BaseModel):
    """바로가기 수정 요청 스키마."""

    shortcut_name: str | None = None
    url: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """URL 형식 검증."""
        if v is not None and not _URL_PATTERN.match(v):
            msg = f"유효한 URL이 아닙니다: {v}"
            raise ValueError(msg)
        return v


class Shortcut(BaseDocument):
    """바로가기 문서.

    BR-PTL-003: 사용자당 최대 20개 제한.
    """

    shortcut_name: str = ""
    url: str = ""
    icon: str = "link"
    color: str = "#1976D2"
    sort_order: int = 0
    user_id: str = ""
    click_count: int = 0
