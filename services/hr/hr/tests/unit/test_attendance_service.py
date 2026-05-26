"""근태 서비스 단위 테스트 — 주 52시간 모니터링."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_hr_app.services.attendance_service import (
    AttendanceLocationValidationError,
    AttendanceService,
)


def _make_cursor(data: list) -> MagicMock:
    """find() → skip() → limit() 체인을 지원하는 cursor mock을 생성한다."""
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


@pytest.fixture
def mock_repos():
    """attendances 컬렉션 mock을 설정한다."""
    with patch("oneerp_core.repository.get_client") as mock_client:
        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        yield mock_col


def test_정상_40시간(mock_repos):
    """주 40시간 근무 시 초과 없음으로 반환된다."""
    mock_repos.find.return_value = _make_cursor(
        [
            {"attendance_date": "2026-03-23", "working_hours": 8},
            {"attendance_date": "2026-03-24", "working_hours": 8},
            {"attendance_date": "2026-03-25", "working_hours": 8},
            {"attendance_date": "2026-03-26", "working_hours": 8},
            {"attendance_date": "2026-03-27", "working_hours": 8},
        ]
    )

    svc = AttendanceService(tenant_id="T001")
    result = svc.check_weekly_work_hours("EMP-001", "2026-03-23")

    assert result["total_hours"] == 40.0
    assert result["overtime_hours"] == 0.0
    assert result["exceeded_52h"] is False
    assert result["exceeded_overtime_12h"] is False


def test_52시간_초과_경고(mock_repos):
    """주 54시간 근무 시 exceeded_52h와 exceeded_overtime_12h가 True로 반환된다."""
    mock_repos.find.return_value = _make_cursor(
        [
            {"attendance_date": "2026-03-23", "working_hours": 10},
            {"attendance_date": "2026-03-24", "working_hours": 10},
            {"attendance_date": "2026-03-25", "working_hours": 10},
            {"attendance_date": "2026-03-26", "working_hours": 10},
            {"attendance_date": "2026-03-27", "working_hours": 10},
            {"attendance_date": "2026-03-28", "working_hours": 4},
        ]
    )

    svc = AttendanceService(tenant_id="T001")
    result = svc.check_weekly_work_hours("EMP-002", "2026-03-23")

    assert result["total_hours"] == 54.0
    assert result["exceeded_52h"] is True
    assert result["overtime_hours"] == 14.0
    assert result["exceeded_overtime_12h"] is True


def test_모바일_체크인은_IP나_GPS_증빙이_필요하다(mock_repos) -> None:
    """모바일/키오스크 채널은 최소한 하나의 위치 증빙을 가져야 한다."""
    svc = AttendanceService(tenant_id="T001")

    with pytest.raises(AttendanceLocationValidationError) as exc_info:
        svc.build_check_in_payload(
            {
                "employee_id": "EMP-001",
                "attendance_date": "2026-04-09",
                "recorded_at": "2026-04-09T09:00:00",
                "capture_channel": "mobile_widget",
            }
        )

    assert exc_info.value.code == "ERR-HR-047"


def test_모바일_체크인은_예정시각이_있어도_위치증빙을_먼저_검증한다(mock_repos) -> None:
    """timezone 없는 체크인 시각도 모바일 위치증빙 검증을 통과하지 못해야 한다."""
    svc = AttendanceService(tenant_id="T001")

    with pytest.raises(AttendanceLocationValidationError) as exc_info:
        svc.build_check_in_payload(
            {
                "employee_id": "EMP-001",
                "attendance_date": "2026-04-09",
                "recorded_at": "2026-04-09T09:05:00",
                "capture_channel": "mobile_widget",
                "scheduled_start_time": "09:00",
            }
        )

    assert exc_info.value.code == "ERR-HR-047"


def test_근태_워크벤치_요약은_채널별_검증건수를_집계한다(mock_repos) -> None:
    """근태 워크벤치 요약은 모바일/키오스크 및 위치검증 집계를 보여줘야 한다."""
    svc = AttendanceService(tenant_id="T001")
    summary = svc.build_workbench_summary(
        [
            {
                "status": "present",
                "capture_channel": "mobile_widget",
                "location_status": "verified",
                "check_in_at": "2026-04-09T09:05:00",
                "late_minutes": 5,
                "is_late": True,
                "working_hours": 0.0,
            },
            {
                "status": "present",
                "capture_channel": "kiosk",
                "location_status": "verified",
                "check_in_at": "2026-04-09T08:55:00",
                "check_out_at": "2026-04-09T18:00:00",
                "working_hours": 8.0,
            },
        ]
    )

    assert summary == {
        "present_count": 2,
        "late_count": 1,
        "early_leave_count": 0,
        "checked_in_count": 1,
        "checked_out_count": 1,
        "location_verified_count": 2,
        "mobile_widget_count": 1,
        "kiosk_count": 1,
        "total_working_hours": 8.0,
    }


class Test건강검진주기:
    """BR-HR-017: 건강검진 주기 초과 여부 확인."""

    def test_주기_초과(self) -> None:
        """마지막 검진이 13개월 전이면 due=True."""
        with patch("oneerp_hr_app.services.attendance_service.Repository") as mock_repo_cls:
            checkup_repo = MagicMock()
            repos: dict[str, MagicMock] = {"health_checkups": checkup_repo}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            svc = AttendanceService(tenant_id="test-tenant")

            checkup_repo.find_many.return_value = [
                {
                    "_id": "HLTH-001",
                    "employee_id": "EMP-001",
                    "checkup_date": "2025-01-01",
                    "status": "completed",
                },
            ]

            result = svc.check_health_checkup_due("EMP-001", cycle_months=12)

        assert result["due"] is True
        assert result["last_checkup_date"] == "2025-01-01"
        assert result["overdue_days"] > 0

    def test_주기_미초과(self) -> None:
        """마지막 검진이 1개월 전이면 due=False."""
        with patch("oneerp_hr_app.services.attendance_service.Repository") as mock_repo_cls:
            checkup_repo = MagicMock()
            repos: dict[str, MagicMock] = {"health_checkups": checkup_repo}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            svc = AttendanceService(tenant_id="test-tenant")

            checkup_repo.find_many.return_value = [
                {
                    "_id": "HLTH-002",
                    "employee_id": "EMP-001",
                    "checkup_date": "2026-03-01",
                    "status": "completed",
                },
            ]

            result = svc.check_health_checkup_due("EMP-001", cycle_months=12)

        assert result["due"] is False
        assert result["overdue_days"] == 0

    def test_검진기록_없음(self) -> None:
        """검진 기록이 없으면 due=True."""
        with patch("oneerp_hr_app.services.attendance_service.Repository") as mock_repo_cls:
            checkup_repo = MagicMock()
            repos: dict[str, MagicMock] = {"health_checkups": checkup_repo}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                if collection_name not in repos:
                    repos[collection_name] = MagicMock()
                return repos[collection_name]

            mock_repo_cls.side_effect = _repo_factory
            svc = AttendanceService(tenant_id="test-tenant")

            checkup_repo.find_many.return_value = []

            result = svc.check_health_checkup_due("EMP-001")

        assert result["due"] is True
        assert result["last_checkup_date"] is None
