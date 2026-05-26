"""게시글 관리 서비스 — 게시글 CRUD, 상태 전이, 필독, 예약 발행.

BR-BRD-002: 게시글 작성 권한 검증
BR-BRD-003: 게시글 수정/삭제 권한
BR-BRD-004: 필독 설정 권한
BR-BRD-006: 예약 발행 시각 검증
BR-BRD-009: 익명 게시글 제한
BR-BRD-010: 필독 확인 생성 자동화
BR-BRD-016: 카테고리 유효성 검증
BR-BRD-017: 게시글 상단 고정 제한
BR-BRD-020: 조회수 중복 카운트 방지
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from oneerp_core.errors import (
    raise_forbidden,
    raise_not_found,
    raise_unprocessable,
)
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 상단 고정 게시글 최대 수
MAX_PINNED_POSTS = 10


class PostService:
    """게시글 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._post_repo = Repository("posts", tenant_id=tenant_id)
        self._board_repo = Repository("boards", tenant_id=tenant_id)
        self._rc_repo = Repository("read_confirmations", tenant_id=tenant_id)

    def create_post(
        self,
        board_id: str,
        data: dict[str, Any],
        *,
        has_write: bool = True,
        has_manage: bool = False,
    ) -> dict[str, Any]:
        """게시글을 생성한다.

        BR-BRD-002: write 이상 권한 필요.
        BR-BRD-004: 필독은 manage 권한 필요.
        BR-BRD-006: 예약 발행 시각 검증.
        BR-BRD-009: 익명 글은 allow_anonymous 게시판만.
        BR-BRD-016: 카테고리 유효성 검증.
        BR-BRD-017: 상단 고정 최대 10개.
        """
        if not has_write:
            raise_forbidden("ERR-BRD-010: 이 작업을 수행할 권한이 없습니다")

        board = self._board_repo.find_by_id(board_id)
        if not board:
            raise_not_found("ERR-BRD-002: 게시판을 찾을 수 없습니다")
        board = cast("dict[str, Any]", board)

        # BR-BRD-009: 익명 글 제한
        if data.get("is_anonymous") and not board.get("allow_anonymous", False):
            raise_unprocessable(
                "ERR-BRD-034",
                "이 게시판에서는 익명 글 작성이 불가합니다",
            )

        # BR-BRD-016: 카테고리 유효성
        category = data.get("category")
        board_categories = board.get("categories", [])
        if category and board_categories and category not in board_categories:
            raise_unprocessable(
                "ERR-BRD-038",
                "유효하지 않은 카테고리입니다",
            )

        # BR-BRD-004: 필독 설정 권한
        if data.get("is_must_read") and not has_manage:
            raise_forbidden("ERR-BRD-012: 필독 설정은 게시판 관리자만 가능합니다")

        # BR-BRD-017: 상단 고정 제한
        if data.get("is_pinned"):
            pinned_count = self._post_repo.count(
                {
                    "board_id": board_id,
                    "is_pinned": True,
                }
            )
            if pinned_count >= MAX_PINNED_POSTS:
                raise_unprocessable(
                    "ERR-BRD-039",
                    f"상단 고정 게시글은 최대 {MAX_PINNED_POSTS}개까지 가능합니다",
                )

        # BR-BRD-006: 예약 발행 시각 검증
        status = data.get("status", "draft")
        scheduled_at = data.get("scheduled_at")
        if status == "scheduled":
            if not scheduled_at:
                raise_unprocessable(
                    "ERR-BRD-030",
                    "예약 발행 시각이 지정되지 않았습니다",
                )
            min_time = datetime.now(tz=UTC) + timedelta(minutes=5)
            normalized_scheduled_at: datetime | None
            if isinstance(scheduled_at, str):
                normalized_scheduled_at = datetime.fromisoformat(scheduled_at)
            elif isinstance(scheduled_at, datetime):
                normalized_scheduled_at = scheduled_at
            else:
                normalized_scheduled_at = None
            if normalized_scheduled_at is None:
                raise_unprocessable("ERR-BRD-030", "예약 발행 시각 형식이 올바르지 않습니다")
            normalized_scheduled_at = cast("datetime", normalized_scheduled_at)
            if normalized_scheduled_at.tzinfo is None:
                normalized_scheduled_at = normalized_scheduled_at.replace(tzinfo=UTC)
            if normalized_scheduled_at < min_time:
                raise_unprocessable(
                    "ERR-BRD-030",
                    "예약 발행 시각은 현재 시각보다 5분 이상 이후여야 합니다",
                )
            data["scheduled_at"] = normalized_scheduled_at.isoformat()

        post_id = generate_name("PST", tenant_id=self._tenant_id)
        data["_id"] = post_id
        data["board_id"] = board_id
        data["tenant_id"] = self._tenant_id

        # 즉시 게시인 경우
        if status == "published":
            data["published_at"] = datetime.now(tz=UTC).isoformat()

        self._post_repo.insert(data)

        # BR-BRD-010: 필독 확인 자동 생성
        result: dict[str, Any] = {"_id": post_id, "board_id": board_id, "status": status}
        if status == "published" and data.get("is_must_read"):
            rc_count = self._create_read_confirmations(
                post_id,
                data.get("must_read_target", {}),
            )
            result["read_confirmation_count"] = rc_count

        logger.info("게시글 생성: %s (게시판: %s)", post_id, board_id)
        return result

    def get_post(self, post_id: str) -> dict[str, Any]:
        """게시글 상세를 조회한다."""
        post = self._post_repo.find_by_id(post_id)
        if not post or post.get("status") == "deleted":
            raise_not_found("ERR-BRD-003: 게시글을 찾을 수 없습니다")
        return cast("dict[str, Any]", post)

    def update_post(
        self,
        post_id: str,
        data: dict[str, Any],
        *,
        user_id: str = "",
        has_manage: bool = False,
    ) -> dict[str, Any]:
        """게시글을 수정한다.

        BR-BRD-003: 본인 글이거나 manage 권한 필요.
        """
        post = self.get_post(post_id)

        if post.get("author_id") != user_id and not has_manage:
            raise_forbidden("ERR-BRD-011: 본인의 글만 수정/삭제할 수 있습니다")

        # 수정 이력 기록
        revision_count = post.get("revision_count", 0) + 1
        data["revision_count"] = revision_count

        self._post_repo.update_by_id(post_id, data)
        logger.info("게시글 수정: %s (revision: %d)", post_id, revision_count)
        return {"_id": post_id, **data}

    def delete_post(
        self,
        post_id: str,
        *,
        user_id: str = "",
        has_manage: bool = False,
    ) -> bool:
        """게시글을 소프트 삭제한다.

        BR-BRD-003: 본인 글이거나 manage 권한 필요.
        """
        post = self.get_post(post_id)

        if post.get("author_id") != user_id and not has_manage:
            raise_forbidden("ERR-BRD-011: 본인의 글만 수정/삭제할 수 있습니다")

        self._post_repo.update_by_id(
            post_id,
            {
                "status": "deleted",
                "deleted_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        logger.info("게시글 삭제: %s", post_id)
        return True

    def publish_post(self, post_id: str) -> dict[str, Any]:
        """게시글을 게시 상태로 전환한다."""
        post = self.get_post(post_id)
        now = datetime.now(tz=UTC).isoformat()
        self._post_repo.update_by_id(
            post_id,
            {
                "status": "published",
                "published_at": now,
            },
        )
        logger.info("게시글 게시: %s", post_id)

        result: dict[str, Any] = {"_id": post_id, "status": "published", "published_at": now}

        # 필독 확인 자동 생성
        if post.get("is_must_read"):
            rc_count = self._create_read_confirmations(
                post_id,
                post.get("must_read_target", {}),
            )
            result["read_confirmation_count"] = rc_count

        return result

    def archive_post(self, post_id: str) -> dict[str, Any]:
        """게시글을 아카이브 상태로 전환한다."""
        self.get_post(post_id)
        self._post_repo.update_by_id(post_id, {"status": "archived"})
        logger.info("게시글 아카이브: %s", post_id)
        return {"_id": post_id, "status": "archived"}

    def increment_view_count(self, post_id: str) -> None:
        """조회수를 1 증가시킨다.

        BR-BRD-020: 실제로는 Redis 기반 중복 방지 필요 (현재는 단순 증가).
        """
        post = self._post_repo.find_by_id(post_id)
        if post:
            self._post_repo.update_by_id(
                post_id,
                {"view_count": post.get("view_count", 0) + 1},
            )

    def process_scheduled_posts(self) -> list[str]:
        """예약 시각이 도래한 게시글을 일괄 게시한다."""
        now = datetime.now(tz=UTC).isoformat()
        scheduled = self._post_repo.find_many(
            {"status": "scheduled", "scheduled_at": {"$lte": now}},
            limit=100,
        )
        published_ids: list[str] = []
        for post in scheduled:
            post_id = post.get("_id", "")
            self._post_repo.update_by_id(
                post_id,
                {
                    "status": "published",
                    "published_at": now,
                },
            )
            published_ids.append(post_id)
            logger.info("예약 게시글 발행: %s", post_id)
        return published_ids

    def _create_read_confirmations(
        self,
        post_id: str,
        target: dict[str, Any] | None,
    ) -> int:
        """필독 확인 레코드를 대상자별로 생성한다.

        BR-BRD-010: 실제로는 HR-Core API로 대상자 조회.
        현재는 target_ids를 직접 사용하거나, 빈 목록 반환.
        """
        if not target:
            return 0

        target_type = target.get("target_type", "all") if isinstance(target, dict) else "all"
        target_ids = target.get("target_ids", []) if isinstance(target, dict) else []
        exclude_ids = set(target.get("exclude_ids", []) if isinstance(target, dict) else [])

        # all 타입일 때는 외부 API 호출이 필요하므로 0 반환
        if target_type == "all" and not target_ids:
            logger.warning("필독 대상 전체(all): HR-Core API 연동 필요")
            return 0

        user_ids = [uid for uid in target_ids if uid not in exclude_ids]
        for user_id in user_ids:
            rc_id = generate_name("RC", tenant_id=self._tenant_id)
            self._rc_repo.insert(
                {
                    "_id": rc_id,
                    "post_id": post_id,
                    "user_id": user_id,
                    "status": "unread",
                    "reminder_count": 0,
                    "tenant_id": self._tenant_id,
                }
            )

        logger.info("필독 확인 생성: %s (대상 %d명)", post_id, len(user_ids))
        return len(user_ids)
