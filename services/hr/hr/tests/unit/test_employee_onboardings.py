"""입사절차(EmployeeOnboarding) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/employee-onboardings"


def test_입사절차_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """입사절차 생성 API가 정상 동작하는지 검증한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="EON-2026-00001")
    response = test_client.post(f"{_BASE_URL}", json={"employee": "EMP-001"})
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_입사절차_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """입사절차 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "EON-001"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_입사절차_조회_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """존재하지 않는 입사절차 조회 시 404를 반환하는지 검증한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404


def test_입사절차_제출_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """초안 상태 입사절차 제출이 정상 동작하는지 검증한다."""
    mock_collection.find_one.return_value = {"_id": "EON-001", "docstatus": 0}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.post(f"{_BASE_URL}/EON-001/submit")
    assert response.status_code == 200


def test_입사절차_취소_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """제출된 입사절차 취소가 정상 동작하는지 검증한다."""
    mock_collection.find_one.return_value = {"_id": "EON-001", "docstatus": 1}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.post(f"{_BASE_URL}/EON-001/cancel")
    assert response.status_code == 200
