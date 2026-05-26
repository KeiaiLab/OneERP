"""게시글 커스텀 라우트 — 게시/아카이브/좋아요/북마크/신고/필독 확인.

L2-spec 5.2~5.7 API 계약에 따른 비즈니스 엔드포인트.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["게시글"])


class LikeResponse(BaseModel):
    """좋아요 토글 응답."""

    post_id: str
    liked: bool
    like_count: int


class BookmarkResponse(BaseModel):
    """북마크 토글 응답."""

    post_id: str
    bookmarked: bool
    bookmark_count: int


class ReadConfirmResponse(BaseModel):
    """필독 확인 응답."""

    post_id: str
    user_id: str
    status: str
    read_at: str | None = None


class ReportRequest(BaseModel):
    """신고 요청."""

    reason: str
    description: str = ""


class ReadConfirmStatsResponse(BaseModel):
    """필독 통계 응답."""

    post_id: str
    total: int
    read: int
    unread: int
    rate: float


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def toggle_like(post_id: str) -> dict[str, Any]:
    """게시글 좋아요 토글.

    BR-BRD-014: 이미 좋아요 상태면 취소, 아니면 추가.
    """
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    return svc.toggle_like(post_id, user_id="current_user")


@router.post("/posts/{post_id}/bookmark", response_model=BookmarkResponse)
async def toggle_bookmark(post_id: str) -> dict[str, Any]:
    """게시글 북마크 토글.

    BR-BRD-014: 이미 북마크 상태면 취소, 아니면 추가.
    """
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    return svc.toggle_bookmark(post_id, user_id="current_user")


@router.post("/posts/{post_id}/read-confirm", response_model=ReadConfirmResponse)
async def confirm_read(post_id: str) -> dict[str, Any]:
    """필독 확인.

    SC-BRD-004: 대상자가 게시글 열람 후 확인 처리.
    """
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    return svc.confirm_read(post_id, user_id="current_user")


@router.get("/posts/{post_id}/read-confirm/stats", response_model=ReadConfirmStatsResponse)
async def read_confirm_stats(post_id: str) -> dict[str, Any]:
    """필독 확인 통계."""
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    return svc.get_read_confirm_stats(post_id)


@router.post("/posts/{post_id}/report")
async def report_post(post_id: str, body: ReportRequest) -> dict[str, Any]:
    """게시글 신고.

    BR-BRD-019: 동일 사용자 동일 게시글 pending 신고 중복 불가.
    """
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    return svc.create_report(
        {
            "post_id": post_id,
            "reporter_id": "current_user",
            "reason": body.reason,
            "description": body.description,
        }
    )


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: str) -> dict[str, Any]:
    """게시글 게시 (draft/scheduled → published)."""
    from oneerp_board_app.services.post_service import PostService

    svc = PostService("T1")
    return svc.publish_post(post_id)


@router.post("/posts/{post_id}/archive")
async def archive_post(post_id: str) -> dict[str, Any]:
    """게시글 아카이브 (published → archived)."""
    from oneerp_board_app.services.post_service import PostService

    svc = PostService("T1")
    return svc.archive_post(post_id)


@router.post("/posts/{post_id}/read-confirm/remind")
async def send_reminders(post_id: str) -> dict[str, int]:
    """필독 미확인자 리마인더 발송.

    BR-BRD-011: 최대 5회까지 리마인더 발송.
    """
    from oneerp_board_app.services.interaction_service import InteractionService

    svc = InteractionService("T1")
    count = svc.send_reminders(post_id)
    return {"reminded_count": count}
