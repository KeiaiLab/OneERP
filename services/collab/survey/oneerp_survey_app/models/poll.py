"""투표(Poll) 문서 모델.

간단한 투표를 관리한다.
네이밍 규칙: POL-{TENANT}-{#####}
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class PollType(StrEnum):
    """투표 유형."""

    YES_NO = "yes_no"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"


class PollStatus(StrEnum):
    """투표 상태."""

    ACTIVE = "active"
    CLOSED = "closed"


class PollShowResults(StrEnum):
    """투표 결과 공개 시점."""

    REALTIME = "realtime"
    AFTER_CLOSE = "after_close"


class PollOption(BaseModel):
    """투표 선택지 — 임베디드."""

    option_id: str = Field(description="선택지 ID")
    text: str = Field(description="선택지 텍스트")
    vote_count: int = Field(default=0, description="득표 수")


class PollCreate(BaseModel):
    """투표 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=500, description="투표 제목")
    poll_type: PollType = Field(description="투표 유형")
    options: list[PollOption] = Field(min_length=2, description="선택지 (최소 2개)")
    anonymity: str = Field(default="named", description="익명/기명")
    ends_at: datetime | None = Field(default=None, description="마감 시각")
    show_results: PollShowResults = Field(
        default=PollShowResults.REALTIME, description="결과 공개 시점"
    )


class PollUpdate(BaseModel):
    """투표 수정 요청 스키마."""

    title: str | None = None
    ends_at: datetime | None = None
    status: PollStatus | None = None


class Poll(BaseDocument):
    """투표 문서."""

    title: str = ""
    poll_type: PollType = PollType.SINGLE_CHOICE
    options: list[PollOption] = Field(default_factory=list)
    anonymity: str = "named"
    status: PollStatus = PollStatus.ACTIVE
    ends_at: datetime | None = None
    show_results: PollShowResults = PollShowResults.REALTIME
    total_votes: int = 0
