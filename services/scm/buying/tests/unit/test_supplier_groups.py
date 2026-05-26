"""공급업체그룹(SupplierGroup) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/supplier-groups"


def test_공급업체그룹_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/supplier-groups -- 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="SGR-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "group_name": "원자재 공급업체",
            "parent_group": None,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_공급업체그룹_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/supplier-groups -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "SGR-001", "group_name": "원자재"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_공급업체그룹_조회_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/supplier-groups/{doc_id} -- 없는 공급업체그룹은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
