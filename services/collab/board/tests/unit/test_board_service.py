"""게시판 서비스 단위 테스트.

SC-BRD-001: 게시판 생성
SC-BRD-E008: 게시글 있는 게시판 삭제 시도
BR-BRD-001: 게시판명 테넌트 내 유니크
BR-BRD-013: 게시글 존재 시 삭제 불가
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_board_app.services.board_service import BoardService
from oneerp_core.errors import OneERPError


class TestBoardService:
    """BoardService 테스트."""

    def test_create_board_정상(self, mock_collection) -> None:
        """SC-BRD-001: 게시판을 정상 생성한다."""
        # find_many: 중복 검사 → 없음
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor

        svc = BoardService("T1")
        result = svc.create_board(
            {
                "board_name": "전사 공지사항",
                "board_type": "notice",
                "scope": "company",
                "created_by": "admin",
            }
        )

        assert result["board_name"] == "전사 공지사항"
        assert result["_id"].startswith("BRD-")
        # insert 2회: 게시판 + 기본 권한
        assert mock_collection.insert_one.call_count == 2

    def test_create_board_이름_중복(self, mock_collection) -> None:
        """BR-BRD-001: 동일 이름 게시판 생성 시 ERR-BRD-020."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [{"_id": "BRD-2026-00001"}]
        mock_collection.find.return_value = cursor

        svc = BoardService("T1")
        with pytest.raises(OneERPError, match="conflict"):
            svc.create_board({"board_name": "전사 공지사항"})

    def test_get_board_정상(self, mock_collection) -> None:
        """게시판 상세 조회 성공."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "전사 공지사항",
            "tenant_id": "T1",
        }
        svc = BoardService("T1")
        result = svc.get_board("BRD-2026-00001")
        assert result["board_name"] == "전사 공지사항"

    def test_get_board_미존재(self, mock_collection) -> None:
        """ERR-BRD-002: 존재하지 않는 게시판."""
        mock_collection.find_one.return_value = None
        svc = BoardService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.get_board("INVALID")

    def test_update_board_정상(self, mock_collection) -> None:
        """게시판 수정 성공."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "기존 이름",
            "tenant_id": "T1",
        }
        # 이름 중복 검사: 없음
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor

        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = BoardService("T1")
        result = svc.update_board("BRD-2026-00001", {"board_name": "새 이름"})
        assert result["board_name"] == "새 이름"

    def test_update_board_이름_중복(self, mock_collection) -> None:
        """BR-BRD-001: 수정 시 이름 중복 검사."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "기존 이름",
            "tenant_id": "T1",
        }
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [{"_id": "BRD-2026-00002"}]
        mock_collection.find.return_value = cursor

        svc = BoardService("T1")
        with pytest.raises(OneERPError, match="conflict"):
            svc.update_board("BRD-2026-00001", {"board_name": "이미 있는 이름"})

    def test_delete_board_게시글_존재(self, mock_collection) -> None:
        """SC-BRD-E008 / BR-BRD-013: 게시글이 있으면 삭제 불가."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "공지",
            "tenant_id": "T1",
            "docstatus": 0,
        }
        mock_collection.count_documents.return_value = 10

        svc = BoardService("T1")
        with pytest.raises(OneERPError, match="conflict"):
            svc.delete_board("BRD-2026-00001")

    def test_delete_board_빈_게시판(self, mock_collection) -> None:
        """빈 게시판은 정상 삭제."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "빈 게시판",
            "tenant_id": "T1",
            "docstatus": 0,
        }
        mock_collection.count_documents.return_value = 0
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        svc = BoardService("T1")
        result = svc.delete_board("BRD-2026-00001")
        assert result is True

    def test_check_board_active_비활성(self, mock_collection) -> None:
        """ERR-BRD-044: 비활성 게시판 접근 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "is_active": False,
            "tenant_id": "T1",
        }
        svc = BoardService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.check_board_active("BRD-2026-00001")
        assert exc_info.value.error == "ERR-BRD-044"

    @patch("oneerp_board_app.services.board_service.generate_name", return_value="BRD-2026-00001")
    def test_create_board_기본_권한_자동_생성(self, mock_name, mock_collection) -> None:
        """SC-BRD-001: 게시판 생성 시 grantee_type=all, permission=read 자동 생성."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor

        svc = BoardService("T1")
        svc.create_board({"board_name": "테스트", "created_by": "admin"})

        # insert_one 2회: 게시판 + 기본 권한
        assert mock_collection.insert_one.call_count == 2
        # 두 번째 insert가 권한 생성
        perm_data = mock_collection.insert_one.call_args_list[1][0][0]
        assert perm_data["grantee_type"] == "all"
        assert perm_data["permission"] == "read"
