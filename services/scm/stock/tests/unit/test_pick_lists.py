"""피킹목록(PickList) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.pick_lists as _mod
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


def test_피킹목록_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/pick-lists — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "PL-2026-00001")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/pick-lists",
        json={"purpose": "delivery", "items": []},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "PL-2026-00001"


# --- 목록 조회 ---


def test_피킹목록_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/pick-lists — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "PL-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/pick-lists?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


# --- 단건 조회 ---


def test_피킹목록_조회_미존재_404(monkeypatch: object) -> None:
    """GET /api/v1/pick-lists/{doc_id} — 없는 문서는 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/pick-lists/NOT-EXIST")
    assert response.status_code == 404


# --- 수정 ---


def test_피킹목록_수정_정상(monkeypatch: object) -> None:
    """PUT /api/v1/pick-lists/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PL-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.put(
        "/api/v1/pick-lists/PL-001",
        json={"purpose": "material_transfer"},
    )
    assert response.status_code == 200


# --- 제출 ---


def test_피킹목록_제출_정상(monkeypatch: object) -> None:
    """POST /api/v1/pick-lists/{doc_id}/submit — 초안 문서를 제출한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PL-001", "docstatus": 0}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/pick-lists/PL-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


def test_피킹목록_제출_비초안_400(monkeypatch: object) -> None:
    """POST /api/v1/pick-lists/{doc_id}/submit — 이미 제출된 문서는 400을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PL-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/pick-lists/PL-001/submit")
    assert response.status_code == 400


def test_판매주문에서_피킹목록_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/pick-lists/from-sales-order — 이벤트 payload로 피킹목록 초안을 생성한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "PL-2026-00077")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/pick-lists/from-sales-order",
        json={
            "sales_order_id": "SO-001",
            "tenant_id": "test-tenant",
            "customer_id": "CUST-001",
            "items": [
                {"item_code": "ITEM-001", "qty": 2, "warehouse": "WH-01"},
                {"item_code": "ITEM-002", "qty": 1, "warehouse": "WH-02"},
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "PL-2026-00077"
    assert payload["sales_order_id"] == "SO-001"
    insert_doc = repo.insert.call_args.args[0]
    assert insert_doc.id == "PL-2026-00077"
    assert insert_doc.purpose == "delivery"
    assert len(insert_doc.items) == 2
    assert insert_doc.items[0].item_code == "ITEM-001"
    assert float(insert_doc.items[0].qty) == 2


# --- 취소 ---


def test_피킹목록_취소_정상(monkeypatch: object) -> None:
    """POST /api/v1/pick-lists/{doc_id}/cancel — 제출된 문서를 취소한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PL-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/pick-lists/PL-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("PL-001")
