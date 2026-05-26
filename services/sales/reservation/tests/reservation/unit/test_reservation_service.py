"""예약 서비스(ReservationService) 단위 테스트.

BR-RSV-003 ~ BR-RSV-010 비즈니스 규칙을 검증한다.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_reservation_app.reservation.models.reservation import RecurrenceType, ReservationCreate


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 목으로 대체한다."""
    _counter = 0

    def _gen(prefix: str, **_kwargs) -> str:
        nonlocal _counter
        _counter += 1
        return f"{prefix}-2026-{_counter:05d}"

    with patch(
        "oneerp_reservation_app.reservation.services.reservation_service.generate_name",
        side_effect=_gen,
    ):
        yield


def _make_service():
    """ReservationService와 mock Repository를 생성한다."""
    with patch(
        "oneerp_reservation_app.reservation.services.reservation_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            # find_many 기본값: 빈 목록
            repo.find_many.return_value = []
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_reservation_app.reservation.services.reservation_service import (
            ReservationService,
        )

        service = ReservationService(tenant_id="test-tenant")
    return service, repos


def _future(hours: int = 1) -> datetime:
    """현재로부터 hours 시간 후의 datetime을 반환한다."""
    return datetime.now(tz=UTC) + timedelta(hours=hours)


def _make_body(
    *,
    start_offset_hours: int = 2,
    duration_hours: int = 1,
    resource_id: str = "RSC-001",
) -> ReservationCreate:
    """테스트용 예약 생성 요청을 만든다."""
    start = _future(start_offset_hours)
    end = start + timedelta(hours=duration_hours)
    return ReservationCreate(
        resource_id=resource_id,
        title="테스트 회의",
        requester_id="EMP-001",
        requester_name="홍길동",
        start_time=start,
        end_time=end,
    )


class Test예약생성:
    """예약 생성 관련 테스트."""

    def test_정상_예약_생성(self) -> None:
        """기본 예약 생성이 정상 작동하는지 확인한다."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = []

        body = _make_body()
        result = service.create_reservation(body)

        assert result["count"] == 1
        assert len(result["reservation_ids"]) == 1
        repos["reservations"].insert.assert_called_once()

    def test_비활성_자원_예약_불가(self) -> None:
        """BR-RSV-003: 비활성 자원에는 예약 생성 불가."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "inactive",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = []

        body = _make_body()
        with pytest.raises(OneERPError, match="ERR-RSV-003"):
            service.create_reservation(body)

    def test_과거시간_예약_불가(self) -> None:
        """BR-RSV-004: 과거 시간에는 예약 생성 불가."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = []

        past = datetime.now(tz=UTC) - timedelta(hours=1)
        body = ReservationCreate(
            resource_id="RSC-001",
            title="과거 회의",
            start_time=past,
            end_time=past + timedelta(hours=1),
        )
        with pytest.raises(OneERPError, match="ERR-RSV-002"):
            service.create_reservation(body)

    def test_시간충돌_예약_불가(self) -> None:
        """BR-RSV-003: 동일 자원의 시간 충돌 예약 불가."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = []

        body = _make_body()
        # 기존 예약이 동일 시간에 존재
        repos["reservations"].find_many.return_value = [
            {
                "_id": "RSV-EXIST",
                "resource_id": "RSC-001",
                "start_time": body.start_time,
                "end_time": body.end_time,
                "status": "confirmed",
            },
        ]

        with pytest.raises(OneERPError, match="ERR-RSV-001"):
            service.create_reservation(body)

    def test_최대예약시간_초과_불가(self) -> None:
        """BR-RSV-008: 정책 최대 예약 시간 초과 불가."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = [
            {
                "max_duration_minutes": 60,
                "max_advance_days": 90,
                "max_concurrent_reservations": 5,
                "requires_approval": False,
            },
        ]

        body = _make_body(duration_hours=2)  # 120분 > 정책 60분
        with pytest.raises(OneERPError, match="ERR-RSV-007"):
            service.create_reservation(body)

    def test_자원_미존재_에러(self) -> None:
        """ERR-RSV-005: 자원이 존재하지 않을 때."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = None

        body = _make_body()
        with pytest.raises(OneERPError, match="ERR-RSV-005"):
            service.create_reservation(body)


class Test반복예약:
    """반복 예약 관련 테스트."""

    def test_주간반복_예약_생성(self) -> None:
        """BR-RSV-006: 주간 반복 예약 시 여러 인스턴스 생성."""
        service, repos = _make_service()
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "status": "active",
            "resource_type": "meeting_room",
            "available_hours_start": "00:00",
            "available_hours_end": "23:59",
        }
        repos["reservation_policies"].find_many.return_value = []
        repos["reservations"].find_many.return_value = []

        start = _future(2)
        body = ReservationCreate(
            resource_id="RSC-001",
            title="주간 회의",
            requester_id="EMP-001",
            start_time=start,
            end_time=start + timedelta(hours=1),
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_count=3,
        )
        result = service.create_reservation(body)

        assert result["count"] == 3
        assert repos["reservations"].insert.call_count == 3


