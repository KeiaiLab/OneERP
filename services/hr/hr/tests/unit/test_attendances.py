"""근태(Attendance) 커스텀 API 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/attendances"


def _make_cursor(data: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


def test_모바일_체크인은_위치증빙이_없으면_차단된다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """모바일 위젯 체크인은 IP 또는 GPS 증빙이 있어야 한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ATT-2026-00001")

    response = test_client.post(
        f"{_BASE_URL}/check-in",
        json={
            "employee_id": "EMP-001",
            "employee_name": "모바일 근태 직원",
            "department": "개발팀",
            "attendance_date": "2026-04-09",
            "capture_channel": "mobile_widget",
            "scheduled_start_time": "09:00",
            "scheduled_end_time": "18:00",
            "recorded_at": "2026-04-09T09:00:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-047"


def test_모바일_체크인은_채널과_위치요약을_저장한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """모바일 체크인은 위치 검증 요약과 채널 정보를 반환해야 한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ATT-2026-00001")

    response = test_client.post(
        f"{_BASE_URL}/check-in",
        json={
            "employee_id": "EMP-001",
            "employee_name": "모바일 근태 직원",
            "department": "개발팀",
            "attendance_date": "2026-04-09",
            "capture_channel": "mobile_widget",
            "ip_address": "10.0.0.5",
            "gps_latitude": 37.5665,
            "gps_longitude": 126.978,
            "scheduled_start_time": "09:00",
            "scheduled_end_time": "18:00",
            "recorded_at": "2026-04-09T09:07:00",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["capture_channel"] == "mobile_widget"
    assert payload["status_badge"] == "checked_in_late"
    assert payload["location_summary"] == {
        "capture_channel": "mobile_widget",
        "location_status": "verified",
        "location_proof_type": "gps+ip",
        "has_ip_address": True,
        "has_gps_coordinates": True,
    }
    assert payload["available_actions"] == ["check_out", "view_weekly_summary"]


def test_근태_목록은_상태배지와_워크벤치요약을_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """근태 목록은 채널별/검증별 운영 요약을 함께 제공해야 한다."""
    mock_collection.find.return_value = _make_cursor(
        [
            {
                "_id": "ATT-001",
                "employee_id": "EMP-001",
                "employee_name": "홍길동",
                "department": "개발팀",
                "attendance_date": "2026-04-09",
                "status": "present",
                "capture_channel": "mobile_widget",
                "location_status": "verified",
                "location_proof_type": "gps",
                "gps_latitude": 37.1,
                "gps_longitude": 127.1,
                "working_hours": 0.0,
                "late_minutes": 8,
                "is_late": True,
                "check_in_at": "2026-04-09T09:08:00",
            },
            {
                "_id": "ATT-002",
                "employee_id": "EMP-002",
                "employee_name": "김대리",
                "department": "개발팀",
                "attendance_date": "2026-04-09",
                "status": "present",
                "capture_channel": "kiosk",
                "location_status": "verified",
                "location_proof_type": "ip",
                "ip_address": "192.168.0.10",
                "working_hours": 8.0,
                "late_minutes": 0,
                "is_late": False,
                "check_in_at": "2026-04-09T08:58:00",
                "check_out_at": "2026-04-09T18:02:00",
            },
        ],
    )
    mock_collection.count_documents.return_value = 2

    response = test_client.get(
        f"{_BASE_URL}?attendance_date=2026-04-09&capture_channel=mobile_widget",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
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
    assert payload["data"][0]["status_badge"] == "checked_in_late"
    assert payload["data"][1]["status_badge"] == "completed"


def test_근태_상세는_사용가능액션과_위치검증요약을_노출한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """근태 상세는 관리자가 바로 쓸 수 있는 요약 필드를 포함해야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "ATT-2026-00001",
        "employee_id": "EMP-001",
        "employee_name": "홍길동",
        "department": "개발팀",
        "attendance_date": "2026-04-09",
        "status": "present",
        "capture_channel": "kiosk",
        "location_status": "verified",
        "location_proof_type": "ip",
        "ip_address": "10.0.0.10",
        "working_hours": 0.0,
        "late_minutes": 0,
        "is_late": False,
        "check_in_at": "2026-04-09T08:55:00",
    }

    response = test_client.get(f"{_BASE_URL}/ATT-2026-00001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "checked_in"
    assert payload["location_summary"] == {
        "capture_channel": "kiosk",
        "location_status": "verified",
        "location_proof_type": "ip",
        "has_ip_address": True,
        "has_gps_coordinates": False,
    }
    assert payload["available_actions"] == ["check_out", "view_weekly_summary"]
