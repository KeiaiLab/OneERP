"""이벤트 핸들러 단위 테스트.

SC-BRD-011: 결재 완료 → 자동 공지 게시
BR-BRD-015: 자동 공지 게시 규칙 실행
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oneerp_board_app.events.handlers import handle_approval_approved, handle_employee_deactivated


class TestEventHandlers:
    """이벤트 핸들러 테스트."""

    @patch("oneerp_board_app.events.handlers.generate_name", return_value="PST-2026-00001")
    def test_handle_approval_매칭_규칙(self, mock_name, mock_collection) -> None:
        """SC-BRD-011: 결재 완료 시 매칭 규칙으로 자동 공지 생성."""
        # 규칙 조회
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "APR-2026-00001",
                "source_event": "APPROVAL_REQUEST_APPROVED",
                "source_document_type": "PersonnelOrder",
                "target_board_id": "BRD-2026-00001",
                "title_template": "[인사 발령] {employee_name} {new_position} 발령",
                "content_template": "{employee_name}님이 {new_position}으로 발령됨",
                "is_must_read": False,
                "is_active": True,
            },
        ]
        mock_collection.find.return_value = cursor

        handle_approval_approved(
            {
                "tenant_id": "T1",
                "document_type": "PersonnelOrder",
                "document_data": {
                    "employee_name": "홍길동",
                    "new_position": "팀장",
                },
            }
        )

        # 게시글 insert 확인
        mock_collection.insert_one.assert_called_once()
        inserted = mock_collection.insert_one.call_args[0][0]
        assert "홍길동" in inserted["title"]
        assert inserted["source_type"] == "approval_auto"

    def test_handle_approval_문서유형_불일치(self, mock_collection) -> None:
        """소스 문서 유형 불일치 시 게시글 미생성."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "APR-2026-00001",
                "source_event": "APPROVAL_REQUEST_APPROVED",
                "source_document_type": "ExpenseReport",
                "target_board_id": "BRD-2026-00001",
                "title_template": "{title}",
                "content_template": "{content}",
                "is_active": True,
            },
        ]
        mock_collection.find.return_value = cursor

        handle_approval_approved(
            {
                "tenant_id": "T1",
                "document_type": "PersonnelOrder",
                "document_data": {"title": "테스트"},
            }
        )

        mock_collection.insert_one.assert_not_called()

    def test_handle_employee_deactivated(self, mock_collection) -> None:
        """퇴직 직원의 필독/권한 정리."""
        # RC 미확인 조회 (find_many는 sort 없이 호출)
        rc_cursor = MagicMock()
        rc_cursor.skip.return_value.limit.return_value = [
            {"_id": "RC-001", "status": "unread"},
        ]
        # 권한 조회
        perm_cursor = MagicMock()
        perm_cursor.skip.return_value.limit.return_value = [
            {"_id": "BPM-001", "is_active": True},
        ]
        mock_collection.find.side_effect = [rc_cursor, perm_cursor]
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        handle_employee_deactivated(
            {
                "tenant_id": "T1",
                "user_id": "EMP-999",
            }
        )

        # RC + 권한 각각 update
        assert mock_collection.update_one.call_count == 2

    def test_handle_approval_null_document_type(self, mock_collection) -> None:
        """규칙의 source_document_type이 null이면 전체 매칭."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "APR-2026-00001",
                "source_event": "APPROVAL_REQUEST_APPROVED",
                "source_document_type": None,
                "target_board_id": "BRD-2026-00001",
                "title_template": "자동 공지: {title}",
                "content_template": "{content}",
                "is_active": True,
            },
        ]
        mock_collection.find.return_value = cursor

        with patch(
            "oneerp_board_app.events.handlers.generate_name",
            return_value="PST-2026-00001",
        ):
            handle_approval_approved(
                {
                    "tenant_id": "T1",
                    "document_type": "AnyType",
                    "document_data": {"title": "무엇이든", "content": "본문"},
                }
            )

        mock_collection.insert_one.assert_called_once()

    def test_handle_employee_deactivated_빈_user_id(self, mock_collection) -> None:
        """user_id가 비어있으면 아무 작업도 하지 않는다."""
        handle_employee_deactivated({"tenant_id": "T1", "user_id": ""})
        mock_collection.find.assert_not_called()
