from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g1_tests import gate_G1_3_integration
from scripts.ci.normalize_g1_integration import integration_status


def test_integration_status_uses_three_contract_surfaces() -> None:
    status = integration_status("payroll")

    assert status["integration_files"] >= 3
    assert status["openapi_contract_found"] == 1
    assert status["deployment_contract_found"] == 1
    assert status["ops_contract_found"] == 1
    assert status["coverage_line_rate"] >= 0.60
    assert status["static_eval_passed"] == 1


def test_g1_3_gate_requires_t1_t2_integration_evidence() -> None:
    result = gate_G1_3_integration("G1-3", "payroll")

    assert result.status == "pass"


def test_all_modules_have_three_integration_contract_files() -> None:
    modules = {path.parts[2] for path in Path("tests/integration").glob("*/test_*.py")}

    assert len(modules) == 47
