"""G4-1 모니터링 · G4-2 런북 (파일럿) · G4-3 백업 · G4-4 롤백 · G4-5 On-call 드릴."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.audit.gates import module_runbook_path
from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)


def gate_G4_1_monitoring(gate: str, module: str) -> GateResult:
    """Grafana 대시보드 JSON + 알림 5+ rule + T2 fired 이력."""
    dash = Path(f"deploy/monitoring/grafana/{module}-overview.json")
    alerts = Path(f"deploy/monitoring/alerts/{module}.yaml")
    if not dash.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{dash} 없음",
        )
    if not alerts.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{alerts} 없음",
        )
    try:
        dashboard = json.loads(dash.read_text())
    except json.JSONDecodeError as exc:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.FAIL,
            reason=f"{dash} JSON 파싱 실패: {exc}",
        )
    panels_defined = len(dashboard.get("panels", []))
    if panels_defined < 6:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.FAIL,
            reason=f"Grafana panel 6개 미달 (실제 {panels_defined})",
        )
    try:
        alerts_doc = yaml.safe_load(alerts.read_text()) or {}
    except yaml.YAMLError as exc:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.FAIL,
            reason=f"{alerts} YAML 파싱 실패: {exc}",
        )
    alerts_defined = sum(
        1
        for group in alerts_doc.get("groups", [])
        for rule in group.get("rules", [])
        if rule.get("alert")
    )
    if alerts_defined < 5:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.FAIL,
            reason=f"alert rule 5개 미달 (실제 {alerts_defined})",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T2"],
            artifact_glob={"T2": f"artifacts/T2/G4-1/{module}/run-*.json"},
            verification_fields={
                "panels_defined": {"gte": 6},
                "alerts_defined": {"gte": 5},
                "fired_history_checked": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G4_2_runbook(gate: str, module: str) -> GateResult:
    """G4-2 (파일럿): 런북 ≥150라인 · 6 H2 섹션 · frontmatter(owner/module/last_reviewed ≤90일)."""
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=[
                "개요",
                "전제 조건",
                "진단 절차",
                "복구 절차",
                "롤백 절차",
                "에스컬레이션",
            ],
            required_frontmatter=["owner", "module", "last_reviewed"],
            frontmatter_age_limits={"last_reviewed": 90},
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G4-2/{module}/*.log"},
            verification_fields={
                "runbook_lines": {"gte": 150},
                "sections_verified": {"eq": 6},
            },
        ),
        gate=gate,
        module=module,
        doc_path=module_runbook_path(module),
    )


def _drill_validator(gate: str, module: str, drill_gate: str) -> GateResult:
    """G4-3/4/5 공통 드릴 검증 — ≥150라인 · 7 섹션 · evidence frontmatter · T3."""
    drills = sorted(
        Path(f"docs/ops/drills/{drill_gate}").glob(f"*-{module}.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not drills:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{drill_gate} 드릴 문서 없음 (docs/ops/drills/{drill_gate}/*-{module}.md)",
        )
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=[
                "시나리오",
                "수행 단계",
                "관측",
                "증거",
                "결과",
                "개선사항",
                "다음 드릴",
            ],
            required_frontmatter=["gate", "module", "drill_date", "scenario", "evidence"],
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/T3/{drill_gate}/{module}/staging-*.log"},
            verification_fields={
                "drill_lines": {"gte": 150},
                "sections_verified": {"eq": 7},
                "staging_log_lines": {"gte": 6},
            },
        ),
        gate=gate,
        module=module,
        doc_path=drills[0],
    )


def gate_G4_3_backup(gate: str, module: str) -> GateResult:
    return _drill_validator(gate, module, "G4-3")


def gate_G4_4_rollback(gate: str, module: str) -> GateResult:
    return _drill_validator(gate, module, "G4-4")


def gate_G4_5_oncall(gate: str, module: str) -> GateResult:
    return _drill_validator(gate, module, "G4-5")
