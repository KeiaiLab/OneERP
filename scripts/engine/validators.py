"""공용 증거 검증 헬퍼 — 라인·섹션·frontmatter·cross-link·tier 검증."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import cast


class GateStatus(StrEnum):
    PASS = "pass"  # noqa: S105
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    FAIL = "fail"
    TAMPERED = "tampered"


@dataclass
class GateResult:
    gate: str
    module: str
    status: GateStatus
    reason: str = ""
    tiers_met: dict[str, bool] = field(default_factory=dict)
    evidence_sha: str | None = None
    verification: dict[str, object] = field(default_factory=dict)
    evidence: str = ""  # 드릴 증거 문구 등 사람이 읽는 근거 메시지 (FAIL/NOT_IMPL 설명)


@dataclass
class ValidationSpec:
    min_lines: int = 0
    required_sections: list[str] | None = None
    required_frontmatter: list[str] | None = None
    frontmatter_age_limits: dict[str, int] | None = None  # {"last_reviewed": 90}
    cross_links_required: list[str] | None = None
    required_tiers: list[str] | None = None
    artifact_glob: dict[str, str] | None = None
    min_fenced_code_blocks: int | None = None
    min_image_refs: int | None = None
    exit_code_required: int = 0
    stdout_contains: list[str] | None = None
    verification_fields: dict[str, object] | None = None


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
_FENCED_CODE_RE = re.compile(r"^```", re.MULTILINE)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _check_age(value: str, max_days: int) -> bool:
    try:
        d = datetime.fromisoformat(value)
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return datetime.now(UTC) - d <= timedelta(days=max_days)


def validate_evidence(
    spec: ValidationSpec,
    *,
    gate: str,
    module: str,
    doc_path: Path | None = None,
) -> GateResult:
    """단일 진입점 — spec 필드별로 순차 검증."""

    if doc_path is not None:
        if not doc_path.exists():
            return GateResult(
                gate=gate,
                module=module,
                status=GateStatus.NOT_IMPLEMENTED,
                reason=f"doc missing: {doc_path}",
            )

        text = doc_path.read_text()
        lines = text.count("\n") + 1

        if spec.min_lines and lines < spec.min_lines:
            return GateResult(
                gate=gate,
                module=module,
                status=GateStatus.FAIL,
                reason=f"min_lines {spec.min_lines} 미달 (실제 {lines})",
            )

        if spec.required_sections:
            present = {m.group(1).strip() for m in _H2_RE.finditer(text)}
            missing = [s for s in spec.required_sections if s not in present]
            if missing:
                return GateResult(
                    gate=gate,
                    module=module,
                    status=GateStatus.FAIL,
                    reason=f"missing sections: {missing}",
                )

        fm = _parse_frontmatter(text)
        if spec.required_frontmatter:
            missing_fm = [k for k in spec.required_frontmatter if k not in fm]
            if missing_fm:
                return GateResult(
                    gate=gate,
                    module=module,
                    status=GateStatus.FAIL,
                    reason=f"missing frontmatter: {missing_fm}",
                )

        if spec.frontmatter_age_limits:
            for key, max_days in spec.frontmatter_age_limits.items():
                if key in fm and not _check_age(fm[key], max_days):
                    return GateResult(
                        gate=gate,
                        module=module,
                        status=GateStatus.FAIL,
                        reason=f"frontmatter {key} 가 {max_days}일 초과",
                    )

        if spec.min_fenced_code_blocks is not None:
            n_code = len(_FENCED_CODE_RE.findall(text)) // 2
            if n_code < spec.min_fenced_code_blocks:
                return GateResult(
                    gate=gate,
                    module=module,
                    status=GateStatus.FAIL,
                    reason=f"fenced code block {spec.min_fenced_code_blocks} 미달 (실제 {n_code})",
                )

        if spec.min_image_refs is not None:
            n_img = len(_IMAGE_RE.findall(text))
            if n_img < spec.min_image_refs:
                return GateResult(
                    gate=gate,
                    module=module,
                    status=GateStatus.FAIL,
                    reason=f"image refs {spec.min_image_refs} 미달 (실제 {n_img})",
                )

        if spec.cross_links_required:
            for pattern in spec.cross_links_required:
                matches = list(Path().glob(pattern))
                if not matches:
                    return GateResult(
                        gate=gate,
                        module=module,
                        status=GateStatus.FAIL,
                        reason=f"cross-link missing: {pattern}",
                    )

    # Tier 증거 검증
    if spec.required_tiers:
        from scripts.engine.evidence import latest_evidence_for

        tiers_met: dict[str, bool] = {}
        tiers_found: dict[str, bool] = {}  # 증거 존재 여부 (없으면 NOT_IMPLEMENTED 후보)
        for tier in spec.required_tiers:
            ev = latest_evidence_for(gate, module, tier, base_dir=Path.cwd())
            if ev is None:
                tiers_found[tier] = False
                tiers_met[tier] = False
                continue
            tiers_found[tier] = True
            if ev.exit_code != spec.exit_code_required:
                tiers_met[tier] = False
                continue
            ok = True
            for field_name, constraint in (spec.verification_fields or {}).items():
                value = ev.verification.get(field_name)
                if value is None:
                    ok = False
                    break
                if isinstance(constraint, dict):
                    constraint_map = cast("dict[str, object]", constraint)
                    gte = constraint_map.get("gte")
                    if gte is not None and not (
                        isinstance(value, (int, float))
                        and isinstance(gte, (int, float))
                        and value >= gte
                    ):
                        ok = False
                        break
                    lte = constraint_map.get("lte")
                    if lte is not None and not (
                        isinstance(value, (int, float))
                        and isinstance(lte, (int, float))
                        and value <= lte
                    ):
                        ok = False
                        break
                    eq = constraint_map.get("eq")
                    if "eq" in constraint_map and value != eq:
                        ok = False
                        break
            tiers_met[tier] = ok

        if not all(tiers_met.values()):
            # 증거 자체가 하나도 없으면 NOT_IMPLEMENTED
            if not any(tiers_found.values()):
                return GateResult(
                    gate=gate,
                    module=module,
                    status=GateStatus.NOT_IMPLEMENTED,
                    reason="tier 증거 없음",
                    tiers_met=tiers_met,
                )
            # 증거는 있으나 조건 미달이면 FAIL
            return GateResult(
                gate=gate,
                module=module,
                status=GateStatus.FAIL,
                reason=f"일부 tier 미충족 또는 verification 미달: {tiers_met}",
                tiers_met=tiers_met,
            )

        return GateResult(gate=gate, module=module, status=GateStatus.PASS, tiers_met=tiers_met)

    # tier 요구 없음 → 문서 검증만으로 PASS
    return GateResult(gate=gate, module=module, status=GateStatus.PASS)
