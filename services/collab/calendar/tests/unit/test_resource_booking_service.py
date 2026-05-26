"""ResourceBookingService 단위 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_service() -> tuple:
    """ResourceBookingService + mock 리포지터리를 생성한다."""
    with patch("oneerp_calendar_app.services.resource_booking_service.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_calendar_app.services.resource_booking_service import ResourceBookingService

        service = ResourceBookingService(tenant_id="test-tenant")
    return service, repos


class Test자원가용성:
    def test_사용가능한_자원(self) -> None:
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "CRES-001",
            "name": "회의실A",
            "status": "available",
        }

        result = service.check_resource_available("CRES-001")

        assert result["name"] == "회의실A"

    def test_존재하지_않는_자원_에러(self) -> None:
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-CAL-040"):
            service.check_resource_available("CRES-999")

    def test_유지보수_중인_자원_에러(self) -> None:
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "CRES-001",
            "name": "회의실A",
            "status": "maintenance",
        }

        with pytest.raises(ValueError, match="ERR-CAL-053"):
            service.check_resource_available("CRES-001")


class Test예약충돌:
    def test_충돌_예약_감지(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["resource_bookings"].find_many.return_value = [
            {
                "_id": "CRBK-001",
                "resource_id": "CRES-001",
                "event_id": "CEVT-001",
                "start_dt": now.isoformat(),
                "end_dt": (now + timedelta(hours=2)).isoformat(),
                "status": "confirmed",
            },
        ]

        conflicts = service.check_booking_conflict(
            "CRES-001",
            now + timedelta(hours=1),
            now + timedelta(hours=3),
        )

        assert len(conflicts) == 1

    def test_충돌_없는_예약(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["resource_bookings"].find_many.return_value = [
            {
                "_id": "CRBK-001",
                "resource_id": "CRES-001",
                "event_id": "CEVT-001",
                "start_dt": now.isoformat(),
                "end_dt": (now + timedelta(hours=1)).isoformat(),
                "status": "confirmed",
            },
        ]

        conflicts = service.check_booking_conflict(
            "CRES-001",
            now + timedelta(hours=2),
            now + timedelta(hours=3),
        )

        assert len(conflicts) == 0


class Test자원예약:
    def test_정상_예약(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["resources"].find_by_id.return_value = {
            "_id": "CRES-001",
            "name": "회의실A",
            "status": "available",
        }
        repos["resource_bookings"].find_many.return_value = []
        repos["resource_bookings"].insert.return_value = "CRBK-001"

        result = service.book_resource(
            event_id="CEVT-001",
            resource_id="CRES-001",
            start_dt=now,
            end_dt=now + timedelta(hours=1),
            booked_by="user-1",
        )

        assert result["status"] == "confirmed"
        assert result["resource_id"] == "CRES-001"
        repos["resource_bookings"].insert.assert_called_once()

    def test_충돌_시_예약_거부(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["resources"].find_by_id.return_value = {
            "_id": "CRES-001",
            "status": "available",
        }
        repos["resource_bookings"].find_many.return_value = [
            {
                "_id": "CRBK-001",
                "start_dt": now.isoformat(),
                "end_dt": (now + timedelta(hours=2)).isoformat(),
                "status": "confirmed",
            },
        ]

        with pytest.raises(ValueError, match="ERR-CAL-051"):
            service.book_resource(
                event_id="CEVT-002",
                resource_id="CRES-001",
                start_dt=now + timedelta(hours=1),
                end_dt=now + timedelta(hours=3),
            )


class Test예약취소:
    def test_정상_취소(self) -> None:
        service, repos = _make_service()
        repos["resource_bookings"].find_by_id.return_value = {
            "_id": "CRBK-001",
            "status": "confirmed",
        }

        result = service.cancel_booking("CRBK-001")

        assert result["status"] == "cancelled"
        repos["resource_bookings"].update_by_id.assert_called_once()

    def test_이미_취소된_예약_에러(self) -> None:
        service, repos = _make_service()
        repos["resource_bookings"].find_by_id.return_value = {
            "_id": "CRBK-001",
            "status": "cancelled",
        }

        with pytest.raises(ValueError, match="ERR-CAL-050"):
            service.cancel_booking("CRBK-001")

    def test_존재하지_않는_예약_에러(self) -> None:
        service, repos = _make_service()
        repos["resource_bookings"].find_by_id.return_value = None

        with pytest.raises(ValueError, match="ERR-CAL-050"):
            service.cancel_booking("CRBK-999")


class Test가용성조회:
    def test_가용_시간대_반환(self) -> None:
        service, repos = _make_service()
        now = datetime.now(tz=UTC)
        repos["resources"].find_by_id.return_value = {
            "_id": "CRES-001",
            "status": "available",
        }
        repos["resource_bookings"].find_many.return_value = [
            {
                "_id": "CRBK-001",
                "start_dt": (now + timedelta(hours=1)).isoformat(),
                "end_dt": (now + timedelta(hours=2)).isoformat(),
                "status": "confirmed",
            },
        ]

        result = service.get_resource_availability(
            "CRES-001",
            now,
            now + timedelta(hours=8),
        )

        assert result["total_bookings"] == 1
        assert len(result["booked_slots"]) == 1
