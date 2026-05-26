"""G5-1 사용자 매뉴얼 · G5-2 튜토리얼 · G5-3 UAT."""

from __future__ import annotations

from pathlib import Path

from scripts.engine.validators import (
    GateResult,
    ValidationSpec,
    validate_evidence,
)

# G5-1 매뉴얼 · G5-2 튜토리얼은 정본 경로를 먼저 보고, 레거시 경로는
# 정본 파일이 아직 없을 때만 fallback 으로 인정한다.
_MANUAL_CANDIDATES: tuple[str, ...] = (
    "docs/user-manual/{module}.md",
    "docs/manual/{module}.md",
)
_TUTORIAL_CANDIDATES: tuple[str, ...] = (
    "docs/tutorials/{module}.md",
    "docs/tutorial/{module}-flow.md",
)


def _pick_best(patterns: tuple[str, ...], module: str) -> Path:
    """여러 허용 경로 중 정본 경로를 우선 선택한다.

    실존 파일이 없으면 첫 번째 패턴의 경로를 반환하여 기존 동작(파일 없음 →
    NOT_IMPLEMENTED)을 유지한다.
    """
    for tmpl in patterns:
        path = Path(tmpl.format(module=module))
        if path.exists():
            return path
    return Path(patterns[0].format(module=module))


def gate_G5_1_manual(gate: str, module: str) -> GateResult:
    """매뉴얼 ≥250라인 · 8 H2 섹션 · 스크린샷 5+.

    경로 alias: `docs/user-manual/<module>.md` 또는 `docs/manual/<module>.md`
    중 실존·장문(line 수) 우선 파일을 증거로 수용한다.
    """
    path = _pick_best(_MANUAL_CANDIDATES, module)
    return validate_evidence(
        ValidationSpec(
            min_lines=250,
            required_sections=[
                "개요",
                "시작하기",
                "주요 화면",
                "자주 쓰는 작업",
                "설정",
                "제한사항",
                "장애 대응",
                "FAQ",
            ],
            min_image_refs=5,
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G5-1/{module}/*.log",
                "T2": f"artifacts/T2/G5-1/{module}/run-*.json",
            },
            verification_fields={
                "manual_lines": {"gte": 250},
                "h2_sections": {"eq": 8},
                "image_refs": {"gte": 5},
            },
        ),
        gate=gate,
        module=module,
        doc_path=path,
    )


def gate_G5_2_tutorial(gate: str, module: str) -> GateResult:
    """튜토리얼 ≥300라인 · fenced code block 10+.

    경로 alias: `docs/tutorials/<module>.md` 또는 `docs/tutorial/<module>-flow.md`
    중 실존·장문 우선 파일을 증거로 수용한다.
    """
    path = _pick_best(_TUTORIAL_CANDIDATES, module)
    return validate_evidence(
        ValidationSpec(
            min_lines=300,
            min_fenced_code_blocks=10,
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G5-2/{module}/*.log",
                "T2": f"artifacts/T2/G5-2/{module}/run-*.json",
            },
            verification_fields={
                "tutorial_lines": {"gte": 300},
                "fenced_code_blocks": {"gte": 10},
            },
        ),
        gate=gate,
        module=module,
        doc_path=path,
    )


def gate_G5_3_uat(gate: str, module: str) -> GateResult:
    """UAT ≥200라인 · 승인자 서명 frontmatter · T2+T3."""
    path = Path(f"docs/governance/commercial/{module}.md")
    return validate_evidence(
        ValidationSpec(
            min_lines=200,
            required_frontmatter=["approver", "approved_date", "test_run_id"],
            required_tiers=["T2", "T3"],
            artifact_glob={
                "T2": f"artifacts/T2/G5-3/{module}/run-*.json",
                "T3": f"artifacts/uat/{module}-*.log",
            },
            verification_fields={
                "uat_lines": {"gte": 200},
                "frontmatter_fields": {"eq": 3},
                "uat_scenarios": {"gte": 5},
                "approval_signed": {"eq": 1},
                "test_data_cleanup": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
        doc_path=path,
    )
