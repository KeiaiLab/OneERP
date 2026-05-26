"""계약 템플릿(ContractTemplate) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/contract-templates"


def test_계약템플릿_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/contract-templates — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="CTT-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "template_name": "표준 NDA",
            "contract_type": "nda",
            "template_body": "본 계약은...",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_계약템플릿_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/contract-templates — 목록 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "CTT-001", "template_name": "표준 NDA"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_계약템플릿_상세_조회_미존재_404(
    mock_collection: MagicMock, test_client: MagicMock
) -> None:
    """GET /api/v1/contract-templates/{id} — 없는 템플릿은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
