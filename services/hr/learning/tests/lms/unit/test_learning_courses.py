"""교육 과정(LearningCourse) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/learning-courses"


def test_교육과정_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="LC-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={"course_name": "성희롱 예방교육", "course_code": "MND-001", "course_type": "online"},
    )
    assert response.status_code == 201
    assert "_id" in response.json()


def test_교육과정_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET — 목록 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter([{"_id": "LC-001", "course_name": "교육A"}]))
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_교육과정_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /{id} — 없는 과정은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
