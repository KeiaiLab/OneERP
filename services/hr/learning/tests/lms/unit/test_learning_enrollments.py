"""수강 등록(LearningEnrollment) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/learning-enrollments"


def test_수강등록_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="LE-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={"employee_id": "EMP-001", "course_id": "LC-001", "enrollment_date": "2026-03-01"},
    )
    assert response.status_code == 201
    assert "_id" in response.json()


def test_수강등록_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET — 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "LE-001", "employee_id": "EMP-001"}])
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1
