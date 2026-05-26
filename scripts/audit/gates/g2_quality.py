"""G2-1 SLO · G2-2 부하 · G2-3 perf · G2-4 chaos · G2-5 i18n."""

from __future__ import annotations

from pathlib import Path

from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)


def gate_G2_1_slo(gate: str, module: str) -> GateResult:
    """SLO 선언 문서 + 30일 번다운 T2 증거."""
    slo_path = Path("docs/infra/ops/slo.md")
    if not slo_path.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason="docs/infra/ops/slo.md 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T2"],
            artifact_glob={"T2": f"artifacts/slo/{module}-30d.json"},
            verification_fields={
                "slo_window_days": {"gte": 30},
                "availability_min": {"gte": 0.999},
                "error_rate_max": {"lte": 0.001},
                "p95_ms_max": {"lte": 200},
            },
        ),
        gate=gate,
        module=module,
        doc_path=slo_path,
    )


def gate_G2_2_load(gate: str, module: str) -> GateResult:
    """k6/locust 부하 스크립트 + T3 실측 결과."""
    load_dir = Path(f"tests/load/{module}")
    if not load_dir.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{load_dir} 없음",
        )
    baseline_path = Path(f"docs/engineering/data/perf-{module}-baseline.md")
    scenario_path = load_dir / "scenarios.js"
    if not baseline_path.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{baseline_path} 없음",
        )
    if not scenario_path.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{scenario_path} 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/k6/{module}-*.csv"},
            verification_fields={
                "load_baseline_found": {"eq": 1},
                "scenario_defined": {"eq": 1},
                "result_rows": {"gte": 10},
                "thresholds_passed": {"eq": 1},
                "p95_or_lcp_ms": {"lte": 2500},
                "success_rate": {"gte": 0.99},
                "duration_minutes": {"gte": 5},
            },
        ),
        gate=gate,
        module=module,
        doc_path=baseline_path,
    )


def gate_G2_3_perf(gate: str, module: str) -> GateResult:
    """30일 회귀 0건 로그."""
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/perf-regression/{module}/*.log"},
            verification_fields={
                "baseline_found": {"eq": 1},
                "regressions_found": {"eq": 0},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G2_4_chaos(gate: str, module: str) -> GateResult:
    """카오스 실행 로그 + MTTR 측정."""
    report_path = Path(f"docs/kb/incident/chaos-{module}-2026-04-22.md")
    scenario_path = Path(f"tests/chaos/{module}/scenarios.yaml")
    if not report_path.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{report_path} 없음",
        )
    if not scenario_path.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{scenario_path} 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/chaos/{module}-*.log"},
            verification_fields={
                "chaos_report_found": {"eq": 1},
                "scenario_defined": {"eq": 1},
                "mttr_minutes": {"lte": 60},
                "rehearsal_log_lines": {"gte": 8},
            },
        ),
        gate=gate,
        module=module,
        doc_path=report_path,
    )


def gate_G2_5_i18n(gate: str, module: str) -> GateResult:
    """ko/en/ja 3언어 ≥95% 커버리지."""
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G2-5/{module}/*.log"},
            verification_fields={
                "locale_coverage": {"gte": 0.95},
                "locales_checked": {"eq": 3},
            },
        ),
        gate=gate,
        module=module,
    )
