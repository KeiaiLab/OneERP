"""재고조정(StockReconciliation) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.stock_reconciliations as _mod
from fastapi.testclient import TestClient
from oneerp_stock_app.main import app as stock_app

client = TestClient(stock_app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


def _mock_repo() -> MagicMock:
    """공통 Repository mock을 반환한다."""
    return MagicMock()


# --- 생성 ---


def test_재고조정_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/stock-reconciliations — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "SREC-2026-00001")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/stock-reconciliations",
        json={"purpose": "stock_reconciliation", "items": []},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "SREC-2026-00001"


# --- 목록 조회 ---


def test_재고조정_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/stock-reconciliations — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "SREC-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/stock-reconciliations?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


# --- 단건 조회 ---


def test_재고조정_조회_미존재_404(monkeypatch: object) -> None:
    """GET /api/v1/stock-reconciliations/{doc_id} — 없는 문서는 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/stock-reconciliations/NOT-EXIST")
    assert response.status_code == 404


# --- 수정 ---


def test_재고조정_수정_정상(monkeypatch: object) -> None:
    """PUT /api/v1/stock-reconciliations/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SREC-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.put(
        "/api/v1/stock-reconciliations/SREC-001",
        json={"purpose": "opening_stock"},
    )
    assert response.status_code == 200


# --- 삭제 ---


def test_재고조정_삭제_정상(monkeypatch: object) -> None:
    """DELETE /api/v1/stock-reconciliations/{doc_id} — 정상 삭제 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SREC-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.delete("/api/v1/stock-reconciliations/SREC-001")
    assert response.status_code == 200


# --- 제출 ---


def test_재고조정_제출_정상(monkeypatch: object) -> None:
    """POST /api/v1/stock-reconciliations/{doc_id}/submit — 초안 문서를 제출한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SREC-001", "docstatus": 0}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/stock-reconciliations/SREC-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


def test_재고조정_제출_비초안_400(monkeypatch: object) -> None:
    """POST /api/v1/stock-reconciliations/{doc_id}/submit — 이미 제출된 문서는 400을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SREC-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/stock-reconciliations/SREC-001/submit")
    assert response.status_code == 400


# --- 취소 ---


def test_재고조정_취소_정상(monkeypatch: object) -> None:
    """POST /api/v1/stock-reconciliations/{doc_id}/cancel — 제출된 문서를 취소한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SREC-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/stock-reconciliations/SREC-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("SREC-001")
