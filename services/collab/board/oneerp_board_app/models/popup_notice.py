"""팝업 공지(PopupNotice) 문서 모델.

엔티티 정의: L2-spec 1.6
- BR-BRD-005: 팝업 공지 생성 권한
- BR-BRD-012: 팝업 공지 기간 검증
- BR-BRD-018: 팝업 공지 동시 활성 제한
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class PopupPriority(StrEnum):
    """팝업 우선순위."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ShowFrequency(StrEnum):
    """팝업 표시 빈도."""

    ONCE = "once"
    EVERY_LOGIN = "every_login"
    DAILY = "daily"


class PopupTarget(BaseModel):
    """팝업 대상 — 임베디드 객체."""

    target_type: str = "all"
    target_ids: list[str] = Field(default_factory=list)
    exclude_ids: list[str] = Field(default_factory=list)


class PopupNoticeCreate(BaseModel):
    """팝업 공지 생성 요청 스키마."""

    post_id: str | None = None
    title: str
    content: str
    priority: PopupPriority = PopupPriority.NORMAL
    target: PopupTarget
    start_at: datetime
    end_at: datetime
    is_active: bool = True
    require_confirm: bool = False
    show_on_login: bool = True
    show_frequency: ShowFrequency = ShowFrequency.ONCE
    display_order: int = 0


class PopupNoticeUpdate(BaseModel):
    """팝업 공지 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    priority: PopupPriority | None = None
    target: PopupTarget | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool | None = None
    require_confirm: bool | None = None
    show_on_login: bool | None = None
    show_frequency: ShowFrequency | None = None
    display_order: int | None = None


class PopupNotice(BaseDocument):
    """팝업 공지 문서.

    BR-BRD-005: 시스템 관리자 또는 board:manage 권한 보유자만 생성 가능.
    BR-BRD-012: end_at > start_at, 최대 기간 90일.
    BR-BRD-018: 테넌트당 동시 활성 팝업 최대 5개.
    """

    post_id: str | None = None
    title: str = ""
    content: str = ""
    priority: PopupPriority = PopupPriority.NORMAL
    target: PopupTarget = Field(default_factory=PopupTarget)
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool = True
    require_confirm: bool = False
    show_on_login: bool = True
    show_frequency: ShowFrequency = ShowFrequency.ONCE
    display_order: int = 0
    confirmed_count: int = 0
    total_target_count: int = 0
