"""G1-2 OpenAPI · G1-3 통합 · G1-4 단위 (파일럿) · G1-5 UI 게이트."""

from __future__ import annotations

from pathlib import Path

from scripts.audit.gates import module_service_dir
from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)

_DOCS_API_ALIAS: dict[str, str] = {
    "directory": "comms",
    "clm": "compliance",
    "consolidation": "finance-extra",
    "ecommerce": "commerce",
    "esg": "finance-extra",
    "fleet": "logistics",
    "lms": "learning",
    "mail": "comms",
    "maintenance": "assets",
    "messenger": "comms",
    "quality": "qm",
    "rental": "selling",
    "subscriptions": "selling",
    "tms": "logistics",
    "workreport": "learning",
}


def module_openapi_path(module: str) -> Path:
    """G1-2 OpenAPI 정본 경로를 반환한다."""
    docs_api_name = _DOCS_API_ALIAS.get(module, module)
    canonical = Path("docs") / "api" / docs_api_name / "openapi.yaml"
    if canonical.exists():
        return canonical
    return module_service_dir(module) / "openapi.yaml"


def gate_G1_2_openapi(gate: str, module: str) -> GateResult:
    """OpenAPI 스펙 파일 + T1/T2 증거."""
    openapi = module_openapi_path(module)
    if not openapi.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"{openapi} 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G1-2/{module}/*.log",
                "T2": f"artifacts/T2/G1-2/{module}/run-*.json",
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G1_3_integration(gate: str, module: str) -> GateResult:
    """통합 테스트 3+ 파일 · coverage ≥60% · T1+T2."""
    tests_dir = Path(f"tests/integration/{module}")
    if not tests_dir.exists() or len(list(tests_dir.glob("test_*.py"))) < 3:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason="통합 테스트 3+ 파일 없음",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G1-3/{module}/*.log",
                "T2": f"artifacts/T2/G1-3/{module}/run-*.json",
            },
            verification_fields={"coverage_line_rate": {"gte": 0.60}},
        ),
        gate=gate,
        module=module,
    )


def gate_G1_4_unit(gate: str, module: str) -> GateResult:
    """G1-4 (파일럿): 단위 테스트 · coverage ≥80% · mutation ≥50%."""
    svc = module_service_dir(module)
    has_tests = (svc / "tests").exists() or Path(f"tests/unit/{module}").exists()
    if not has_tests:
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"단위 테스트 디렉토리 없음 ({svc}/tests 또는 tests/unit/{module})",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G1-4/{module}/*.log"},
            verification_fields={
                "coverage_line_rate": {"gte": 0.80},
                "mutation_score": {"gte": 0.50},
                "pytest_exit": {"eq": 0},
                "unit_tests_defined": {"gte": 5},
                "service_unit_tests": {"gte": 2},
                "mutation_cases": {"gte": 5},
                "static_eval_passed": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
    )


def gate_G1_5_ui(gate: str, module: str) -> GateResult:
    """UI Playwright 3+ 시나리오 · a11y 0 · T1+T2."""
    pw_dir = Path(f"tests/playwright/ui/{module}")
    if not pw_dir.exists():
        return GateResult(
            gate=gate,
            module=module,
            status=GateStatus.NOT_IMPLEMENTED,
            reason=f"Playwright UI 테스트 디렉토리 없음 ({pw_dir})",
        )
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/playwright/{module}/report-*.html",
                "T2": f"artifacts/T2/G1-5/{module}/run-*.json",
            },
            verification_fields={
                "scenarios": {"gte": 3},
                "playwright_exit": {"eq": 0},
                "a11y_violations": {"eq": 0},
                "manual_linked": {"eq": 1},
                "tutorial_linked": {"eq": 1},
                "uat_linked": {"eq": 1},
                "static_eval_passed": {"eq": 1},
            },
        ),
        gate=gate,
        module=module,
    )
