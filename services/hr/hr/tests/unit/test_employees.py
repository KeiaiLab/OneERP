"""직원(Employee) API 엔드포인트 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from oneerp_core.events.schemas import EventType

_BASE_URL = "/api/v1/employees"


def _make_cursor(documents: list[dict[str, object]]) -> MagicMock:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.__iter__ = MagicMock(return_value=iter(documents))
    return cursor


def test_직원_생성시_핵심_프로필_필드와_생성_이벤트를_저장한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """직원 생성 API가 생년월일/고용유형/보고라인과 employee.created 이벤트를 저장해야 한다."""
    manager = {
        "_id": "EMP-2025-00001",
        "employee_name": "김팀장",
        "status": "active",
    }
    mock_collection.find_one.return_value = manager
    mock_collection.insert_one.return_value = MagicMock(inserted_id="EMP-2026-00001")

    response = test_client.post(
        _BASE_URL,
        json={
            "employee_name": "홍길동",
            "department": "개발팀",
            "designation": "선임개발자",
            "date_of_joining": "2026-01-01",
            "date_of_birth": "1990-05-15",
            "employment_type": "REGULAR",
            "reports_to": "EMP-2025-00001",
            "email": "hong@example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["date_of_birth"] == "1990-05-15"
    assert data["employment_type"] == "REGULAR"
    assert data["reports_to"] == "EMP-2025-00001"
    inserted = mock_collection.insert_one.call_args.args[0]
    assert inserted["date_of_birth"] == datetime(1990, 5, 15, tzinfo=UTC)
    assert inserted["employment_type"] == "REGULAR"
    assert inserted["reports_to"] == "EMP-2025-00001"
    assert inserted["_outbox"][0]["event_type"] == EventType.EMPLOYEE_CREATED.value


def test_직원_생성시_존재하지_않는_보고상사는_차단한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """존재하지 않는 보고 상사를 지정하면 422를 반환해야 한다."""
    mock_collection.find_one.return_value = None

    response = test_client.post(
        _BASE_URL,
        json={
            "employee_name": "홍길동",
            "date_of_joining": "2026-01-01",
            "reports_to": "EMP-MISSING-001",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-041"


def test_직원_디렉터리가_보고라인과_직속인원수를_반환한다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """직원 디렉터리 API가 manager_name/direct_report_count와 상태 요약을 제공해야 한다."""
    documents = [
        {
            "_id": "EMP-0001",
            "employee_name": "김팀장",
            "department": "개발팀",
            "designation": "팀장",
            "status": "active",
            "employment_type": "REGULAR",
            "company": "OneERP",
            "reports_to": "",
        },
        {
            "_id": "EMP-0002",
            "employee_name": "박주임",
            "department": "개발팀",
            "designation": "주임",
            "status": "active",
            "employment_type": "REGULAR",
            "company": "OneERP",
            "reports_to": "EMP-0001",
        },
        {
            "_id": "EMP-0003",
            "employee_name": "이퇴사",
            "department": "개발팀",
            "designation": "사원",
            "status": "left",
            "employment_type": "CONTRACT",
            "company": "OneERP",
            "reports_to": "",
        },
    ]
    mock_collection.find.return_value = _make_cursor(documents)

    response = test_client.get(f"{_BASE_URL}/directory?status=active")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["active"] == 2
    assert payload["summary"]["left"] == 1
    manager = next(item for item in payload["data"] if item["id"] == "EMP-0001")
    subordinate = next(item for item in payload["data"] if item["id"] == "EMP-0002")
    assert manager["direct_report_count"] == 1
    assert subordinate["manager_name"] == "김팀장"


def test_보고라인에_사용중인_직원은_삭제할_수_없다(
    mock_collection: MagicMock,
    test_client: MagicMock,
) -> None:
    """부하 직원이 연결된 직원은 삭제하지 못해야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "EMP-0001",
        "employee_name": "김팀장",
        "status": "left",
    }
    mock_collection.count_documents.side_effect = [1]

    response = test_client.delete(f"{_BASE_URL}/EMP-0001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-043"
