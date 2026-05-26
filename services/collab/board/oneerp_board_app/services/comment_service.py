"""댓글 관리 서비스 — 댓글/대댓글 CRUD.

BR-BRD-008: 댓글 깊이 제한 (최대 3단계)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 대댓글 최대 깊이
MAX_COMMENT_DEPTH = 3


class CommentService:
    """댓글 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._comment_repo = Repository("comments", tenant_id=tenant_id)
        self._post_repo = Repository("posts", tenant_id=tenant_id)

    def create_comment(
        self,
        post_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """댓글을 생성한다.

        BR-BRD-008: 대댓글 최대 깊이는 3.
        ERR-BRD-003: 삭제된 게시글에 댓글 불가.
        ERR-BRD-043: 부모 댓글이 동일 게시글에 속해야 함.
        """
        # 게시글 존재/상태 확인
        post = self._post_repo.find_by_id(post_id)
        if not post or post.get("status") == "deleted":
            raise_not_found("ERR-BRD-003: 게시글을 찾을 수 없습니다")

        depth = 0
        parent_id = data.get("parent_id")

        if parent_id:
            parent = self._comment_repo.find_by_id(parent_id)
            if not parent:
                raise_not_found("ERR-BRD-004: 댓글을 찾을 수 없습니다")

            # ERR-BRD-043: 부모 댓글이 동일 게시글에 속하는지 확인
            if parent.get("post_id") != post_id:
                raise_unprocessable(
                    "ERR-BRD-043",
                    "대댓글의 부모 댓글이 동일 게시글에 속하지 않습니다",
                )

            parent_depth = parent.get("depth", 0)
            # BR-BRD-008: 깊이 제한
            if parent_depth >= MAX_COMMENT_DEPTH:
                raise_unprocessable(
                    "ERR-BRD-033",
                    f"대댓글은 최대 {MAX_COMMENT_DEPTH}단계까지 가능합니다",
                )
            depth = parent_depth + 1

        comment_id = generate_name("CMT", tenant_id=self._tenant_id)
        data["_id"] = comment_id
        data["post_id"] = post_id
        data["depth"] = depth
        data["tenant_id"] = self._tenant_id

        self._comment_repo.insert(data)

        # 게시글 댓글 수 증가
        self._post_repo.update_by_id(
            post_id,
            {"comment_count": post.get("comment_count", 0) + 1},
        )

        logger.info("댓글 생성: %s (게시글: %s, depth: %d)", comment_id, post_id, depth)
        return {"_id": comment_id, "post_id": post_id, "depth": depth}

    def delete_comment(self, comment_id: str) -> bool:
        """댓글을 소프트 삭제한다.

        대댓글이 있는 경우 is_deleted=true, content="삭제된 댓글"로 표시.
        """
        comment = self._comment_repo.find_by_id(comment_id)
        if not comment:
            raise_not_found("ERR-BRD-004: 댓글을 찾을 수 없습니다")

        # 대댓글 존재 여부 확인
        children = self._comment_repo.find_many(
            {"parent_id": comment_id},
            limit=1,
        )
        if children:
            # 대댓글 보존을 위해 내용만 변경
            self._comment_repo.update_by_id(
                comment_id,
                {
                    "is_deleted": True,
                    "content": "삭제된 댓글입니다.",
                    "deleted_at": datetime.now(tz=UTC).isoformat(),
                },
            )
        else:
            self._comment_repo.update_by_id(
                comment_id,
                {
                    "is_deleted": True,
                    "deleted_at": datetime.now(tz=UTC).isoformat(),
                },
            )

        # 게시글 댓글 수 감소
        post_id = comment.get("post_id", "")
        post = self._post_repo.find_by_id(post_id)
        if post:
            new_count = max(0, post.get("comment_count", 0) - 1)
            self._post_repo.update_by_id(post_id, {"comment_count": new_count})

        logger.info("댓글 삭제: %s", comment_id)
        return True

    def get_comments(self, post_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """게시글의 댓글 목록을 조회한다."""
        return self._comment_repo.find_many(
            {"post_id": post_id, "is_deleted": {"$ne": True}},
            sort=[("created_at", 1)],
            limit=limit,
        )
