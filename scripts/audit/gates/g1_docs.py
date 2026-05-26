"""G1-1 ADR 게이트 — 문서 기반 검증."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)

# G1-1 ADR 파일 후보 디렉토리 — 기존(docs/governance/adr) 외에
# 경계 박제(bounded-context) ADR 이 실제로 작성되는 docs/kb/adr 도 인정한다.
# 두 위치 모두 모듈명이 포함된 마크다운을 동등 증거로 수용 (path alias).
_ADR_GLOB_DIRS: tuple[tuple[str, str], ...] = (
    ("docs/governance/adr", "*{module}*.md"),
    ("docs/kb/adr", "*{module}-bounds.md"),
    ("docs/kb/adr", "*{module}*.md"),
)
_MODULE_BOUNDARY_CATALOG = Path("docs/kb/adr/0021-module-boundary-catalog.md")


def _matches_module_token(path: Path, module: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")
    target = module.lower()
    return f"-{target}-" in f"-{normalized}-"


def _catalog_has_module(module: str) -> bool:
    if not _MODULE_BOUNDARY_CATALOG.exists():
        return False
    pattern = re.compile(rf"^##\s+{re.escape(module)}\s+[—-]", re.MULTILINE)
    return bool(pattern.search(_MODULE_BOUNDARY_CATALOG.read_text(encoding="utf-8")))


def _find_adr_candidates(module: str) -> list[Path]:
    """여러 허용 경로에서 ADR 후보를 모은다."""
    seen: set[Path] = set()
    ordered: list[Path] = []
    if _catalog_has_module(module):
        ordered.append(_MODULE_BOUNDARY_CATALOG)
        seen.add(_MODULE_BOUNDARY_CATALOG)
    for directory, pattern in _ADR_GLOB_DIRS:
        for p in Path(directory).glob(pattern.format(module=module)):
            if not _matches_module_token(p, module):
                continue
            if p not in seen:
                seen.add(p)
                ordered.append(p)
    return ordered


def gate_G1_1_adr(gate: str, module: str) -> GateResult:
    """ADR 파일 ≥ 1건 · ≥ 100 라인 · frontmatter(status/date/decision/consequences).

    경로 alias: `docs/governance/adr/*<module>*.md` 또는
    `docs/kb/adr/*<module>-bounds.md` 를 동등 증거로 수용한다.
    """
    candidates = _find_adr_candidates(module)
    if not candidates:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=(
                f"ADR 파일 없음 (docs/governance/adr/*{module}*.md · "
                f"docs/kb/adr/*{module}-bounds.md)"
            ),
        )
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return validate_evidence(
        ValidationSpec(
            min_lines=100,
            required_frontmatter=["status", "date", "decision", "consequences"],
        ),
        gate=gate,
        module=module,
        doc_path=candidates[0],
    )
