"""팝업 공지 서비스 단위 테스트.

SC-BRD-010: 팝업 공지 생성 및 표시
SC-BRD-E009: 팝업 동시 활성 제한 초과
SC-BRD-E010: 팝업 기간 90일 초과
BR-BRD-012: 팝업 공지 기간 검증
BR-BRD-018: 팝업 공지 동시 활성 제한
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_board_app.services.popup_service import PopupService
from oneerp_core.errors import OneERPError


class TestPopupService:
    """PopupService 테스트."""

    def test_create_popup_정상(self, mock_collection) -> None:
        """SC-BRD-010: 팝업 공지 정상 생성."""
        mock_collection.count_documents.return_value = 2

        svc = PopupService("T1")
        result = svc.create_popup(
            {
                "title": "긴급 점검",
                "content": "시스템 점검 안내",
                "priority": "urgent",
                "target": {"target_type": "all"},
                "start_at": "2026-03-28T14:00:00+00:00",
                "end_at": "2026-03-29T06:00:00+00:00",
                "is_active": True,
            }
        )
        assert result["_id"].startswith("POP-")
        mock_collection.insert_one.assert_called_once()

    def test_create_popup_기간_역전(self, mock_collection) -> None:
        """BR-BRD-012: end_at <= start_at."""
        svc = PopupService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_popup(
                {
                    "title": "테스트",
                    "content": "내용",
                    "start_at": "2026-03-29T00:00:00+00:00",
                    "end_at": "2026-03-28T00:00:00+00:00",
                    "is_active": True,
                }
            )
        assert exc_info.value.error == "ERR-BRD-035"

    def test_create_popup_기간_초과(self, mock_collection) -> None:
        """SC-BRD-E010 / BR-BRD-012: 90일 초과."""
        svc = PopupService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_popup(
                {
                    "title": "테스트",
                    "content": "내용",
                    "start_at": "2026-03-01T00:00:00+00:00",
                    "end_at": "2026-07-01T00:00:00+00:00",
                    "is_active": True,
                }
            )
        assert exc_info.value.error == "ERR-BRD-036"

    def test_create_popup_동시활성_초과(self, mock_collection) -> None:
        """SC-BRD-E009 / BR-BRD-018: 6번째 활성 팝업."""
        mock_collection.count_documents.return_value = 5

        svc = PopupService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_popup(
                {
                    "title": "6번째",
                    "content": "내용",
                    "start_at": "2026-03-28T00:00:00+00:00",
                    "end_at": "2026-03-29T00:00:00+00:00",
                    "is_active": True,
                }
            )
        assert exc_info.value.error == "ERR-BRD-040"

    def test_confirm_popup(self, mock_collection) -> None:
        """팝업 확인 처리."""
        mock_collection.find_one.return_value = {
            "_id": "POP-2026-00001",
            "confirmed_count": 5,
            "tenant_id": "T1",
        }
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = cursor
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PopupService("T1")
        result = svc.confirm_popup("POP-2026-00001", "EMP-003")
        assert result["status"] == "confirmed"
        mock_collection.insert_one.assert_called_once()

    def test_get_active_popups(self, mock_collection) -> None:
        """활성 팝업 조회."""
        popup_cursor = MagicMock()
        popup_cursor.skip.return_value.limit.return_value.sort.return_value = [
            {
                "_id": "POP-2026-00001",
                "title": "긴급 안내",
                "show_frequency": "every_login",
                "tenant_id": "T1",
            },
        ]
        mock_collection.find.return_value = popup_cursor

        svc = PopupService("T1")
        result = svc.get_active_popups("EMP-003")
        assert len(result) == 1
