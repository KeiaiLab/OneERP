"""23 게이트 레지스트리 · 47 모듈 · evaluate API 테스트."""

from __future__ import annotations

from scripts.audit.commercial_readiness import (
    GATE_IDS,
    GATE_REGISTRY,
    MODULES,
    evaluate_all,
    evaluate_module,
)


def test_gate_registry_has_23_entries() -> None:
    assert len(GATE_REGISTRY) == 23
    ids = [g["id"] for g in GATE_REGISTRY]
    assert ids == sorted(set(ids))


def test_gate_ids_has_23() -> None:
    assert len(GATE_IDS) == 23
    assert "G1-1" in GATE_IDS
    assert "G5-3" in GATE_IDS


def test_modules_count_is_47() -> None:
    assert len(MODULES) == 47
    assert MODULES[0] == "gateway"  # ADR-0012 점수 최상위


def test_evaluate_module_returns_23_gates() -> None:
    result = evaluate_module("gateway")
    assert result["module"] == "gateway"
    assert len(result["gates"]) == 23


def test_evaluate_all_returns_47_modules() -> None:
    out = evaluate_all()
    assert out["schema_version"] == "v2.0"
    assert len(out["reports"]) == 47
    assert out["summary"]["total"] == 47 * 23
