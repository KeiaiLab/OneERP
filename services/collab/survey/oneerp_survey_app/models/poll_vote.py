"""투표 기록(PollVote) 문서 모델.

개별 투표 기록을 저장한다.
네이밍 규칙: PV-{TENANT}-{#####}
"""

from __future__ import annotations

from datetime import UTC, datetime

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PollVoteCreate(BaseModel):
    """투표 기록 생성 요청 스키마."""

    poll_id: str = Field(description="투표 ID")
    voter_id: str | None = Field(default=None, description="투표자 ID")
    selected_options: list[str] = Field(min_length=1, description="선택한 option_id")
    voter_hash: str | None = Field(default=None, description="중복 투표 방지 해시")


class PollVoteUpdate(BaseModel):
    """투표 기록 수정 요청 스키마 (사용하지 않지만 EntityMeta 호환)."""


class PollVote(BaseDocument):
    """투표 기록 문서."""

    poll_id: str = ""
    voter_id: str | None = None
    selected_options: list[str] = Field(default_factory=list)
    voted_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    voter_hash: str | None = None
