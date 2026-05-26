"""가격규칙(Pricing Rule) 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

_BASE_URL = "/api/v1/pricing-rules"


def test_가격규칙_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/pricing-rules -- 정상 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="PRC-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "rule_name": "신규 고객 할인",
            "apply_on": "item",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "priority": 1,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_가격규칙_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/pricing-rules -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "PRC-001", "rule_name": "할인 규칙"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_가격규칙_조회_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/pricing-rules/{doc_id} -- 없는 문서는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404
