"""인사발령(Employee Transfer) 워크벤치 API 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

_BASE_URL = "/api/v1/employee-transfers"


def _make_cursor(data: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


def test_인사발령_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """인사발령 목록은 이동 범위, 급여 연계 가이드, 상태 배지를 함께 보여줘야 한다."""
    transfer_date = datetime.now(tz=UTC).date().isoformat()
    mock_collection.find.side_effect = [
        _make_cursor(
            [
                {
                    "_id": "ETR-001",
                    "employee": "EMP-001",
                    "employee_name": "홍길동",
                    "transfer_date": transfer_date,
                    "from_department": "영업팀",
                    "to_department": "기획팀",
                    "from_designation": "사원",
                    "to_designation": "대리",
                    "docstatus": 1,
                },
            ],
        ),
    ]
    mock_collection.count_documents.return_value = 1
    mock_collection.find_one.side_effect = [
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "기획팀",
            "designation": "대리",
            "status": "active",
            "_outbox": [
                {
                    "event_type": "employee.updated",
                    "data": {"transfer_id": "ETR-001"},
                },
            ],
        },
    ]

    response = test_client.get(f"{_BASE_URL}?employee=EMP-001&page=1&page_size=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "draft_count": 0,
        "submitted_count": 1,
        "cancelled_count": 0,
        "effective_today_count": 1,
        "payroll_sync_pending_count": 1,
    }
    row = payload["data"][0]
    assert row["status_badge"] == "submitted_dual_change"
    assert row["recommended_action"] == "verify_payroll_sync"
    assert row["summary"] == {
        "change_scope": "department_and_designation",
        "department_changed": True,
        "designation_changed": True,
        "transfer_date": transfer_date,
        "payroll_sync_pending": True,
    }
    assert row["available_actions"] == [
        "open_employee_profile",
        "verify_payroll_sync",
        "cancel",
    ]


def test_인사발령_요약은_변경영향과_급여연계가이드를_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """상세 요약은 이동 영향과 급여 동기화 상태를 함께 반환해야 한다."""
    mock_collection.find_one.side_effect = [
        {
            "_id": "ETR-001",
            "employee": "EMP-001",
            "employee_name": "홍길동",
            "transfer_date": "2026-04-10",
            "from_department": "영업팀",
            "to_department": "기획팀",
            "from_designation": "사원",
            "to_designation": "대리",
            "reason": "조직개편",
            "docstatus": 1,
        },
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "기획팀",
            "designation": "대리",
            "status": "active",
            "_outbox": [
                {
                    "event_type": "employee.updated",
                    "data": {"transfer_id": "ETR-001"},
                },
            ],
        },
    ]

    response = test_client.get(f"{_BASE_URL}/ETR-001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted_dual_change"
    assert payload["recommended_action"] == "verify_payroll_sync"
    assert payload["change_summary"] == {
        "change_scope": "department_and_designation",
        "from_department": "영업팀",
        "to_department": "기획팀",
        "from_designation": "사원",
        "to_designation": "대리",
        "transfer_date": "2026-04-10",
    }
    assert payload["impact_summary"] == {
        "employee_status": "active",
        "department_changed": True,
        "designation_changed": True,
        "current_department": "기획팀",
        "current_designation": "대리",
    }
    assert payload["sync_summary"] == {
        "employee_update_event_count": 1,
        "payroll_sync_pending": True,
        "last_event_type": "employee.updated",
    }
    assert payload["available_actions"] == [
        "open_employee_profile",
        "verify_payroll_sync",
        "cancel",
    ]


def test_인사발령_제출은_직원마스터와_outbox를_갱신한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """초안 인사발령 제출 시 직원 부서/직급과 급여 동기화 이벤트가 함께 갱신되어야 한다."""
    mock_collection.find_one.side_effect = [
        {
            "_id": "ETR-001",
            "employee": "EMP-001",
            "employee_name": "홍길동",
            "transfer_date": "2026-04-10",
            "from_department": "영업팀",
            "to_department": "기획팀",
            "from_designation": "사원",
            "to_designation": "대리",
            "docstatus": 0,
        },
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "영업팀",
            "designation": "사원",
            "status": "active",
        },
        {
            "_id": "ETR-001",
            "employee": "EMP-001",
            "employee_name": "홍길동",
            "transfer_date": "2026-04-10",
            "from_department": "영업팀",
            "to_department": "기획팀",
            "from_designation": "사원",
            "to_designation": "대리",
            "docstatus": 1,
        },
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "기획팀",
            "designation": "대리",
            "status": "active",
            "_outbox": [
                {
                    "event_type": "employee.updated",
                    "data": {"transfer_id": "ETR-001"},
                },
            ],
        },
    ]
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    response = test_client.post(f"{_BASE_URL}/ETR-001/submit")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted_dual_change"
    assert payload["recommended_action"] == "verify_payroll_sync"

    employee_updates = [
        call
        for call in mock_collection.update_one.call_args_list
        if call.args[0].get("_id") == "EMP-001"
    ]
    assert len(employee_updates) >= 2
    assert any(
        call.args[1].get("$set", {}).get("department") == "기획팀"
        and call.args[1].get("$set", {}).get("designation") == "대리"
        for call in employee_updates
    )
    assert any("$push" in call.args[1] for call in employee_updates)


def test_인사발령_취소는_직원정보를_원복한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """제출된 인사발령 취소 시 직원 마스터는 원래 부서/직급으로 되돌아가야 한다."""
    mock_collection.find_one.side_effect = [
        {
            "_id": "ETR-001",
            "employee": "EMP-001",
            "employee_name": "홍길동",
            "transfer_date": "2026-04-10",
            "from_department": "영업팀",
            "to_department": "기획팀",
            "from_designation": "사원",
            "to_designation": "대리",
            "docstatus": 1,
        },
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "기획팀",
            "designation": "대리",
            "status": "active",
        },
        {
            "_id": "ETR-001",
            "employee": "EMP-001",
            "employee_name": "홍길동",
            "transfer_date": "2026-04-10",
            "from_department": "영업팀",
            "to_department": "기획팀",
            "from_designation": "사원",
            "to_designation": "대리",
            "docstatus": 2,
        },
        {
            "_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "영업팀",
            "designation": "사원",
            "status": "active",
            "_outbox": [],
        },
    ]
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    response = test_client.post(f"{_BASE_URL}/ETR-001/cancel")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "cancelled"
    assert payload["recommended_action"] == "review_transfer_history"

    employee_updates = [
        call
        for call in mock_collection.update_one.call_args_list
        if call.args[0].get("_id") == "EMP-001"
    ]
    assert any(
        call.args[1].get("$set", {}).get("department") == "영업팀"
        and call.args[1].get("$set", {}).get("designation") == "사원"
        for call in employee_updates
    )


def test_인사발령_조회_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """존재하지 않는 인사발령 summary 조회는 404를 반환해야 한다."""
    mock_collection.find_one.return_value = None

    response = test_client.get(f"{_BASE_URL}/NOT-EXIST/summary")

    assert response.status_code == 404
