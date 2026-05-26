"""뉴스/이벤트(NewsEvent) 문서 모델.

사내 뉴스와 이벤트를 관리한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import datetime


class NewsEventStatus(StrEnum):
    """뉴스/이벤트 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class NewsEventType(StrEnum):
    """뉴스/이벤트 유형."""

    NEWS = "news"
    EVENT = "event"
    NOTICE = "notice"


class NewsEventCreate(BaseModel):
    """뉴스/이벤트 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=200, description="제목")
    content: str = Field(min_length=1, description="내용")
    summary: str = Field(default="", max_length=500, description="요약")
    event_type: NewsEventType = Field(default=NewsEventType.NEWS, description="유형")
    thumbnail_url: str = Field(default="", description="썸네일 URL")
    event_date: datetime | None = Field(default=None, description="이벤트 일시")
    event_end_date: datetime | None = Field(default=None, description="이벤트 종료 일시")
    tags: list[str] = Field(default_factory=list, description="태그")
    target_departments: list[str] = Field(
        default_factory=list,
        description="대상 부서 (빈 목록=전체)",
    )

    @model_validator(mode="after")
    def validate_event_dates(self) -> NewsEventCreate:
        """이벤트 종료일이 시작일 이전이면 에러."""
        if self.event_date and self.event_end_date and self.event_end_date < self.event_date:
            msg = "이벤트 종료일은 시작일 이후여야 합니다"
            raise ValueError(msg)
        return self


class NewsEventUpdate(BaseModel):
    """뉴스/이벤트 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    summary: str | None = None
    event_type: NewsEventType | None = None
    thumbnail_url: str | None = None
    event_date: datetime | None = None
    event_end_date: datetime | None = None
    tags: list[str] | None = None
    target_departments: list[str] | None = None
    status: NewsEventStatus | None = None


class NewsEvent(BaseDocument):
    """뉴스/이벤트 문서."""

    title: str = ""
    content: str = ""
    summary: str = ""
    event_type: NewsEventType = NewsEventType.NEWS
    status: NewsEventStatus = NewsEventStatus.DRAFT
    thumbnail_url: str = ""
    event_date: datetime | None = None
    event_end_date: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    target_departments: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    published_by: str = ""
    view_count: int = 0
