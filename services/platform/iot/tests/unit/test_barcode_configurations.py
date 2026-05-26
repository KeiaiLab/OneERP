"""바코드 설정(BarcodeConfiguration) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/barcode-configurations"


def test_바코드설정_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="BARC-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={"barcode_type": "GS1-128", "prefix": "880"},
    )
    assert response.status_code == 201
    assert "_id" in response.json()


def test_바코드설정_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET — 목록 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "BARC-001", "barcode_type": "GS1-128"}])
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_바코드설정_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /{id} — 없는 설정은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
