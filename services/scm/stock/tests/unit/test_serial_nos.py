"""시리얼번호(SerialNo) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.serial_nos as _mod
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


def test_시리얼번호_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/serial-nos — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "SN-2026-00001")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/serial-nos",
        json={"serial_no": "SN001", "item_code": "ITEM-001", "item_name": "테스트 품목"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "SN-2026-00001"


def test_시리얼번호_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/serial-nos — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "SN-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/serial-nos?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_시리얼번호_조회_미존재_404(monkeypatch: object) -> None:
    """GET /api/v1/serial-nos/{doc_id} — 없는 시리얼번호는 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/serial-nos/NOT-EXIST")
    assert response.status_code == 404


def test_시리얼번호_수정_정상(monkeypatch: object) -> None:
    """PUT /api/v1/serial-nos/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SN-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.put("/api/v1/serial-nos/SN-001", json={"status": "delivered"})
    assert response.status_code == 200


def test_시리얼번호_삭제_정상(monkeypatch: object) -> None:
    """DELETE /api/v1/serial-nos/{doc_id} — 정상 삭제 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "SN-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.delete("/api/v1/serial-nos/SN-001")
    assert response.status_code == 200
