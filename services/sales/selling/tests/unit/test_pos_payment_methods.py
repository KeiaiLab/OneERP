"""POS 결제 수단(POSPaymentMethod) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/pos-payment-methods"


def test_POS결제수단_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/pos-payment-methods -- 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="POPM-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "method_name": "신용카드",
            "payment_type": "card",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_POS결제수단_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/pos-payment-methods -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "POPM-001", "method_name": "현금"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


def test_POS결제수단_상세_조회_미존재_404(
    mock_collection: MagicMock, test_client: MagicMock
) -> None:
    """GET /api/v1/pos-payment-methods/{doc_id} -- 없는 결제 수단은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404


def test_POS결제수단_수정_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """PUT /api/v1/pos-payment-methods/{doc_id} -- 정상 수정 시 200을 반환한다."""
    mock_collection.find_one.return_value = {"_id": "POPM-001", "method_name": "현금"}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.put(
        f"{_BASE_URL}/POPM-001",
        json={"method_name": "현금결제"},
    )
    assert response.status_code == 200


def test_POS결제수단_삭제_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """DELETE /api/v1/pos-payment-methods/{doc_id} -- 정상 삭제 시 204를 반환한다."""
    mock_collection.find_one.return_value = {"_id": "POPM-001", "docstatus": 0}
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = test_client.delete(f"{_BASE_URL}/POPM-001")
    assert response.status_code == 204
