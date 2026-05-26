"""댓글 서비스 단위 테스트.

SC-BRD-007: 댓글/대댓글 작성
SC-BRD-E006: 대댓글 깊이 초과
SC-BRD-E015: 삭제된 게시글에 댓글 시도
BR-BRD-008: 댓글 깊이 제한
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_board_app.services.comment_service import CommentService
from oneerp_core.errors import OneERPError


class TestCommentService:
    """CommentService 테스트."""

    def test_create_comment_정상(self, mock_collection) -> None:
        """SC-BRD-007: 댓글 정상 작성 (depth=0)."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "status": "published",
            "comment_count": 5,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = CommentService("T1")
        result = svc.create_comment(
            "PST-2026-00001",
            {
                "content": "좋은 공지 감사합니다.",
                "author_id": "EMP-003",
                "author_name": "박사원",
            },
        )
        assert result["depth"] == 0
        assert result["_id"].startswith("CMT-")
        mock_collection.insert_one.assert_called_once()

    def test_create_reply_depth1(self, mock_collection) -> None:
        """SC-BRD-007: 대댓글 작성 (depth=1)."""
        # find_one: 첫 호출 → 게시글, 두 번째 → 부모 댓글
        mock_collection.find_one.side_effect = [
            {
                "_id": "PST-2026-00001",
                "status": "published",
                "comment_count": 5,
                "tenant_id": "T1",
            },
            {
                "_id": "CMT-2026-00001",
                "post_id": "PST-2026-00001",
                "depth": 0,
                "tenant_id": "T1",
            },
            # update를 위한 find
            {
                "_id": "PST-2026-00001",
                "status": "published",
                "comment_count": 5,
                "tenant_id": "T1",
            },
        ]
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = CommentService("T1")
        result = svc.create_comment(
            "PST-2026-00001",
            {
                "content": "답글입니다.",
                "parent_id": "CMT-2026-00001",
                "author_id": "EMP-001",
            },
        )
        assert result["depth"] == 1

    def test_create_reply_depth_exceed(self, mock_collection) -> None:
        """SC-BRD-E006 / BR-BRD-008: depth=3 댓글에 대댓글 시 422."""
        mock_collection.find_one.side_effect = [
            {
                "_id": "PST-2026-00001",
                "status": "published",
                "tenant_id": "T1",
            },
            {
                "_id": "CMT-2026-00100",
                "post_id": "PST-2026-00001",
                "depth": 3,
                "tenant_id": "T1",
            },
        ]

        svc = CommentService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_comment(
                "PST-2026-00001",
                {
                    "content": "너무 깊은 대댓글",
                    "parent_id": "CMT-2026-00100",
                },
            )
        assert exc_info.value.error == "ERR-BRD-033"

    def test_create_comment_삭제된_게시글(self, mock_collection) -> None:
        """SC-BRD-E015: 삭제된 게시글에 댓글 시 404."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "status": "deleted",
            "tenant_id": "T1",
        }

        svc = CommentService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.create_comment("PST-2026-00001", {"content": "댓글"})

    def test_create_comment_부모_다른_게시글(self, mock_collection) -> None:
        """ERR-BRD-043: 부모 댓글이 다른 게시글에 속한 경우."""
        mock_collection.find_one.side_effect = [
            {
                "_id": "PST-2026-00001",
                "status": "published",
                "tenant_id": "T1",
            },
            {
                "_id": "CMT-2026-00001",
                "post_id": "PST-2026-00002",  # 다른 게시글
                "depth": 0,
                "tenant_id": "T1",
            },
        ]

        svc = CommentService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_comment(
                "PST-2026-00001",
                {
                    "content": "잘못된 부모",
                    "parent_id": "CMT-2026-00001",
                },
            )
        assert exc_info.value.error == "ERR-BRD-043"

    def test_delete_comment_대댓글_있음(self, mock_collection) -> None:
        """대댓글이 있는 댓글 삭제 시 내용만 변경."""
        mock_collection.find_one.side_effect = [
            {
                "_id": "CMT-2026-00001",
                "post_id": "PST-2026-00001",
                "is_deleted": False,
                "tenant_id": "T1",
                "docstatus": 0,
            },
            # 게시글 조회 (댓글 수 감소용)
            {
                "_id": "PST-2026-00001",
                "comment_count": 5,
                "tenant_id": "T1",
            },
        ]
        # 대댓글 존재 여부
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [{"_id": "CMT-2026-00002"}]
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = CommentService("T1")
        result = svc.delete_comment("CMT-2026-00001")
        assert result is True

    def test_get_comments(self, mock_collection) -> None:
        """게시글별 댓글 목록 조회."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value.sort.return_value = [
            {"_id": "CMT-2026-00001", "content": "댓글1"},
            {"_id": "CMT-2026-00002", "content": "댓글2"},
        ]
        mock_collection.find.return_value = cursor

        svc = CommentService("T1")
        result = svc.get_comments("PST-2026-00001")
        assert len(result) == 2
