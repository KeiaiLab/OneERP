"""메일 조회 서비스 단위 테스트.

SC-MAIL-030 ~ SC-MAIL-032, EX-MAIL-030 ~ EX-MAIL-031 시나리오를 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_comms_app.mail.services.mail_read_service import MailReadService


class TestMailReadService:
    """MailReadService 테스트."""

    def test_read_message_정상(self, mock_collection) -> None:
        """SC-MAIL-030: 메일 읽기 정상 시나리오."""
        mock_collection.find_one.return_value = {
            "_id": "MAIL-2026-00001",
            "subject": "테스트",
            "tenant_id": "T1",
        }
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "status": "unread"},
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailReadService("T1")
        result = svc.read_message(message_id="MAIL-2026-00001", user_id="user1")
        assert result["subject"] == "테스트"
        mock_collection.update_one.assert_called_once()

    def test_read_message_이미_읽음(self, mock_collection) -> None:
        """이미 읽은 메시지는 update하지 않는다."""
        mock_collection.find_one.return_value = {
            "_id": "MAIL-2026-00001",
            "subject": "테스트",
            "tenant_id": "T1",
        }
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "status": "read"},
        ]
        mock_collection.find.return_value = mock_cursor

        svc = MailReadService("T1")
        svc.read_message(message_id="MAIL-2026-00001", user_id="user1")
        mock_collection.update_one.assert_not_called()

    def test_read_message_존재하지_않으면_에러(self, mock_collection) -> None:
        """EX-MAIL-030: 메시지가 없으면 에러."""
        mock_collection.find_one.return_value = None

        svc = MailReadService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.read_message(message_id="INVALID", user_id="user1")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_mark_as_unread(self, mock_collection) -> None:
        """안읽음 표시 정상."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "status": "read"},
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailReadService("T1")
        result = svc.mark_as_unread(message_id="MAIL-2026-00001", user_id="user1")
        assert result["status"] == "unread"

    def test_mark_as_unread_상태_없으면_에러(self, mock_collection) -> None:
        """수신 상태가 없으면 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailReadService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.mark_as_unread(message_id="INVALID", user_id="user1")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_get_thread(self, mock_collection) -> None:
        """SC-MAIL-031: 스레드 조회 정상 시나리오."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value.sort.return_value = [
            {"_id": "MAIL-2026-00001", "thread_id": "T001"},
            {"_id": "MAIL-2026-00002", "thread_id": "T001"},
        ]
        mock_collection.find.return_value = mock_cursor

        svc = MailReadService("T1")
        result = svc.get_thread(thread_id="T001")
        assert len(result) == 2

    def test_toggle_star(self, mock_collection) -> None:
        """즐겨찾기 토글 정상."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "is_starred": False},
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailReadService("T1")
        result = svc.toggle_star(message_id="MAIL-2026-00001", user_id="user1")
        assert result["is_starred"] is True

    def test_toggle_star_상태_없으면_에러(self, mock_collection) -> None:
        """수신 상태가 없으면 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailReadService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.toggle_star(message_id="INVALID", user_id="user1")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_delete_message_정상(self, mock_collection) -> None:
        """BR-MAIL-031: 수신자 삭제(소프트) 정상 시나리오."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "status": "read"},
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailReadService("T1")
        result = svc.delete_message(message_id="MAIL-2026-00001", user_id="user1")
        assert result["deleted"] is True

    def test_delete_message_상태_없으면_에러(self, mock_collection) -> None:
        """EX-MAIL-031: 수신 상태 없으면 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailReadService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.delete_message(message_id="INVALID", user_id="user1")
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")
