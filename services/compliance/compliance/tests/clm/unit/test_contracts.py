"""계약(Contract) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/contracts"


def test_계약_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/contracts — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="CTR-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "contract_name": "공급 계약 A",
            "contract_type": "purchase",
            "party_type": "supplier",
            "party_id": "SUP-001",
            "currency": "KRW",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_계약_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/contracts — 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "CTR-001", "contract_name": "계약A"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_계약_상세_조회_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/contracts/{id} — 없는 계약은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
