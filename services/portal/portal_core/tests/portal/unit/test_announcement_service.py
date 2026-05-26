"""공지사항 서비스 단위 테스트.

SC-PTL-006~008: 공지사항 상태 전이, 필수/긴급 공지 테스트.
EX-PTL-006~010: 에러 케이스 테스트.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_core_app.portal.services.announcement_service import AnnouncementService


class TestAnnouncementService:
    """AnnouncementService 테스트."""

    def test_공지사항_활성화(self, mock_collection: MagicMock) -> None:
        """SC-PTL-006: draft 공지를 active로 전이한다."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "draft",
            "priority": "normal",
            "title": "테스트 공지",
            "tenant_id": "T1",
        }
        mock_collection.count_documents.return_value = 0
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = AnnouncementService("T1")
        result = svc.publish_announcement("ANN-2026-00001", published_by="admin")

        assert result["status"] == "active"
        assert result.get("published_by") == "admin"

    def test_공지사항_만료(self, mock_collection: MagicMock) -> None:
        """SC-PTL-007: active 공지를 expired로 전이한다."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "active",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = AnnouncementService("T1")
        result = svc.expire_announcement("ANN-2026-00001")

        assert result["status"] == "expired"

    def test_공지사항_보관(self, mock_collection: MagicMock) -> None:
        """SC-PTL-008: expired 공지를 archived로 전이한다."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "expired",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = AnnouncementService("T1")
        result = svc.archive_announcement("ANN-2026-00001")

        assert result["status"] == "archived"

    def test_잘못된_상태_전이(self, mock_collection: MagicMock) -> None:
        """EX-PTL-006: draft에서 직접 expired로 전이 불가 (ERR-PTL-007)."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "draft",
            "tenant_id": "T1",
        }

        svc = AnnouncementService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.expire_announcement("ANN-2026-00001")
        assert "ERR-PTL-007" in (exc_info.value.detail or "")

    def test_보관_상태에서_전이_불가(self, mock_collection: MagicMock) -> None:
        """EX-PTL-007: archived 상태에서는 어떤 전이도 불가."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "archived",
            "tenant_id": "T1",
        }

        svc = AnnouncementService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.publish_announcement("ANN-2026-00001")
        assert "ERR-PTL-007" in (exc_info.value.detail or "")

    def test_필수_공지_숨기기_불가(self, mock_collection: MagicMock) -> None:
        """EX-PTL-008: 필수 공지는 숨길 수 없다 (BR-PTL-004, ERR-PTL-004)."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "active",
            "is_mandatory": True,
            "tenant_id": "T1",
        }

        svc = AnnouncementService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.hide_announcement_for_today("ANN-2026-00001", "user1")
        assert "ERR-PTL-004" in (exc_info.value.detail or "")

    def test_긴급_공지_초과_경고(self, mock_collection: MagicMock) -> None:
        """EX-PTL-009: 동시 긴급 공지 3건 초과 시 경고 포함 (BR-PTL-011)."""
        mock_collection.find_one.return_value = {
            "_id": "ANN-2026-00001",
            "status": "draft",
            "priority": "urgent",
            "tenant_id": "T1",
        }
        # 이미 3건의 긴급 공지 활성
        mock_collection.count_documents.return_value = 3
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = AnnouncementService("T1")
        result = svc.publish_announcement("ANN-2026-00001")

        assert "_warning" in result
        assert "ERR-PTL-011" in result["_warning"]

    def test_활성_공지_목록_조회(self, mock_collection: MagicMock) -> None:
        """SC-PTL-008: 활성 공지를 가져오고 긴급 공지가 최상단에 위치한다."""
        now = datetime.now(tz=UTC)
        active_announcements = [
            {
                "_id": "ANN-1",
                "status": "active",
                "priority": "normal",
                "is_mandatory": False,
                "target_departments": [],
                "target_roles": [],
                "start_date": now - timedelta(days=1),
                "end_date": now + timedelta(days=1),
                "tenant_id": "T1",
            },
            {
                "_id": "ANN-2",
                "status": "active",
                "priority": "urgent",
                "is_mandatory": False,
                "target_departments": [],
                "target_roles": [],
                "start_date": now - timedelta(days=1),
                "end_date": now + timedelta(days=1),
                "tenant_id": "T1",
            },
        ]

        # find for announcements
        cursor_active = MagicMock()
        cursor_active.skip.return_value.limit.return_value = active_announcements
        # find for reads
        cursor_reads = MagicMock()
        cursor_reads.skip.return_value.limit.return_value = []

        mock_collection.find.side_effect = [cursor_active, cursor_reads]

        svc = AnnouncementService("T1")
        result = svc.get_active_announcements("user1")

        assert len(result) == 2
        # 긴급 공지가 첫 번째 (BR-PTL-006)
        assert result[0]["priority"] == "urgent"

    def test_존재하지_않는_공지사항_404(self, mock_collection: MagicMock) -> None:
        """EX-PTL-010: 존재하지 않는 공지사항 조회 시 404."""
        mock_collection.find_one.return_value = None

        svc = AnnouncementService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.publish_announcement("NONEXISTENT")
        assert exc_info.value.status_code == 404
        assert "ERR-PTL-005" in (exc_info.value.detail or "")

    def test_필수_공지_필터링_시_항상_표시(self, mock_collection: MagicMock) -> None:
        """BR-PTL-004: 필수 공지는 숨김 처리되어도 항상 표시된다."""
        now = datetime.now(tz=UTC)
        mandatory_ann = {
            "_id": "ANN-M1",
            "status": "active",
            "priority": "high",
            "is_mandatory": True,
            "target_departments": [],
            "target_roles": [],
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=1),
            "tenant_id": "T1",
        }

        cursor_active = MagicMock()
        cursor_active.skip.return_value.limit.return_value = [mandatory_ann]
        # 읽음 기록에 hide_until이 있어도 무시
        cursor_reads = MagicMock()
        cursor_reads.skip.return_value.limit.return_value = [
            {
                "announcement_id": "ANN-M1",
                "user_id": "user1",
                "hide_until": now + timedelta(hours=12),
            },
        ]

        mock_collection.find.side_effect = [cursor_active, cursor_reads]

        svc = AnnouncementService("T1")
        result = svc.get_active_announcements("user1")

        assert len(result) == 1
        assert result[0]["_id"] == "ANN-M1"
        assert result[0]["_display_mode"] == "mandatory"
