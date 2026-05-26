"""POS 마감(POSClosingEntry) CRUD + submit/cancel 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/pos-closing-entries"


def test_POS마감_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/pos-closing-entries -- 정상 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="POSC-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "pos_profile": "POS-PROF-001",
            "opening_amount": 100000.0,
            "closing_amount": 350000.0,
            "total_sales": 250000.0,
            "difference": 0.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_POS마감_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/pos-closing-entries -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "POSC-001", "total_sales": 250000.0}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_POS마감_상세_조회_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/pos-closing-entries/{doc_id} -- 없는 마감은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404


def test_POS마감_수정_초안_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """PUT /api/v1/pos-closing-entries/{doc_id} -- 초안 상태에서 정상 수정한다."""
    mock_collection.find_one.return_value = {"_id": "POSC-001", "docstatus": 0}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.put(
        f"{_BASE_URL}/POSC-001",
        json={"closing_amount": 400000.0},
    )
    assert response.status_code == 200


def test_POS마감_제출_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/pos-closing-entries/{doc_id}/submit -- 초안에서 제출 성공."""
    mock_collection.find_one.return_value = {"_id": "POSC-001", "docstatus": 0}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.post(f"{_BASE_URL}/POSC-001/submit")
    assert response.status_code == 200


def test_POS마감_취소_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/pos-closing-entries/{doc_id}/cancel -- 제출 상태에서 취소 성공."""
    mock_collection.find_one.return_value = {"_id": "POSC-001", "docstatus": 1}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.post(f"{_BASE_URL}/POSC-001/cancel")
    assert response.status_code == 200


def test_POS마감_삭제_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """DELETE /api/v1/pos-closing-entries/{doc_id} -- 정상 삭제 시 204를 반환한다."""
    mock_collection.find_one.return_value = {"_id": "POSC-001", "docstatus": 0}
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = test_client.delete(f"{_BASE_URL}/POSC-001")
    assert response.status_code == 204
