"""commercial_readiness 엔진 모듈 레지스트리 단위 테스트."""

from __future__ import annotations

from scripts.audit.commercial_readiness import (
    GATE_REGISTRY,
    MODULES,
    _build_summary,
    evaluate_module,
)
from scripts.audit.gates import _MODULE_CLUSTER


def test_module_list_contains_accounting_and_hr() -> None:
    """accounting/hr 가 최상위 MODULES 레지스트리에 포함되어 있어야 한다."""
    assert "accounting" in MODULES
    assert "hr" in MODULES


def test_module_list_entries_have_cluster_mapping() -> None:
    """MODULES 의 모든 항목은 _MODULE_CLUSTER 에 경로 매핑이 존재해야 한다."""
    missing = [m for m in MODULES if m not in _MODULE_CLUSTER]
    assert missing == [], f"경로 매핑 누락: {missing}"


def test_per_module_score_returns_nonzero_denominator() -> None:
    """evaluate_module 는 23 게이트를 모두 enumerate 하여 denominator 를 보장한다."""
    for module in ("accounting", "hr", "gateway"):
        report = evaluate_module(module)
        assert report["module"] == module
        assert len(report["gates"]) == len(GATE_REGISTRY) == 23
        summary = _build_summary([report])
        assert summary["total"] == 23
        # score 는 0 이상, total 은 23 고정 — 빈 결과(0/0)가 아님을 보장
        assert summary["passed"] >= 0
        assert isinstance(report["score"], int)


def test_build_summary_aggregates_all_statuses() -> None:
    """_build_summary 는 passed/partial/failed/not_implemented/tampered 모두 집계한다."""
    report = evaluate_module("accounting")
    summary = _build_summary([report])
    accounted = (
        summary["passed"]
        + summary["partial"]
        + summary["failed"]
        + summary["not_implemented"]
        + summary["tampered"]
    )
    assert accounted == 23
