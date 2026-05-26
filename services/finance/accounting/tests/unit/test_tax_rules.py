"""세금규칙(Tax Rule) CRUD 엔드포인트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


_BASE_URL = "/api/v1/tax-rules"


def test_세금규칙_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/tax-rules — 세금규칙 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="TXR-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "tax_type": "VAT",
            "tax_rate": 10.0,
            "conditions": {"country": "KR"},
            "priority": 1,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tax_type"] == "VAT"
    assert data["tax_rate"] == "10.0"
    assert "_id" in data


def test_세금규칙_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/tax-rules — 세금규칙 목록을 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "TXR-2026-00001", "tax_type": "VAT", "tenant_id": "default"}])
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_세금규칙_단건_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/tax-rules/{doc_id} — 세금규칙을 단건 조회한다."""
    mock_collection.find_one.return_value = {
        "_id": "TXR-2026-00001",
        "tax_type": "VAT",
        "tax_rate": 10.0,
        "tenant_id": "default",
    }
    response = client.get(f"{_BASE_URL}/TXR-2026-00001")
    assert response.status_code == 200
    assert response.json()["tax_type"] == "VAT"


def test_세금규칙_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/tax-rules/{doc_id} — 미존재 시 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404


def test_세금규칙_삭제(mock_collection: MagicMock) -> None:
    """DELETE /api/v1/tax-rules/{doc_id} — 세금규칙을 삭제한다."""
    mock_collection.find_one.return_value = {
        "_id": "TXR-2026-00001",
        "tax_type": "VAT",
        "tenant_id": "default",
    }
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = client.delete(f"{_BASE_URL}/TXR-2026-00001")
    assert response.status_code == 204
