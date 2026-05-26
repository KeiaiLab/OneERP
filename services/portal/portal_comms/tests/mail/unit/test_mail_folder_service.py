"""메일 폴더 서비스 단위 테스트.

SC-MAIL-010 ~ SC-MAIL-011, EX-MAIL-010 ~ EX-MAIL-012 시나리오를 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_comms_app.mail.services.mail_folder_service import MailFolderService


class TestMailFolderService:
    """MailFolderService 테스트."""

    def test_create_folder_정상(self, mock_collection) -> None:
        """SC-MAIL-010: 사용자 폴더 생성 정상 시나리오."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailFolderService("T1")
        result = svc.create_folder(owner_id="user1", name="프로젝트")
        assert "folder_id" in result
        assert result["name"] == "프로젝트"
        assert result["depth"] == 0

    def test_create_folder_이름_중복_에러(self, mock_collection) -> None:
        """EX-MAIL-011: 폴더명 중복 시 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MFLD-2026-00001", "name": "프로젝트"},
        ]
        mock_collection.find.return_value = mock_cursor

        svc = MailFolderService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_folder(owner_id="user1", name="프로젝트")
        assert "이미 존재합니다" in (exc_info.value.detail or "")

    def test_create_folder_계층_초과_에러(self, mock_collection) -> None:
        """EX-MAIL-012: 폴더 계층 3단계 초과 시 에러."""
        # find_many: 중복 검증 -> 없음
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor
        # find_by_id: 상위 폴더 조회 -> depth=3
        mock_collection.find_one.return_value = {
            "_id": "MFLD-2026-00003",
            "depth": 3,
            "tenant_id": "T1",
        }

        svc = MailFolderService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_folder(
                owner_id="user1",
                name="하위폴더",
                parent_folder_id="MFLD-2026-00003",
            )
        assert "최대" in (exc_info.value.detail or "")

    def test_delete_folder_정상(self, mock_collection) -> None:
        """폴더 삭제 정상 시나리오."""
        mock_collection.find_one.return_value = {
            "_id": "MFLD-2026-00001",
            "name": "프로젝트",
            "owner_id": "user1",
            "is_system": False,
            "docstatus": 0,
            "tenant_id": "T1",
        }
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        svc = MailFolderService("T1")
        result = svc.delete_folder(folder_id="MFLD-2026-00001", owner_id="user1")
        assert result["deleted"] is True

    def test_delete_folder_시스템폴더_에러(self, mock_collection) -> None:
        """EX-MAIL-010: 시스템 폴더 삭제 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "MFLD-2026-00001",
            "name": "inbox",
            "owner_id": "user1",
            "is_system": True,
            "tenant_id": "T1",
        }

        svc = MailFolderService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.delete_folder(folder_id="MFLD-2026-00001", owner_id="user1")
        assert "시스템 폴더" in (exc_info.value.detail or "")

    def test_delete_folder_타인_소유_에러(self, mock_collection) -> None:
        """다른 사용자의 폴더 삭제 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "MFLD-2026-00001",
            "name": "프로젝트",
            "owner_id": "user2",
            "is_system": False,
            "tenant_id": "T1",
        }

        svc = MailFolderService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.delete_folder(folder_id="MFLD-2026-00001", owner_id="user1")
        assert "본인 소유" in (exc_info.value.detail or "")

    def test_move_message_정상(self, mock_collection) -> None:
        """SC-MAIL-011: 폴더간 메일 이동 정상 시나리오."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MRST-2026-00001", "message_id": "MAIL-2026-00001", "folder": "inbox"},
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailFolderService("T1")
        result = svc.move_message(
            user_id="user1",
            message_id="MAIL-2026-00001",
            target_folder="프로젝트",
        )
        assert result["to_folder"] == "프로젝트"
        assert result["from_folder"] == "inbox"

    def test_move_message_상태_없으면_에러(self, mock_collection) -> None:
        """메시지 수신 상태가 없으면 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailFolderService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.move_message(
                user_id="user1",
                message_id="INVALID",
                target_folder="프로젝트",
            )
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_get_user_folders(self, mock_collection) -> None:
        """사용자 폴더 목록 조회."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MFLD-2026-00001", "name": "프로젝트"},
        ]
        mock_collection.find.return_value = mock_cursor

        svc = MailFolderService("T1")
        result = svc.get_user_folders(owner_id="user1")
        assert len(result) == 1
