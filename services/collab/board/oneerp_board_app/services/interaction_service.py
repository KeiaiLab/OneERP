"""상호작용 서비스 — 좋아요, 북마크, 신고, 필독 확인.

BR-BRD-014: 좋아요/북마크 중복 방지 (토글)
BR-BRD-019: 게시글 신고 중복 방지
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_conflict, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class InteractionService:
    """좋아요/북마크/신고/필독 확인 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._like_repo = Repository("post_likes", tenant_id=tenant_id)
        self._bookmark_repo = Repository("post_bookmarks", tenant_id=tenant_id)
        self._report_repo = Repository("post_reports", tenant_id=tenant_id)
        self._rc_repo = Repository("read_confirmations", tenant_id=tenant_id)
        self._post_repo = Repository("posts", tenant_id=tenant_id)

    def toggle_like(self, post_id: str, user_id: str) -> dict[str, Any]:
        """좋아요를 토글한다.

        BR-BRD-014: 이미 존재하면 삭제, 없으면 생성.
        """
        post = self._post_repo.find_by_id(post_id)
        if not post:
            raise_not_found("ERR-BRD-003: 게시글을 찾을 수 없습니다")

        existing = self._like_repo.find_many(
            {"post_id": post_id, "user_id": user_id},
            limit=1,
        )

        like_count = post.get("like_count", 0)

        if existing:
            # 좋아요 취소
            like_id = existing[0].get("_id", "")
            self._like_repo.delete_by_id(like_id)
            new_count = max(0, like_count - 1)
            self._post_repo.update_by_id(post_id, {"like_count": new_count})
            logger.info("좋아요 취소: %s (사용자: %s)", post_id, user_id)
            return {"post_id": post_id, "liked": False, "like_count": new_count}

        # 좋아요 추가
        like_id = generate_name("LK", tenant_id=self._tenant_id)
        self._like_repo.insert(
            {
                "_id": like_id,
                "post_id": post_id,
                "user_id": user_id,
                "tenant_id": self._tenant_id,
            }
        )
        new_count = like_count + 1
        self._post_repo.update_by_id(post_id, {"like_count": new_count})
        logger.info("좋아요 추가: %s (사용자: %s)", post_id, user_id)
        return {"post_id": post_id, "liked": True, "like_count": new_count}

    def toggle_bookmark(self, post_id: str, user_id: str) -> dict[str, Any]:
        """북마크를 토글한다.

        BR-BRD-014: 이미 존재하면 삭제, 없으면 생성.
        """
        post = self._post_repo.find_by_id(post_id)
        if not post:
            raise_not_found("ERR-BRD-003: 게시글을 찾을 수 없습니다")

        existing = self._bookmark_repo.find_many(
            {"post_id": post_id, "user_id": user_id},
            limit=1,
        )

        bookmark_count = post.get("bookmark_count", 0)

        if existing:
            bm_id = existing[0].get("_id", "")
            self._bookmark_repo.delete_by_id(bm_id)
            new_count = max(0, bookmark_count - 1)
            self._post_repo.update_by_id(post_id, {"bookmark_count": new_count})
            logger.info("북마크 취소: %s (사용자: %s)", post_id, user_id)
            return {"post_id": post_id, "bookmarked": False, "bookmark_count": new_count}

        bm_id = generate_name("BM", tenant_id=self._tenant_id)
        self._bookmark_repo.insert(
            {
                "_id": bm_id,
                "post_id": post_id,
                "user_id": user_id,
                "tenant_id": self._tenant_id,
            }
        )
        new_count = bookmark_count + 1
        self._post_repo.update_by_id(post_id, {"bookmark_count": new_count})
        logger.info("북마크 추가: %s (사용자: %s)", post_id, user_id)
        return {"post_id": post_id, "bookmarked": True, "bookmark_count": new_count}

    def create_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """게시글 신고를 접수한다.

        BR-BRD-019: 동일 사용자가 동일 게시글에 pending 신고 중복 불가.
        """
        post_id = data.get("post_id", "")
        reporter_id = data.get("reporter_id", "")

        # 중복 신고 확인
        existing = self._report_repo.find_many(
            {"post_id": post_id, "reporter_id": reporter_id, "status": "pending"},
            limit=1,
        )
        if existing:
            raise_conflict("ERR-BRD-041: 이미 접수된 신고가 있습니다")

        report_id = generate_name("RPT", tenant_id=self._tenant_id)
        data["_id"] = report_id
        data["status"] = "pending"
        data["tenant_id"] = self._tenant_id
        self._report_repo.insert(data)

        logger.info("게시글 신고: %s (게시글: %s)", report_id, post_id)
        return {"_id": report_id, "status": "pending"}

    def confirm_read(self, post_id: str, user_id: str) -> dict[str, Any]:
        """필독 확인을 처리한다.

        ERR-BRD-045: 대상이 아닌 사용자.
        """
        confirmations = self._rc_repo.find_many(
            {"post_id": post_id, "user_id": user_id},
            limit=1,
        )
        if not confirmations:
            raise_not_found("ERR-BRD-045: 필독 확인 대상이 아닙니다")

        rc = confirmations[0]
        rc_id = rc.get("_id", "")

        # 이미 확인된 경우 멱등 처리
        if rc.get("status") == "read":
            return {
                "post_id": post_id,
                "user_id": user_id,
                "status": "read",
                "read_at": rc.get("read_at"),
            }

        now = datetime.now(tz=UTC).isoformat()
        self._rc_repo.update_by_id(
            rc_id,
            {
                "status": "read",
                "read_at": now,
            },
        )

        logger.info("필독 확인: %s (사용자: %s)", post_id, user_id)
        return {"post_id": post_id, "user_id": user_id, "status": "read", "read_at": now}

    def get_read_confirm_stats(self, post_id: str) -> dict[str, Any]:
        """필독 확인 통계를 반환한다."""
        total = self._rc_repo.count({"post_id": post_id})
        read_count = self._rc_repo.count({"post_id": post_id, "status": "read"})
        unread_count = self._rc_repo.count({"post_id": post_id, "status": {"$ne": "read"}})
        rate = round(read_count / total * 100, 1) if total > 0 else 0.0

        return {
            "post_id": post_id,
            "total": total,
            "read": read_count,
            "unread": unread_count,
            "rate": rate,
        }

    def send_reminders(self, post_id: str, *, max_reminders: int = 5) -> int:
        """필독 미확인자에게 리마인더를 발송한다.

        BR-BRD-011: 최대 5회까지 리마인더 발송.
        """
        unread = self._rc_repo.find_many(
            {
                "post_id": post_id,
                "status": {"$ne": "read"},
                "reminder_count": {"$lt": max_reminders},
            },
            limit=500,
        )

        now = datetime.now(tz=UTC).isoformat()
        count = 0
        for rc in unread:
            rc_id = rc.get("_id", "")
            self._rc_repo.update_by_id(
                rc_id,
                {
                    "status": "reminded",
                    "reminder_count": rc.get("reminder_count", 0) + 1,
                    "last_reminded_at": now,
                },
            )
            count += 1

        logger.info("필독 리마인더 발송: %s (%d명)", post_id, count)
        return count
