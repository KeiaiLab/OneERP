"""BOM 트리(BOMTree) 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_manufacturing_app.main import app

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


@patch("oneerp_manufacturing_app.routes.boms._get_repo")
def test_BOM_트리_조회_정상(mock_repo: MagicMock) -> None:
    """GET /api/v1/boms/{doc_id}/tree — BOM 트리를 조회한다."""
    repo = MagicMock()
    bom_doc = {
        "_id": "BOM-001",
        "item_code": "ITEM-001",
        "items": [
            {"item_code": "RAW-001", "item_name": "원자재A", "qty": 2.0},
        ],
    }
    repo.find_by_id.return_value = bom_doc
    mock_repo.return_value = repo

    response = client.get("/api/v1/boms/BOM-001/tree")
    assert response.status_code == 200
    data = response.json()
    assert data["bom"]["_id"] == "BOM-001"
    assert len(data["children"]) == 1


@patch("oneerp_manufacturing_app.routes.boms._get_repo")
def test_BOM_트리_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/boms/{doc_id}/tree — 없는 BOM은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.get("/api/v1/boms/NOT-EXIST/tree")
    assert response.status_code == 404
