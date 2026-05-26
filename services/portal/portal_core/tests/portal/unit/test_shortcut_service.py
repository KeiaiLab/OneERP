"""바로가기 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_core_app.portal.services.shortcut_service import ShortcutService


class TestShortcutService:
    """ShortcutService 테스트."""

    def test_바로가기_생성_정상(self, mock_collection: MagicMock) -> None:
        """바로가기를 정상적으로 생성한다."""
        mock_collection.count_documents.return_value = 5
        mock_collection.insert_one.return_value = MagicMock(inserted_id="SCUT-2026-00001")

        svc = ShortcutService("T1")
        result = svc.create_shortcut(
            user_id="user1",
            shortcut_name="대시보드",
            url="/dashboard",
            icon="home",
        )

        assert result["shortcut_name"] == "대시보드"
        assert result["url"] == "/dashboard"
        assert result["click_count"] == 0

    def test_바로가기_20개_초과_에러(self, mock_collection: MagicMock) -> None:
        """BR-PTL-003: 20개 초과 시 에러 (ERR-PTL-003)."""
        mock_collection.count_documents.return_value = 20

        svc = ShortcutService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_shortcut(
                user_id="user1",
                shortcut_name="추가 바로가기",
                url="/extra",
            )
        assert "ERR-PTL-003" in (exc_info.value.detail or "")

    def test_클릭_추적(self, mock_collection: MagicMock) -> None:
        """클릭 수가 증가한다."""
        mock_collection.find_one.return_value = {
            "_id": "SCUT-2026-00001",
            "user_id": "user1",
            "click_count": 5,
            "url": "/dashboard",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = ShortcutService("T1")
        result = svc.track_click("SCUT-2026-00001", "user1")

        assert result["click_count"] == 6

    def test_다른_사용자_바로가기_클릭_에러(self, mock_collection: MagicMock) -> None:
        """다른 사용자의 바로가기에 접근 시 에러 (ERR-PTL-009)."""
        mock_collection.find_one.return_value = {
            "_id": "SCUT-2026-00001",
            "user_id": "other_user",
            "tenant_id": "T1",
        }

        svc = ShortcutService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.track_click("SCUT-2026-00001", "user1")
        assert "ERR-PTL-009" in (exc_info.value.detail or "")

    def test_존재하지_않는_바로가기_404(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 바로가기 클릭 시 404 (ERR-PTL-008)."""
        mock_collection.find_one.return_value = None

        svc = ShortcutService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.track_click("NONEXISTENT", "user1")
        assert exc_info.value.status_code == 404
        assert "ERR-PTL-008" in (exc_info.value.detail or "")

    def test_바로가기_삭제(self, mock_collection: MagicMock) -> None:
        """바로가기를 정상적으로 삭제한다."""
        mock_collection.find_one.return_value = {
            "_id": "SCUT-2026-00001",
            "user_id": "user1",
            "docstatus": 0,
            "tenant_id": "T1",
        }
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        svc = ShortcutService("T1")
        svc.delete_shortcut("SCUT-2026-00001", "user1")

    def test_바로가기_목록_조회(self, mock_collection: MagicMock) -> None:
        """사용자의 바로가기 목록을 정렬 순서대로 반환한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value.sort.return_value = [
            {"_id": "SCUT-1", "shortcut_name": "홈", "sort_order": 0},
            {"_id": "SCUT-2", "shortcut_name": "설정", "sort_order": 1},
        ]
        mock_collection.find.return_value = cursor

        svc = ShortcutService("T1")
        result = svc.get_user_shortcuts("user1")

        assert len(result) == 2
