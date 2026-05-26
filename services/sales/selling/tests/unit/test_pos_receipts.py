"""POS 영수증(POSReceipt) 로그 엔드포인트 테스트 — 생성/조회만."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_selling_app.main import app

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


@patch("oneerp_selling_app.routes.pos_receipts._get_repo")
@patch("oneerp_selling_app.routes.pos_receipts.generate_name", return_value="POSR-2026-00001")
def test_POS영수증_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/pos-receipts -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/pos-receipts",
        json={
            "transaction_id": "PTXN-001",
            "receipt_data": "영수증 내용",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "POSR-2026-00001"


@patch("oneerp_selling_app.routes.pos_receipts._get_repo")
def test_POS영수증_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/pos-receipts -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "POSR-001", "transaction_id": "PTXN-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/pos-receipts?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


@patch("oneerp_selling_app.routes.pos_receipts._get_repo")
def test_POS영수증_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/pos-receipts/{doc_id} -- 없는 영수증은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/pos-receipts/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_selling_app.routes.pos_receipts._get_repo")
def test_POS영수증_상세_조회_정상(mock_repo: MagicMock) -> None:
    """GET /api/v1/pos-receipts/{doc_id} -- 존재하는 영수증은 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "POSR-001", "transaction_id": "PTXN-001"}
    mock_repo.return_value = repo
    response = client.get("/api/v1/pos-receipts/POSR-001")
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == "POSR-001"
