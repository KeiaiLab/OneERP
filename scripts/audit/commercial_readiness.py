"""v2 상용 증거 감사 스크립트 — 47모듈 x 23게이트 검증.

외부 노출 상수:
- ``REPO`` — 레포 루트 (테스트에서 monkeypatch 가능)
- ``DRILL_ROOT`` — ``<REPO>/docs/ops/drills`` 드릴 아티팩트 루트
- ``DRILL_MAX_AGE_DAYS`` — 드릴 최대 허용 기간(일)

외부 노출 타입:
- ``Status`` = GateStatus 별칭 (PASS/FAIL/PARTIAL/NOT_IMPLEMENTED/TAMPERED)
- ``Label`` = 모듈 상용도 라벨 StrEnum
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

# 스크립트를 ``python3 scripts/audit/commercial_readiness.py`` 로 직접 실행할 때
# ``scripts.*`` 절대 임포트를 허용하도록 레포 루트를 sys.path 선두에 삽입한다.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.audit.gates.g1_docs import gate_G1_1_adr  # noqa: E402
from scripts.audit.gates.g1_tests import (  # noqa: E402
    gate_G1_2_openapi,
    gate_G1_3_integration,
    gate_G1_4_unit,
    gate_G1_5_ui,
)
from scripts.audit.gates.g2_quality import (  # noqa: E402
    gate_G2_1_slo,
    gate_G2_2_load,
    gate_G2_3_perf,
    gate_G2_4_chaos,
    gate_G2_5_i18n,
)
from scripts.audit.gates.g3_security import (  # noqa: E402
    gate_G3_1_authn,
    gate_G3_2_secret,
    gate_G3_3_rbac,
    gate_G3_4_audit,
    gate_G3_5_dep,
)
from scripts.audit.gates.g4_ops import (  # noqa: E402
    gate_G4_1_monitoring,
    gate_G4_2_runbook,
    gate_G4_3_backup,
    gate_G4_4_rollback,
    gate_G4_5_oncall,
)
from scripts.audit.gates.g5_docs import (  # noqa: E402
    gate_G5_1_manual,
    gate_G5_2_tutorial,
    gate_G5_3_uat,
)
from scripts.engine.validators import GateResult, GateStatus  # noqa: E402

# ---------------------------------------------------------------------------
# 외부 노출 상수 / 타입 별칭
# ---------------------------------------------------------------------------

#: 레포 루트 — 테스트에서 monkeypatch 로 치환 가능.
REPO: Path = Path(__file__).resolve().parents[2]

#: 드릴 아티팩트 규약 루트 — ``<REPO>/docs/ops/drills/<gate-id>/<YYYY-MM-DD>-<module>.md``.
DRILL_ROOT: Path = REPO / "docs" / "ops" / "drills"

#: 드릴 최대 허용 기간(일). ADR-0001 §6.4 드릴 증거 계약.
DRILL_MAX_AGE_DAYS: int = 90

#: GateStatus 별칭 — 테스트·외부 코드가 ``commercial_readiness.Status`` 로 접근.
Status = GateStatus


class Label(StrEnum):
    """모듈 상용도 라벨 (ADR-0012 §2).

    순서: alpha < beta < pre-commercial < commercial-ready.
    """

    ALPHA = "alpha"
    BETA = "beta"
    PRE_COMMERCIAL = "pre-commercial"
    COMMERCIAL_READY = "commercial-ready"


# 47 모듈 (ADR-0012 점수순 — gateway 98 최상위)
MODULES: list[str] = [
    "gateway",
    "accounting",
    "hr",
    "directory",
    "selling",
    "buying",
    "stock",
    "payroll",
    "portal",
    "projects",
    "expenses",
    "crm",
    "advanced-planning",
    "analytics",
    "assets",
    "board",
    "calendar",
    "clm",
    "compliance",
    "consolidation",
    "documents",
    "ecommerce",
    "ehs",
    "esg",
    "fleet",
    "gtm",
    "integration-hub",
    "iot",
    "knowledge",
    "lms",
    "mail",
    "maintenance",
    "manufacturing",
    "marketing",
    "marketing-automation",
    "messenger",
    "plm",
    "pos",
    "quality",
    "rental",
    "reservation",
    "rpa",
    "subscriptions",
    "survey",
    "tms",
    "wiki",
    "workreport",
]

GATE_IDS: list[str] = [
    "G1-1",
    "G1-2",
    "G1-3",
    "G1-4",
    "G1-5",
    "G2-1",
    "G2-2",
    "G2-3",
    "G2-4",
    "G2-5",
    "G3-1",
    "G3-2",
    "G3-3",
    "G3-4",
    "G3-5",
    "G4-1",
    "G4-2",
    "G4-3",
    "G4-4",
    "G4-5",
    "G5-1",
    "G5-2",
    "G5-3",
]


GATE_REGISTRY: list[dict[str, object]] = [
    {"id": "G1-1", "fn": gate_G1_1_adr, "tiers": ["T1"]},
    {"id": "G1-2", "fn": gate_G1_2_openapi, "tiers": ["T1", "T2"]},
    {"id": "G1-3", "fn": gate_G1_3_integration, "tiers": ["T1", "T2"]},
    {"id": "G1-4", "fn": gate_G1_4_unit, "tiers": ["T1"]},
    {"id": "G1-5", "fn": gate_G1_5_ui, "tiers": ["T1", "T2"]},
    {"id": "G2-1", "fn": gate_G2_1_slo, "tiers": ["T2"]},
    {"id": "G2-2", "fn": gate_G2_2_load, "tiers": ["T3"]},
    {"id": "G2-3", "fn": gate_G2_3_perf, "tiers": ["T1"]},
    {"id": "G2-4", "fn": gate_G2_4_chaos, "tiers": ["T3"]},
    {"id": "G2-5", "fn": gate_G2_5_i18n, "tiers": ["T1"]},
    {"id": "G3-1", "fn": gate_G3_1_authn, "tiers": ["T1", "T2"]},
    {"id": "G3-2", "fn": gate_G3_2_secret, "tiers": ["T2"]},
    {"id": "G3-3", "fn": gate_G3_3_rbac, "tiers": ["T1"]},
    {"id": "G3-4", "fn": gate_G3_4_audit, "tiers": ["T1"]},
    {"id": "G3-5", "fn": gate_G3_5_dep, "tiers": ["T1"]},
    {"id": "G4-1", "fn": gate_G4_1_monitoring, "tiers": ["T2"]},
    {"id": "G4-2", "fn": gate_G4_2_runbook, "tiers": ["T1"]},
    {"id": "G4-3", "fn": gate_G4_3_backup, "tiers": ["T3"]},
    {"id": "G4-4", "fn": gate_G4_4_rollback, "tiers": ["T3"]},
    {"id": "G4-5", "fn": gate_G4_5_oncall, "tiers": ["T3"]},
    {"id": "G5-1", "fn": gate_G5_1_manual, "tiers": ["T1", "T2"]},
    {"id": "G5-2", "fn": gate_G5_2_tutorial, "tiers": ["T1", "T2"]},
    {"id": "G5-3", "fn": gate_G5_3_uat, "tiers": ["T2", "T3"]},
]


# ---------------------------------------------------------------------------
# G4-3 / G4-4 / G4-5 드릴 증거 검증 (ADR-0001 §6.4)
# ---------------------------------------------------------------------------

# 각 드릴 게이트의 필수 런북 세트 — 하나라도 누락 시 FAIL.
_DRILL_RUNBOOKS: dict[str, tuple[str, ...]] = {
    "G4-3": (
        "docs/ops/runbook-db-backup-restore.md",
        "docs/infra/ops/backup-restore.md",
    ),
    "G4-4": ("docs/infra/ops/rollback.md",),
    "G4-5": ("docs/ops/runbook-incident-response.md",),
}


def _runbook_missing(drill_gate: str) -> list[str]:
    """REPO 기준 필수 런북 중 누락된 경로 리스트 반환."""
    return [rel for rel in _DRILL_RUNBOOKS.get(drill_gate, ()) if not (REPO / rel).exists()]


def _latest_drill_date(drill_gate: str, module: str) -> date | None:
    """해당 게이트·모듈의 드릴 파일명에서 날짜를 파싱해 최신 드릴 날짜 반환.

    파일명 규약: ``<YYYY-MM-DD>-<module>.md`` (DRILL_ROOT/<drill_gate>/ 하위).
    """
    gate_dir = REPO / "docs" / "ops" / "drills" / drill_gate
    if not gate_dir.is_dir():
        return None
    candidates: list[date] = []
    for path in gate_dir.glob(f"*-{module}.md"):
        stem = path.stem
        if not stem.endswith(f"-{module}"):
            continue
        date_part = stem[: -(len(module) + 1)]
        try:
            candidates.append(date.fromisoformat(date_part))
        except ValueError:
            continue
    return max(candidates) if candidates else None


def _drill_gate(drill_gate: str, module: str) -> GateResult:
    """드릴 증거 계약 검증 — 런북/드릴 유무·최근성·모듈 일치 체크."""
    missing = _runbook_missing(drill_gate)
    if missing:
        return GateResult(
            gate=drill_gate,
            module=module,
            status=Status.FAIL,
            reason=f"필수 런북 누락: {missing}",
            evidence=f"runbook missing: {missing}",
        )

    latest = _latest_drill_date(drill_gate, module)
    if latest is None:
        return GateResult(
            gate=drill_gate,
            module=module,
            status=Status.NOT_IMPLEMENTED,
            reason=f"{drill_gate} 드릴 기록 없음 ({module})",
            evidence=f"no drill artifact for module={module} under {drill_gate}",
        )

    today = datetime.now(tz=UTC).date()
    age_days = (today - latest).days
    if age_days > DRILL_MAX_AGE_DAYS:
        return GateResult(
            gate=drill_gate,
            module=module,
            status=Status.NOT_IMPLEMENTED,
            reason=(
                f"최근 드릴 {latest.isoformat()} 이 "
                f"{DRILL_MAX_AGE_DAYS}일({age_days}일 경과)을 초과"
            ),
            evidence=f"drill stale: latest={latest.isoformat()} age={age_days}d",
        )

    return GateResult(
        gate=drill_gate,
        module=module,
        status=Status.PASS,
        reason=f"{drill_gate} 드릴 {latest.isoformat()} (age={age_days}d)",
        evidence=f"drill ok: {latest.isoformat()} age={age_days}d",
    )


def _gate_G4_3_backup(module: str) -> GateResult:
    """G4-3 백업·복구 드릴 증거 (단일 인자)."""
    return _drill_gate("G4-3", module)


def _gate_G4_4_rollback(module: str) -> GateResult:
    """G4-4 롤백 드릴 증거 (단일 인자)."""
    return _drill_gate("G4-4", module)


def _gate_G4_5_oncall(module: str) -> GateResult:
    """G4-5 on-call 드릴 증거 (단일 인자)."""
    return _drill_gate("G4-5", module)


# ---------------------------------------------------------------------------
# 모듈 라벨 · 리포트 API
# ---------------------------------------------------------------------------

_LABEL_STR_TO_ENUM: dict[str, Label] = {lbl.value: lbl for lbl in Label}


@dataclass
class ModuleReport:
    """단일 모듈 평가 결과 래퍼 — ``.label()`` 로 Label enum 반환."""

    module: str
    raw: dict[str, object]

    def label(self) -> Label:
        return _LABEL_STR_TO_ENUM.get(str(self.raw.get("label", "alpha")), Label.ALPHA)


def discover_modules() -> list[str]:
    """47 모듈 목록 반환 — ADR-0012 §2."""
    return list(MODULES)


def run_module(module: str) -> ModuleReport:
    """단일 모듈 평가 후 ``ModuleReport`` 로 포장."""
    return ModuleReport(module=module, raw=evaluate_module(module))


def _module_label(gates: list[GateResult]) -> str:
    pass_set = {g.gate for g in gates if g.status == GateStatus.PASS}
    score = len(pass_set)
    g_core = {"G1-1", "G1-2", "G1-3", "G1-4"}
    beta_required = g_core | {"G3-1", "G3-4", "G4-2"}
    if score == 23:
        return "commercial-ready"
    if score >= 18:
        return "pre-commercial"
    if beta_required.issubset(pass_set):
        return "beta"
    if {"G1-1", "G1-2"}.issubset(pass_set):
        return "alpha"
    return "none"


def evaluate_module(module: str) -> dict[str, object]:
    """한 모듈의 23 게이트 평가."""
    results: list[GateResult] = []
    for entry in GATE_REGISTRY:
        fn: Callable[[str, str], GateResult] = entry["fn"]  # type: ignore[assignment]
        gid: str = entry["id"]  # type: ignore[assignment]
        results.append(fn(gid, module))

    return {
        "module": module,
        "label": _module_label(results),
        "score": sum(1 for g in results if g.status == GateStatus.PASS),
        "gates": [
            {
                "id": g.gate,
                "status": g.status.value,
                "tiers_met": g.tiers_met,
                "evidence_sha": g.evidence_sha,
                "reason": g.reason,
                "verification": g.verification,
            }
            for g in results
        ],
    }


def _build_summary(reports: list[dict[str, object]]) -> dict[str, object]:
    """보고서 리스트로부터 공통 요약 집계 생성."""
    total_gates = len(reports) * 23
    passed = sum(1 for r in reports for g in r["gates"] if g["status"] == "pass")
    partial = sum(1 for r in reports for g in r["gates"] if g["status"] == "partial")
    not_impl = sum(1 for r in reports for g in r["gates"] if g["status"] == "not_implemented")
    failed = sum(1 for r in reports for g in r["gates"] if g["status"] == "fail")
    tampered = sum(1 for r in reports for g in r["gates"] if g["status"] == "tampered")
    labels = [r["label"] for r in reports]
    ready_count = labels.count("commercial-ready")
    overall_complete = passed == total_gates and ready_count == len(reports)
    return {
        "total": total_gates,
        "total_judgments": total_gates,  # 47 x 23 = 1081 판정 수 (테스트 호환)
        "passed": passed,
        "partial": partial,
        "not_implemented": not_impl,
        "failed": failed,
        "tampered": tampered,
        "commercial_ready_modules": ready_count,
        "pre_commercial_modules": labels.count("pre-commercial"),
        "beta_modules": labels.count("beta"),
        "alpha_modules": labels.count("alpha"),
        "overall_complete": overall_complete,
    }


def evaluate_all() -> dict[str, object]:
    """47 모듈 전체 평가."""
    reports = [evaluate_module(m) for m in MODULES]
    return {
        "schema_version": "v2.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": _build_summary(reports),
        "reports": reports,
    }


def _render_text(out: dict) -> str:
    s = out.get("summary", {})
    lines = [
        f"Commercial Readiness v{out.get('schema_version', '?')}",
        f"Generated: {out.get('generated_at', '')}",
        f"Summary: passed={s.get('passed', 0)}/{s.get('total', 0)}",
        f"  commercial-ready={s.get('commercial_ready_modules', 0)} "
        f"pre={s.get('pre_commercial_modules', 0)} "
        f"beta={s.get('beta_modules', 0)} "
        f"alpha={s.get('alpha_modules', 0)}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--module")
    parser.add_argument("--gate")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verify-evidence", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.module:
        # 미등록 모듈은 조용히 빈 결과가 나오지 않도록 명시적으로 거부한다
        if args.module not in MODULES:
            print(
                f"error: unknown module '{args.module}' (not in MODULES registry)",
                file=sys.stderr,
            )
            return 2
        reports = [evaluate_module(args.module)]
        out: dict[str, object] = {
            "schema_version": "v2.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": _build_summary(reports),
            "reports": reports,
        }
    else:
        out = evaluate_all()

    text = (
        json.dumps(out, ensure_ascii=False, indent=2)
        if args.format == "json"
        else _render_text(out)
    )
    if args.output:
        Path(args.output).write_text(text)
    else:
        print(text)

    if args.verify and args.strict:
        s = out.get("summary", {})
        return 0 if s.get("passed") == 1081 and s.get("commercial_ready_modules") == 47 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
