"""구매승인매트릭스(BuyerApprovalMatrix) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/buyer-approval-matrices"


def test_구매승인매트릭스_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/buyer-approval-matrices -- 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="BAM-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "item_group": "원자재",
            "min_amount": 0,
            "max_amount": 1000000,
            "approver": "manager@example.com",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_구매승인매트릭스_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/buyer-approval-matrices -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "BAM-001", "item_group": "원자재"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_구매승인매트릭스_조회_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/buyer-approval-matrices/{doc_id} -- 없는 구매승인매트릭스는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
