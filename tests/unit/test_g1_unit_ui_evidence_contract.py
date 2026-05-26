from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g1_tests import gate_G1_4_unit, gate_G1_5_ui
from scripts.ci.normalize_g1_ui import ui_status
from scripts.ci.normalize_g1_unit import unit_status


def test_unit_status_uses_service_tests_and_mutation_contract() -> None:
    status = unit_status("payroll")

    assert status["unit_tests_defined"] >= 5
    assert status["service_unit_tests"] >= 2
    assert status["pytest_exit"] == 0
    assert status["coverage_line_rate"] >= 0.80
    assert status["mutation_score"] >= 0.50
    assert status["static_eval_passed"] == 1


def test_ui_status_uses_three_playwright_scenarios() -> None:
    status = ui_status("payroll")

    assert status["scenarios"] >= 3
    assert status["playwright_exit"] == 0
    assert status["a11y_violations"] == 0
    assert status["manual_linked"] == 1
    assert status["uat_linked"] == 1
    assert status["static_eval_passed"] == 1


def test_g1_4_and_g1_5_gates_require_verification_fields() -> None:
    assert gate_G1_4_unit("G1-4", "payroll").status == "pass"
    assert gate_G1_5_ui("G1-5", "payroll").status == "pass"


def test_all_modules_have_unit_and_ui_contracts() -> None:
    unit_modules = {path.parts[2] for path in Path("tests/unit").glob("*/test_unit_*.py")}
    ui_modules = {path.parts[3] for path in Path("tests/playwright/ui").glob("*/test_*.py")}

    assert len(unit_modules) == 47
    assert len(ui_modules) == 47
