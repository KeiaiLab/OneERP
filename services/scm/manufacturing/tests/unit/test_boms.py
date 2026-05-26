"""BOM(Bill of Materials) CRUD 엔드포인트 테스트."""

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
@patch("oneerp_manufacturing_app.routes.boms.generate_name", return_value="BOM-2026-00001")
def test_BOM_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/boms -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/boms",
        json={
            "item_code": "ITEM-001",
            "item_name": "완제품A",
            "quantity": 1.0,
            "items": [
                {"item_code": "RAW-001", "item_name": "원자재A", "qty": 2.0},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "BOM-2026-00001"


@patch("oneerp_manufacturing_app.routes.boms._get_repo")
def test_BOM_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/boms -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "BOM-001", "item_code": "ITEM-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/boms?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


@patch("oneerp_manufacturing_app.routes.boms._get_repo")
def test_BOM_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/boms/{doc_id} -- 없는 BOM은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/boms/NOT-EXIST")
    assert response.status_code == 404
