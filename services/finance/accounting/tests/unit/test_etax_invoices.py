"""전자세금계산서(ETaxInvoice) CRUD 엔드포인트 테스트."""

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


_BASE_URL = "/api/v1/etax-invoices"


def test_전자세금계산서_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/etax-invoices — 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ETAX-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "invoice_ref": "SINV-001",
            "issue_date": "2026-03-17",
            "supplier_or_customer": "테스트 고객",
            "supply_amount": 100000.0,
            "tax_amount": 10000.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_전자세금계산서_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/etax-invoices — 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [{"_id": "ETAX-001", "invoice_ref": "SINV-001"}],
        )
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


def test_전자세금계산서_상세_조회_미존재_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/etax-invoices/{doc_id} — 없는 전자세금계산서는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
