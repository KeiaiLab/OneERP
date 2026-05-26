"""EventService 단위 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """EventService + mock 리포지터리를 생성한다."""
    with patch("oneerp_calendar_app.services.event_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_calendar_app.services.event_service import EventService

        service = EventService(tenant_id="test-tenant")
    return service, repos


class Test캘린더존재확인:
    def test_존재하는_캘린더(self) -> None:
        service, repos = _make_service()
        repos["calendars"].find_by_id.return_value = {
            "_id": "CAL-001",
            "name": "테스트 캘린더",
        }

        result = service.check_calendar_exists("CAL-001")

        assert result["_id"] == "CAL-001"

    def test_존재하지_않는_캘린더_에러(self) -> None:
        service, repos = _make_service()
        repos["calendars"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-CAL-010"):
            service.check_calendar_exists("CAL-999")


class Test이벤트상태전환:
    def test_draft에서_confirmed로_전환(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "status": "draft",
        }

        result = service.change_event_status("CEVT-001", "confirmed")

        assert result["new_status"] == "confirmed"
        assert result["previous_status"] == "draft"
        repos["calendar_events"].update_by_id.assert_called_once()

    def test_confirmed에서_cancelled로_전환(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "status": "confirmed",
        }

        result = service.change_event_status("CEVT-001", "cancelled")

        assert result["new_status"] == "cancelled"

    def test_잘못된_전환_에러(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "status": "cancelled",
        }

        with pytest.raises(ValueError, match="ERR-CAL-014"):
            service.change_event_status("CEVT-001", "confirmed")

    def test_존재하지_않는_이벤트_에러(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-CAL-011"):
            service.change_event_status("CEVT-999", "confirmed")


class Test충돌검사:
    def test_겹치는_이벤트_감지(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["calendar_events"].find_many.return_value = [
            {
                "_id": "CEVT-001",
                "title": "기존 회의",
                "organizer_id": "user-1",
                "start_dt": (now + timedelta(hours=1)).isoformat(),
                "end_dt": (now + timedelta(hours=2)).isoformat(),
                "status": "confirmed",
            },
        ]

        conflicts = service.detect_conflicts(
            "user-1",
            now,
            now + timedelta(hours=3),
        )

        assert len(conflicts) == 1
        assert conflicts[0]["title"] == "기존 회의"

    def test_겹치지_않는_이벤트(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["calendar_events"].find_many.return_value = [
            {
                "_id": "CEVT-001",
                "title": "기존 회의",
                "organizer_id": "user-1",
                "start_dt": (now + timedelta(hours=5)).isoformat(),
                "end_dt": (now + timedelta(hours=6)).isoformat(),
                "status": "confirmed",
            },
        ]

        conflicts = service.detect_conflicts(
            "user-1",
            now,
            now + timedelta(hours=2),
        )

        assert len(conflicts) == 0

    def test_제외_이벤트_ID(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["calendar_events"].find_many.return_value = [
            {
                "_id": "CEVT-001",
                "title": "자기 자신",
                "organizer_id": "user-1",
                "start_dt": now.isoformat(),
                "end_dt": (now + timedelta(hours=1)).isoformat(),
                "status": "confirmed",
            },
        ]

        conflicts = service.detect_conflicts(
            "user-1",
            now,
            now + timedelta(hours=1),
            exclude_event_id="CEVT-001",
        )

        assert len(conflicts) == 0


class Test초대자관리:
    def test_초대자_추가(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "title": "회의",
        }
        repos["invitees"].find_many.return_value = []

        result = service.add_invitee("CEVT-001", "user-2", "김철수", "kim@test.com")

        assert result["user_id"] == "user-2"
        assert result["status"] == "pending"
        repos["invitees"].insert.assert_called_once()

    def test_중복_초대_에러(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
        }
        repos["invitees"].find_many.return_value = [{"_id": "INV-001"}]

        with pytest.raises(ValueError, match="ERR-CAL-021"):
            service.add_invitee("CEVT-001", "user-2")

    def test_초대_응답(self) -> None:
        service, repos = _make_service()
        repos["invitees"].find_many.return_value = [
            {"_id": "INV-001", "event_id": "CEVT-001", "user_id": "user-2"},
        ]

        result = service.respond_to_invite("CEVT-001", "user-2", "accepted", "참석합니다")

        assert result["response_status"] == "accepted"
        repos["invitees"].update_by_id.assert_called_once()

    def test_초대_없는_응답_에러(self) -> None:
        service, repos = _make_service()
        repos["invitees"].find_many.return_value = []

        with pytest.raises(ValueError, match="ERR-CAL-022"):
            service.respond_to_invite("CEVT-001", "user-unknown", "accepted")

    def test_유효하지_않은_응답_상태(self) -> None:
        service, repos = _make_service()
        repos["invitees"].find_many.return_value = [
            {"_id": "INV-001", "event_id": "CEVT-001", "user_id": "user-2"},
        ]

        with pytest.raises(ValueError, match="ERR-CAL-022"):
            service.respond_to_invite("CEVT-001", "user-2", "invalid_status")


class Test반복이벤트:
    def test_일간_반복_생성(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "calendar_id": "CAL-001",
            "title": "일일 스탠드업",
            "description": "",
            "event_type": "meeting",
            "start_dt": now.isoformat(),
            "end_dt": (now + timedelta(hours=1)).isoformat(),
            "all_day": False,
            "location": "",
            "organizer_id": "user-1",
            "recurrence_frequency": "daily",
            "recurrence_interval": 1,
            "recurrence_count": 3,
            "recurrence_end_date": None,
        }

        result = service.generate_recurring_events("CEVT-001")

        assert len(result) == 3
        assert repos["calendar_events"].insert.call_count == 3

    def test_반복_규칙_없는_이벤트_에러(self) -> None:
        service, repos = _make_service()
        repos["calendar_events"].find_by_id.return_value = {
            "_id": "CEVT-001",
            "recurrence_frequency": None,
            "start_dt": datetime.now(tz=UTC).isoformat(),
            "end_dt": (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat(),
        }

        with pytest.raises(ValueError, match="ERR-CAL-013"):
            service.generate_recurring_events("CEVT-001")
