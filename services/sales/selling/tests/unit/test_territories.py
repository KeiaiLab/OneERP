"""영업구역(Territory) 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/territories"


def test_영업구역_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/territories -- 정상 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="TER-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "territory_name": "서울",
            "parent_territory": None,
            "territory_manager": "김영업",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_영업구역_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/territories -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "TER-001", "territory_name": "서울"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


def test_영업구역_조회_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/territories/{doc_id} -- 없는 문서는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404
