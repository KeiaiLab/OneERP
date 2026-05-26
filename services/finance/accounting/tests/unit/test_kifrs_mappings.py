"""K-IFRS 매핑(KIFRS Mapping) CRUD 엔드포인트 단위 테스트."""

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


_BASE_URL = "/api/v1/kifrs-mappings"


def test_KIFRS매핑_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/kifrs-mappings — K-IFRS 매핑 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="KIFRS-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "k_ifrs_account": "1110",
            "local_account": "ACC-2026-00001",
            "mapping_type": "one_to_one",
            "effective_date": "2026-01-01",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["k_ifrs_account"] == "1110"
    assert data["mapping_type"] == "one_to_one"
    assert "_id" in data


def test_KIFRS매핑_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/kifrs-mappings — K-IFRS 매핑 목록을 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [{"_id": "KIFRS-2026-00001", "k_ifrs_account": "1110", "tenant_id": "default"}]
        )
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_KIFRS매핑_단건_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/kifrs-mappings/{doc_id} — K-IFRS 매핑을 단건 조회한다."""
    mock_collection.find_one.return_value = {
        "_id": "KIFRS-2026-00001",
        "k_ifrs_account": "1110",
        "local_account": "ACC-2026-00001",
        "tenant_id": "default",
    }
    response = client.get(f"{_BASE_URL}/KIFRS-2026-00001")
    assert response.status_code == 200
    assert response.json()["k_ifrs_account"] == "1110"


def test_KIFRS매핑_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/kifrs-mappings/{doc_id} — 미존재 시 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404


def test_KIFRS매핑_삭제(mock_collection: MagicMock) -> None:
    """DELETE /api/v1/kifrs-mappings/{doc_id} — K-IFRS 매핑을 삭제한다."""
    mock_collection.find_one.return_value = {
        "_id": "KIFRS-2026-00001",
        "k_ifrs_account": "1110",
        "tenant_id": "default",
    }
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
    response = client.delete(f"{_BASE_URL}/KIFRS-2026-00001")
    assert response.status_code == 204
