"""상호작용 서비스 단위 테스트.

SC-BRD-004: 필독 확인
SC-BRD-009: 좋아요 토글
SC-BRD-014: 북마크 토글
SC-BRD-015: 게시글 신고
SC-BRD-E012: 중복 신고
BR-BRD-014: 좋아요/북마크 중복 방지
BR-BRD-019: 신고 중복 방지
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_board_app.services.interaction_service import InteractionService
from oneerp_core.errors import OneERPError


class TestInteractionService:
    """InteractionService 테스트."""

    def test_toggle_like_추가(self, mock_collection) -> None:
        """SC-BRD-009: 좋아요 추가."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "like_count": 24,
            "tenant_id": "T1",
        }
        # 기존 좋아요 없음
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        result = svc.toggle_like("PST-2026-00001", "EMP-003")
        assert result["liked"] is True
        assert result["like_count"] == 25

    def test_toggle_like_취소(self, mock_collection) -> None:
        """SC-BRD-009: 좋아요 취소 (토글)."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "like_count": 25,
            "tenant_id": "T1",
            "docstatus": 0,
        }
        # 기존 좋아요 존재
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "LK-2026-00001", "docstatus": 0},
        ]
        mock_collection.find.return_value = cursor
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        result = svc.toggle_like("PST-2026-00001", "EMP-003")
        assert result["liked"] is False
        assert result["like_count"] == 24

    def test_toggle_bookmark_추가(self, mock_collection) -> None:
        """SC-BRD-014: 북마크 추가."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "bookmark_count": 7,
            "tenant_id": "T1",
        }
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        result = svc.toggle_bookmark("PST-2026-00001", "EMP-003")
        assert result["bookmarked"] is True
        assert result["bookmark_count"] == 8

    def test_toggle_bookmark_취소(self, mock_collection) -> None:
        """SC-BRD-014: 북마크 취소 (토글)."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "bookmark_count": 8,
            "tenant_id": "T1",
            "docstatus": 0,
        }
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "BM-2026-00001", "docstatus": 0},
        ]
        mock_collection.find.return_value = cursor
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        result = svc.toggle_bookmark("PST-2026-00001", "EMP-003")
        assert result["bookmarked"] is False
        assert result["bookmark_count"] == 7

    def test_create_report_정상(self, mock_collection) -> None:
        """SC-BRD-015: 게시글 신고 정상 접수."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor

        svc = InteractionService("T1")
        result = svc.create_report(
            {
                "post_id": "PST-2026-00001",
                "reporter_id": "EMP-003",
                "reason": "inappropriate",
                "description": "부적절한 내용",
            }
        )
        assert result["status"] == "pending"
        mock_collection.insert_one.assert_called_once()

    def test_create_report_중복(self, mock_collection) -> None:
        """SC-BRD-E012 / BR-BRD-019: 중복 신고."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [{"_id": "RPT-2026-00001"}]
        mock_collection.find.return_value = cursor

        svc = InteractionService("T1")
        with pytest.raises(OneERPError, match="conflict"):
            svc.create_report(
                {
                    "post_id": "PST-2026-00001",
                    "reporter_id": "EMP-003",
                    "reason": "spam",
                }
            )

    def test_confirm_read_정상(self, mock_collection) -> None:
        """SC-BRD-004: 필독 확인 처리."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "RC-2026-00001",
                "post_id": "PST-2026-00001",
                "user_id": "EMP-003",
                "status": "unread",
                "tenant_id": "T1",
            },
        ]
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        result = svc.confirm_read("PST-2026-00001", "EMP-003")
        assert result["status"] == "read"
        assert result["read_at"] is not None

    def test_confirm_read_이미_확인(self, mock_collection) -> None:
        """필독 이미 확인 — 멱등 처리."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "RC-2026-00001",
                "status": "read",
                "read_at": "2026-03-28T10:00:00",
                "tenant_id": "T1",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = InteractionService("T1")
        result = svc.confirm_read("PST-2026-00001", "EMP-003")
        assert result["status"] == "read"
        # update_one 호출하지 않음 (멱등)
        mock_collection.update_one.assert_not_called()

    def test_confirm_read_비대상자(self, mock_collection) -> None:
        """ERR-BRD-045: 필독 대상이 아닌 사용자."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor

        svc = InteractionService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.confirm_read("PST-2026-00001", "EMP-999")

    def test_get_read_confirm_stats(self, mock_collection) -> None:
        """필독 확인 통계."""
        mock_collection.count_documents.side_effect = [100, 72, 28]

        svc = InteractionService("T1")
        result = svc.get_read_confirm_stats("PST-2026-00001")
        assert result["total"] == 100
        assert result["read"] == 72
        assert result["rate"] == 72.0

    def test_send_reminders(self, mock_collection) -> None:
        """BR-BRD-011: 필독 리마인더 발송."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "RC-001", "reminder_count": 1, "status": "unread"},
            {"_id": "RC-002", "reminder_count": 0, "status": "unread"},
        ]
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = InteractionService("T1")
        count = svc.send_reminders("PST-2026-00001")
        assert count == 2

    def test_toggle_like_미존재_게시글(self, mock_collection) -> None:
        """좋아요 시 게시글 없으면 404."""
        mock_collection.find_one.return_value = None

        svc = InteractionService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.toggle_like("INVALID", "EMP-001")
