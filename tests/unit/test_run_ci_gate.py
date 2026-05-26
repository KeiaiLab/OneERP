from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "ci" / "run.sh"
OPENAPI_DRIFT_SCRIPT = ROOT / "scripts" / "ci" / "check_openapi_drift.sh"
CONTRACT_SCRIPT = ROOT / "scripts" / "ci" / "run_contract_tests.sh"
DEP_AUDIT_SCRIPT = ROOT / "scripts" / "ci" / "dep_audit.sh"


def test_run_ci_gate_bounded_context_uses_core_fastapi_environment() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    command = (
        "uv run --with fastapi python -m pytest "
        "services/hr/learning/tests/unit/test_context_boundary.py "
        "services/sales/reservation/tests/unit/test_context_boundary.py "
        "-q"
    )
    assert command in content


def test_run_ci_gate_uses_module_pytest_for_core_gates() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert (
        "uv run --directory core --with fastapi python -m pytest "
        "tests/unit/test_kernel_architecture_boundaries.py -q"
    ) in content
    assert "uv run --directory core --with fastapi python -m pytest" in content


def test_run_ci_gate_uses_supported_commercial_readiness_format() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "commercial_readiness.py --format text" in content
    assert "commercial_readiness.py --format summary" not in content


def test_run_ci_gate_enforces_dependency_audit_failures() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "./scripts/ci/dep_audit.sh" in content
    assert "./scripts/ci/dep_audit.sh --report-only" not in content


def test_openapi_drift_gate_checks_untracked_and_staged_generated_files() -> None:
    content = OPENAPI_DRIFT_SCRIPT.read_text(encoding="utf-8")

    assert "git -C web diff --cached --exit-code -- lib/types/generated/" in content
    assert "git -C web ls-files --others --exclude-standard -- lib/types/generated/" in content
    assert "OpenAPI 생성 타입에 미추적 파일" in content


def test_contract_gate_records_g1_2_openapi_evidence() -> None:
    content = CONTRACT_SCRIPT.read_text(encoding="utf-8")

    assert "schemathesis.openapi.from_dict(schema).validate()" in content
    assert "record_openapi_contract_evidence.py" in content
    assert '--module "$svc_name"' in content


def test_contract_gate_validates_static_docs_openapi_modules() -> None:
    content = CONTRACT_SCRIPT.read_text(encoding="utf-8")

    assert "DOCS_API_MODULES=(" in content
    assert "ecommerce:commerce" in content
    assert "quality:qm" in content
    assert 'schema_file="docs/api/${api_name}/openapi.json"' in content


def test_dependency_audit_records_g3_5_evidence() -> None:
    content = DEP_AUDIT_SCRIPT.read_text(encoding="utf-8")

    assert "record_dep_audit_evidence.py" in content
    assert "--pip-report" in content
    assert "--npm-report" in content
