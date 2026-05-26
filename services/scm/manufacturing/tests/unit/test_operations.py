"""공정(Operation) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_manufacturing_app.routes.operations as _mod
from fastapi.testclient import TestClient
from oneerp_manufacturing_app.main import app as manufacturing_app

client = TestClient(manufacturing_app)
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


def test_공정_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/operations — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "OPR-2026-00001")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/operations",
        json={"operation_name": "절단", "workstation": "WS-001", "time_in_mins": 30.0},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "OPR-2026-00001"


def test_공정_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/operations — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "OPR-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/operations?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_공정_조회_미존재_404(monkeypatch: object) -> None:
    """GET /api/v1/operations/{doc_id} — 없는 공정은 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/operations/NOT-EXIST")
    assert response.status_code == 404


def test_공정_수정_정상(monkeypatch: object) -> None:
    """PUT /api/v1/operations/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "OPR-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.put("/api/v1/operations/OPR-001", json={"time_in_mins": 45.0})
    assert response.status_code == 200


def test_공정_삭제_정상(monkeypatch: object) -> None:
    """DELETE /api/v1/operations/{doc_id} — 정상 삭제 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "OPR-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.delete("/api/v1/operations/OPR-001")
    assert response.status_code == 200
