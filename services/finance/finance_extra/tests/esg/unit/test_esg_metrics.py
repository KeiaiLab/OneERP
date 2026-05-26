"""ESG 지표(ESGMetric) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/esg-metrics"


def test_ESG지표_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ESGM-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "metric_code": "ENV-001",
            "metric_name": "탄소배출량",
            "category": "environmental",
            "unit": "tCO2e",
        },
    )
    assert response.status_code == 201
    assert "_id" in response.json()


def test_ESG지표_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET — 목록 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "ESGM-001", "metric_name": "탄소"}])
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_ESG지표_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /{id} — 없는 지표는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
