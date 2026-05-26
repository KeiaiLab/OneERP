"""메일 전송 서비스 단위 테스트.

SC-MAIL-001 ~ SC-MAIL-003, EX-MAIL-001 시나리오를 검증한다.
"""

from __future__ import annotations

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_comms_app.mail.services.mail_send_service import MailSendService


class TestMailSendService:
    """MailSendService 테스트."""

    def test_send_message_정상(self, mock_collection) -> None:
        """SC-MAIL-001: 메일 전송 정상 시나리오."""
        svc = MailSendService("T1")
        result = svc.send_message(
            sender_id="user1",
            subject="테스트 메일",
            body="본문입니다",
            recipients=[{"user_id": "user2", "recipient_type": "to"}],
        )
        assert result["status"] == "sent"
        assert result["recipient_count"] == 1
        assert "message_id" in result

    def test_send_message_수신자_없으면_에러(self, mock_collection) -> None:
        """EX-MAIL-001: 수신자 없이 전송 시 에러 [ERR-MAIL-001]."""
        svc = MailSendService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.send_message(
                sender_id="user1",
                subject="테스트",
                recipients=[],
            )
        assert "수신자" in (exc_info.value.detail or "")

    def test_send_message_제목_없으면_에러(self, mock_collection) -> None:
        """EX-MAIL-002: 제목 없이 전송 시 에러 [ERR-MAIL-002]."""
        svc = MailSendService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.send_message(
                sender_id="user1",
                subject="",
                recipients=[{"user_id": "user2", "recipient_type": "to"}],
            )
        assert "제목" in (exc_info.value.detail or "")

    def test_send_message_cc_bcc_포함(self, mock_collection) -> None:
        """CC/BCC 포함 전송 시 전체 수신자 수에 반영된다."""
        svc = MailSendService("T1")
        result = svc.send_message(
            sender_id="user1",
            subject="CC 테스트",
            recipients=[{"user_id": "user2", "recipient_type": "to"}],
            cc=["user3"],
            bcc=["user4"],
        )
        assert result["recipient_count"] == 3

    def test_send_message_수신자별_상태_생성(self, mock_collection) -> None:
        """BR-MAIL-005: 수신자별 상태 레코드가 생성되어야 한다."""
        svc = MailSendService("T1")
        svc.send_message(
            sender_id="user1",
            subject="상태 테스트",
            recipients=[
                {"user_id": "user2", "recipient_type": "to"},
                {"user_id": "user3", "recipient_type": "to"},
            ],
        )
        # 메시지 1건 + 수신자 상태 2건 = insert_one 3회
        assert mock_collection.insert_one.call_count == 3

    def test_reply_message_정상(self, mock_collection) -> None:
        """SC-MAIL-002: 회신 정상 시나리오."""
        mock_collection.find_one.return_value = {
            "_id": "MAIL-2026-00001",
            "subject": "원본 메일",
            "sender_id": "user2",
            "recipients": [{"user_id": "user1", "recipient_type": "to"}],
            "cc": [],
            "thread_id": "MAIL-2026-00001",
            "attachments": [],
            "tenant_id": "T1",
        }
        svc = MailSendService("T1")
        result = svc.reply_message(
            original_message_id="MAIL-2026-00001",
            sender_id="user1",
            body="회신합니다",
        )
        assert result["status"] == "sent"
        assert result["thread_id"] == "MAIL-2026-00001"

    def test_reply_message_원본_없으면_에러(self, mock_collection) -> None:
        """EX-MAIL-001: 원본 메시지 없으면 에러."""
        mock_collection.find_one.return_value = None
        svc = MailSendService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.reply_message(
                original_message_id="INVALID",
                sender_id="user1",
                body="회신",
            )
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_forward_message_정상(self, mock_collection) -> None:
        """SC-MAIL-003: 전달 정상 시나리오."""
        mock_collection.find_one.return_value = {
            "_id": "MAIL-2026-00001",
            "subject": "원본 메일",
            "sender_id": "user1",
            "recipients": [],
            "attachments": [{"file_name": "doc.pdf", "file_url": "/files/doc.pdf"}],
            "thread_id": "MAIL-2026-00001",
            "tenant_id": "T1",
        }
        svc = MailSendService("T1")
        result = svc.forward_message(
            original_message_id="MAIL-2026-00001",
            sender_id="user1",
            forward_to=[{"user_id": "user3", "recipient_type": "to"}],
        )
        assert result["status"] == "sent"

    def test_forward_message_전달대상_없으면_에러(self, mock_collection) -> None:
        """전달 대상 없이 전달 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "MAIL-2026-00001",
            "subject": "원본",
            "sender_id": "user1",
            "attachments": [],
            "thread_id": "MAIL-2026-00001",
            "tenant_id": "T1",
        }
        svc = MailSendService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.forward_message(
                original_message_id="MAIL-2026-00001",
                sender_id="user1",
                forward_to=[],
            )
        assert "수신자" in (exc_info.value.detail or "")

    def test_forward_message_원본_없으면_에러(self, mock_collection) -> None:
        """전달할 원본이 없으면 에러."""
        mock_collection.find_one.return_value = None
        svc = MailSendService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.forward_message(
                original_message_id="INVALID",
                sender_id="user1",
                forward_to=[{"user_id": "user3", "recipient_type": "to"}],
            )
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")
