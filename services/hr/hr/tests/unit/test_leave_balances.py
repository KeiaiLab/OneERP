"""휴가잔액(LeaveBalance) API 엔드포인트 테스트 — Report."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from bson import ObjectId

_BASE_URL = "/api/v1/leave-balances"
_today_fn = date.today


def _make_cursor(data: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(data))
    return cursor


def test_휴가잔액_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """휴가잔액 목록 API가 빈 결과를 정상 반환하는지 검증한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter([]))
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 0
    response = test_client.get(f"{_BASE_URL}")
    assert response.status_code == 200


def test_휴가잔액_목록_데이터(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """휴가잔액 목록 API가 데이터를 정상 반환하는지 검증한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "LVBL-001"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.json()["total"] == 1


def test_휴가잔액_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """휴가잔액 목록은 만료 위험, 이월 후보, 운영 액션을 함께 보여줘야 한다."""
    expiry_date = _today_fn() + timedelta(days=14)
    balance_doc = {
        "_id": "LB-001",
        "employee": "EMP-001",
        "leave_type": "연차",
        "fiscal_year": str(_today_fn().year),
        "expiry_date": expiry_date,
        "total_allocated": 15,
        "total_used": 4,
        "balance": 11,
    }
    mock_collection.find.side_effect = [
        _make_cursor([balance_doc]),
        _make_cursor(
            [{"_id": "LT-001", "leave_type_name": "연차", "is_carry_forward": True}],
        ),
        _make_cursor(
            [
                {
                    "_id": "LP-001",
                    "leave_type_id": "LT-001",
                    "carry_forward": True,
                    "max_carry_forward_days": 5,
                    "status": "active",
                },
            ],
        ),
        _make_cursor(
            [
                {"_id": "LA-001", "employee_id": "EMP-001", "leave_type": "연차", "status": "open"},
                {
                    "_id": "LA-002",
                    "employee_id": "EMP-001",
                    "leave_type": "연차",
                    "status": "approved",
                },
            ],
        ),
    ]
    mock_collection.find_one.side_effect = [
        {"_id": "EMP-001", "employee_name": "홍길동"},
    ]
    mock_collection.count_documents.side_effect = [1]

    response = test_client.get(f"{_BASE_URL}?employee_id=EMP-001&fiscal_year={_today_fn().year}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["employee_count"] == 1
    assert payload["summary"]["expiring_soon_count"] == 1
    assert payload["summary"]["carry_forward_ready_count"] == 1
    assert payload["summary"]["total_remaining_days"] == 11.0
    row = payload["data"][0]
    assert row["employee_name"] == "홍길동"
    assert row["status_badge"] == "expiring_soon"
    assert row["recommended_action"] == "review_expiry"
    assert row["summary"]["remaining_days"] == 11.0
    assert row["summary"]["open_application_count"] == 1
    assert row["summary"]["approved_application_count"] == 1
    assert row["summary"]["carry_forward_cap_days"] == 5.0
    assert row["summary"]["expected_carry_forward_days"] == 5.0
    assert row["summary"]["utilization_rate_pct"] == pytest.approx(26.7, abs=0.05)
    assert row["available_actions"] == [
        "edit",
        "open_leave_applications",
        "run_carry_forward",
        "view_leave_report",
    ]


def test_휴가잔액_상세는_이월가이드와_권장액션을_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """휴가잔액 상세 요약은 이월 예상치와 운영 액션을 함께 반환해야 한다."""
    expiry_date = _today_fn() + timedelta(days=10)
    balance_doc = {
        "_id": "LB-001",
        "employee": "EMP-001",
        "leave_type": "연차",
        "fiscal_year": str(_today_fn().year),
        "expiry_date": expiry_date,
        "total_allocated": 18,
        "total_used": 8,
        "balance": 10,
    }
    mock_collection.find_one.side_effect = [
        balance_doc,
        {"_id": "EMP-001", "employee_name": "홍길동"},
    ]
    mock_collection.find.side_effect = [
        _make_cursor([{"_id": "LT-001", "leave_type_name": "연차", "is_carry_forward": True}]),
        _make_cursor(
            [
                {
                    "_id": "LP-001",
                    "leave_type_id": "LT-001",
                    "carry_forward": True,
                    "max_carry_forward_days": 5,
                    "status": "active",
                },
            ],
        ),
        _make_cursor(
            [
                {
                    "_id": ObjectId(),
                    "employee_id": "EMP-001",
                    "leave_type": "연차",
                    "status": "open",
                },
                {
                    "_id": ObjectId(),
                    "employee_id": "EMP-001",
                    "leave_type": "연차",
                    "status": "approved",
                },
            ],
        ),
    ]

    response = test_client.get(f"{_BASE_URL}/LB-001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["employee_name"] == "홍길동"
    assert payload["status_badge"] == "expiring_soon"
    assert payload["recommended_action"] == "review_expiry"
    assert payload["summary"]["remaining_days"] == 10.0
    assert payload["summary"]["approved_application_count"] == 1
    assert payload["carry_forward_summary"]["carry_forward_cap_days"] == 5.0
    assert payload["carry_forward_summary"]["expected_carry_forward_days"] == 5.0
    assert payload["carry_forward_summary"]["expires_in_days"] == 10
    assert payload["carry_forward_summary"]["utilization_rate_pct"] == pytest.approx(44.4, abs=0.05)
    assert payload["available_actions"] == [
        "edit",
        "open_leave_applications",
        "run_carry_forward",
        "view_leave_report",
    ]
