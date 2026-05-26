"""지속가능성 보고서(SustainabilityReport) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/sustainability-reports"


def test_보고서_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ESGR-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "report_code": "ESGR-2026-001",
            "title": "2026 ESG 보고서",
            "reporting_year": 2026,
            "company": "COMP-001",
        },
    )
    assert response.status_code == 201
    assert "_id" in response.json()


def test_보고서_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET — 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter([{"_id": "ESGR-001", "title": "2026 ESG"}]))
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1
