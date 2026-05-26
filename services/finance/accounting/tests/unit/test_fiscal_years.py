"""회계연도(Fiscal Year) CRUD 엔드포인트 단위 테스트."""

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


_BASE_URL = "/api/v1/fiscal-years"


def test_회계연도_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/fiscal-years — 회계연도 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="FY-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "year_name": "2026",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "company": "테스트회사",
            "is_closed": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["year_name"] == "2026"
    assert "_id" in data


def test_회계연도_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/fiscal-years — 회계연도 목록을 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "FY-2026-00001", "year_name": "2026", "tenant_id": "default"}])
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_회계연도_단건_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/fiscal-years/{doc_id} — 회계연도를 단건 조회한다."""
    mock_collection.find_one.return_value = {
        "_id": "FY-2026-00001",
        "year_name": "2026",
        "tenant_id": "default",
    }
    response = client.get(f"{_BASE_URL}/FY-2026-00001")
    assert response.status_code == 200
    assert response.json()["year_name"] == "2026"


def test_회계연도_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/fiscal-years/{doc_id} — 미존재 시 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404


def test_회계연도_삭제(mock_collection: MagicMock) -> None:
    """DELETE /api/v1/fiscal-years/{doc_id} — 회계연도를 삭제한다."""
    mock_collection.find_one.return_value = {
        "_id": "FY-2026-00001",
        "year_name": "2026",
        "tenant_id": "default",
    }
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = client.delete(f"{_BASE_URL}/FY-2026-00001")
    assert response.status_code == 204
