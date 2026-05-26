"""계정과목(Account) CRUD 엔드포인트 단위 테스트."""

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


_BASE_URL = "/api/v1/accounts"


def test_계정과목_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/accounts — 계정과목 생성 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ACC-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "account_name": "현금",
            "account_type": "asset",
            "currency": "KRW",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "계정과목 생성 완료"


def test_계정과목_생성_그룹계정(mock_collection: MagicMock) -> None:
    """POST /api/v1/accounts — 그룹 계정 생성을 확인한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="ACC-2026-00002")
    response = client.post(
        _BASE_URL,
        json={
            "account_name": "유동자산",
            "account_type": "asset",
            "is_group": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_계정과목_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts — 계정과목 목록을 페이지네이션으로 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [
                {"_id": "ACC-2026-00001", "account_name": "현금", "tenant_id": "default"},
            ]
        )
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(_BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["account_name"] == "현금"


def test_계정과목_단건_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts/{doc_id} — 계정과목을 단건 조회한다."""
    mock_collection.find_one.return_value = {
        "_id": "ACC-2026-00001",
        "account_name": "현금",
        "account_type": "asset",
        "tenant_id": "default",
    }
    response = client.get(f"{_BASE_URL}/ACC-2026-00001")
    assert response.status_code == 200
    assert response.json()["account_name"] == "현금"


def test_계정과목_조회_404(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts/{doc_id} — 존재하지 않는 계정은 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404
