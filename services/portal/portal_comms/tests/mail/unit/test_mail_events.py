"""메일 이벤트 핸들러 단위 테스트."""

from __future__ import annotations

from oneerp_portal_comms_app.mail.events.handlers import (
    handle_approval_approved,
    handle_approval_rejected,
)


class TestMailEventHandlers:
    """이벤트 핸들러 테스트."""

    def test_approval_approved_정상(self, mock_collection) -> None:
        """결재 승인 시 알림 메일이 발송된다."""
        handle_approval_approved(
            {
                "requester_id": "user1",
                "doc_id": "DOC-2026-00001",
                "tenant_id": "T1",
            }
        )
        # 메시지 1건 + 수신자 상태 1건 = 2회 insert
        assert mock_collection.insert_one.call_count == 2

    def test_approval_approved_요청자_없으면_스킵(self, mock_collection) -> None:
        """요청자 ID가 없으면 메일 발송하지 않는다."""
        handle_approval_approved(
            {
                "doc_id": "DOC-2026-00001",
                "tenant_id": "T1",
            }
        )
        mock_collection.insert_one.assert_not_called()

    def test_approval_rejected_정상(self, mock_collection) -> None:
        """결재 거부 시 알림 메일이 발송된다."""
        handle_approval_rejected(
            {
                "requester_id": "user1",
                "doc_id": "DOC-2026-00001",
                "tenant_id": "T1",
            }
        )
        assert mock_collection.insert_one.call_count == 2

    def test_approval_rejected_요청자_없으면_스킵(self, mock_collection) -> None:
        """요청자 ID가 없으면 메일 발송하지 않는다."""
        handle_approval_rejected(
            {
                "doc_id": "DOC-2026-00001",
                "tenant_id": "T1",
            }
        )
        mock_collection.insert_one.assert_not_called()
