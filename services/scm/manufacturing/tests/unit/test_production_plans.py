"""생산계획(ProductionPlan) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_manufacturing_app.routes.production_plans as _mod
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


def test_생산계획_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/production-plans — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "PP-2026-00001")  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/production-plans",
        json={"status": "draft", "items": []},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "PP-2026-00001"


def test_생산계획_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/production-plans — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "PP-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/production-plans?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_생산계획_조회_미존재_404(monkeypatch: object) -> None:
    """GET /api/v1/production-plans/{doc_id} — 없는 문서는 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/production-plans/NOT-EXIST")
    assert response.status_code == 404


def test_생산계획_수정_정상(monkeypatch: object) -> None:
    """PUT /api/v1/production-plans/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PP-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.put("/api/v1/production-plans/PP-001", json={"status": "submitted"})
    assert response.status_code == 200


def test_생산계획_삭제_정상(monkeypatch: object) -> None:
    """DELETE /api/v1/production-plans/{doc_id} — 정상 삭제 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PP-001"}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.delete("/api/v1/production-plans/PP-001")
    assert response.status_code == 200


def test_생산계획_제출_정상(monkeypatch: object) -> None:
    """POST /api/v1/production-plans/{doc_id}/submit — 초안 문서를 제출한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PP-001", "docstatus": 0}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/production-plans/PP-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


def test_생산계획_제출_비초안_400(monkeypatch: object) -> None:
    """POST /api/v1/production-plans/{doc_id}/submit — 이미 제출된 문서는 400을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PP-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/production-plans/PP-001/submit")
    assert response.status_code == 400


def test_생산계획_취소_정상(monkeypatch: object) -> None:
    """POST /api/v1/production-plans/{doc_id}/cancel — 제출된 문서를 취소한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "PP-001", "docstatus": 1}
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.post("/api/v1/production-plans/PP-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("PP-001")
