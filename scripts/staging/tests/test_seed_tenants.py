"""seed_tenants 유닛 테스트 — build_tenants 계약 검증."""

from __future__ import annotations

from scripts.staging.seed_tenants import build_tenants


def test_build_tenants_returns_three_with_gl_accounts() -> None:
    tenants = build_tenants()
    assert len(tenants) == 3
    for t in tenants:
        assert t["id"].startswith("stg-")
        assert "name" in t
        assert len(t["gl_accounts"]) >= 5
