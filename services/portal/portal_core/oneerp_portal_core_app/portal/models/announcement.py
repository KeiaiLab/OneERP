"""공지사항(Announcement) 문서 모델.

BR-PTL-004: 필수 공지사항 강제 표시.
BR-PTL-005: 선택 공지 '오늘 하루 보지 않기'.
BR-PTL-006: 긴급 공지 빨간 배너 표시.
BR-PTL-011: 동시 긴급 공지 3건 초과 경고.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import datetime


class AnnouncementStatus(StrEnum):
    """공지사항 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class AnnouncementPriority(StrEnum):
    """공지사항 우선순위."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementCreate(BaseModel):
    """공지사항 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=200, description="제목")
    content: str = Field(min_length=1, description="내용")
    priority: AnnouncementPriority = Field(
        default=AnnouncementPriority.NORMAL,
        description="우선순위",
    )
    is_mandatory: bool = Field(default=False, description="필수 공지 여부 (BR-PTL-004)")
    target_departments: list[str] = Field(
        default_factory=list,
        description="대상 부서 (빈 목록=전체)",
    )
    target_roles: list[str] = Field(
        default_factory=list,
        description="대상 역할 (빈 목록=전체)",
    )
    start_date: datetime | None = Field(default=None, description="게시 시작일")
    end_date: datetime | None = Field(default=None, description="게시 종료일")

    @model_validator(mode="after")
    def validate_dates(self) -> AnnouncementCreate:
        """종료일이 시작일보다 이전이면 에러 — ERR-PTL-006."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            msg = "종료일은 시작일 이후여야 합니다 (ERR-PTL-006)"
            raise ValueError(msg)
        return self


class AnnouncementUpdate(BaseModel):
    """공지사항 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    priority: AnnouncementPriority | None = None
    is_mandatory: bool | None = None
    target_departments: list[str] | None = None
    target_roles: list[str] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: AnnouncementStatus | None = None


class Announcement(BaseDocument):
    """공지사항 문서.

    BR-PTL-004: 필수 공지사항은 닫기 버튼 없이 표시.
    BR-PTL-005: 선택 공지는 '오늘 하루 보지 않기' 가능.
    BR-PTL-006: 긴급 공지는 빨간 배너로 최상단 표시.
    """

    title: str = ""
    content: str = ""
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    status: AnnouncementStatus = AnnouncementStatus.DRAFT
    is_mandatory: bool = False
    target_departments: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    published_by: str = ""
    read_count: int = 0
