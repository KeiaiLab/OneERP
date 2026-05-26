"""품목변형(ItemVariant) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.item_variants as _mod
import pytest
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


def test_품목변형_생성_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/v1/item-variants — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "IVR-2026-00001")

    response = client.post(
        "/api/v1/item-variants",
        json={"item_code": "ITEM-001", "variant_of": "ITEM-TPL", "attributes": {"color": "red"}},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "IVR-2026-00001"


def test_품목변형_목록_조회(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/v1/item-variants — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "IVR-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.get("/api/v1/item-variants?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_품목변형_조회_미존재_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/v1/item-variants/{doc_id} — 없는 품목변형은 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.get("/api/v1/item-variants/NOT-EXIST")
    assert response.status_code == 404


def test_품목변형_수정_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """PUT /api/v1/item-variants/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "IVR-001"}
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.put(
        "/api/v1/item-variants/IVR-001",
        json={"attributes": {"color": "blue"}},
    )
    assert response.status_code == 200


def test_품목변형_삭제_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/v1/item-variants/{doc_id} — 정상 삭제 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "IVR-001"}
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.delete("/api/v1/item-variants/IVR-001")
    assert response.status_code == 200
