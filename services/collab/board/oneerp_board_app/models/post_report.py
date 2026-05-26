"""게시글 신고(PostReport) 문서 모델.

엔티티 정의: L2-spec 1.11
- BR-BRD-019: 게시글 신고 중복 방지
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class ReportReason(StrEnum):
    """신고 사유 유형."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    PRIVACY = "privacy"
    OTHER = "other"


class ReportStatus(StrEnum):
    """신고 처리 상태."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ACTION_TAKEN = "action_taken"


class PostReportCreate(BaseModel):
    """게시글 신고 생성 요청 스키마."""

    post_id: str
    reporter_id: str = ""
    reason: ReportReason
    description: str = ""


class PostReportUpdate(BaseModel):
    """게시글 신고 수정 요청 스키마."""

    status: ReportStatus | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    action_note: str | None = None


class PostReport(BaseDocument):
    """게시글 신고 문서.

    BR-BRD-019: 동일 사용자가 동일 게시글에 pending 상태 신고 중복 불가.
    """

    post_id: str = ""
    reporter_id: str = ""
    reason: ReportReason = ReportReason.OTHER
    description: str = ""
    status: ReportStatus = ReportStatus.PENDING
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    action_note: str | None = None
