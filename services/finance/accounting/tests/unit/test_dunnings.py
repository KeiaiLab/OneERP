"""독촉장(Dunning) CRUD 엔드포인트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app
from oneerp_core.document import DocStatus

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


_BASE_URL = "/api/v1/dunnings"


def test_독촉장_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/dunnings — 독촉장 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="DUN-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "customer": "CUST-001",
            "outstanding_amount": 5000000.0,
            "dunning_level": 1,
            "dunning_date": "2026-03-18",
            "dunning_fee": 50000.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer"] == "CUST-001"
    assert data["outstanding_amount"] == "5000000.0"
    assert "_id" in data


def test_독촉장_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/dunnings — 독촉장 목록을 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [{"_id": "DUN-2026-00001", "customer": "CUST-001", "tenant_id": "default"}]
        )
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_독촉장_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/dunnings/{doc_id} — 미존재 시 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404


def test_독촉장_제출(mock_collection: MagicMock) -> None:
    """POST /api/v1/dunnings/{doc_id}/submit — 초안 독촉장을 제출한다."""
    mock_collection.find_one.return_value = {
        "_id": "DUN-2026-00001",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "default",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = client.post(f"{_BASE_URL}/DUN-2026-00001/submit")
    assert response.status_code == 200
    assert response.json()["docstatus"] == DocStatus.SUBMITTED


def test_독촉장_취소(mock_collection: MagicMock) -> None:
    """POST /api/v1/dunnings/{doc_id}/cancel — 제출된 독촉장을 취소한다."""
    mock_collection.find_one.return_value = {
        "_id": "DUN-2026-00001",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "default",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = client.post(f"{_BASE_URL}/DUN-2026-00001/cancel")
    assert response.status_code == 200
    assert response.json()["docstatus"] == DocStatus.CANCELLED