class Test예약취소:
    """예약 취소 관련 테스트."""

    def test_정상_취소(self) -> None:
        """확인된 예약의 정상 취소."""
        service, repos = _make_service()
        future_time = _future(2)
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "confirmed",
            "start_time": future_time,
            "resource_id": "RSC-001",
        }
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "resource_type": "meeting_room",
        }
        repos["reservation_policies"].find_many.return_value = [
            {"cancellation_deadline_minutes": 30},
        ]

        result = service.cancel_reservation("RSV-001")
        assert result["status"] == "cancelled"
        repos["reservations"].update_by_id.assert_called_once()

    def test_이미_시작된_예약_취소불가(self) -> None:
        """BR-RSV-005: 이미 시작된 예약 취소 불가."""
        service, repos = _make_service()
        past_time = datetime.now(tz=UTC) - timedelta(hours=1)
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "in_progress",
            "start_time": past_time,
            "resource_id": "RSC-001",
        }

        with pytest.raises(OneERPError, match="ERR-RSV-004"):
            service.cancel_reservation("RSV-001")

    def test_이미_취소된_예약_재취소불가(self) -> None:
        """이미 취소된 예약은 다시 취소할 수 없다."""
        service, repos = _make_service()
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "cancelled",
        }

        with pytest.raises(OneERPError, match="ERR-RSV-004"):
            service.cancel_reservation("RSV-001")


class Test체크인_체크아웃:
    """체크인/체크아웃 관련 테스트."""

    def test_정상_체크인(self) -> None:
        """confirmed 상태의 예약 체크인."""
        service, repos = _make_service()
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "confirmed",
        }

        result = service.check_in("RSV-001")
        assert result["status"] == "in_progress"
        repos["reservations"].update_by_id.assert_called_once()

    def test_잘못된_상태_체크인_불가(self) -> None:
        """draft 상태에서는 체크인 불가."""
        service, repos = _make_service()
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "draft",
        }

        with pytest.raises(OneERPError, match="ERR-RSV-004"):
            service.check_in("RSV-001")

    def test_정상_체크아웃(self) -> None:
        """in_progress 상태의 예약 체크아웃."""
        service, repos = _make_service()
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "in_progress",
        }

        result = service.check_out("RSV-001")
        assert result["status"] == "completed"

    def test_잘못된_상태_체크아웃_불가(self) -> None:
        """confirmed 상태에서는 체크아웃 불가."""
        service, repos = _make_service()
        repos["reservations"].find_by_id.return_value = {
            "_id": "RSV-001",
            "status": "confirmed",
        }

        with pytest.raises(OneERPError, match="ERR-RSV-004"):
            service.check_out("RSV-001")


class Test미체크인_자동해제:
    """미체크인 자동 해제 관련 테스트."""

    def test_시간초과_자동해제(self) -> None:
        """auto_release_minutes 경과 후 no_show 처리."""
        service, repos = _make_service()
        past_start = datetime.now(tz=UTC) - timedelta(minutes=30)
        repos["reservations"].find_many.return_value = [
            {
                "_id": "RSV-001",
                "status": "confirmed",
                "start_time": past_start,
                "resource_id": "RSC-001",
            },
        ]
        repos["resources"].find_by_id.return_value = {
            "_id": "RSC-001",
            "resource_type": "meeting_room",
        }
        repos["reservation_policies"].find_many.return_value = [
            {"auto_release_minutes": 15},
        ]

        result = service.release_no_shows()
        assert result["released_count"] == 1
