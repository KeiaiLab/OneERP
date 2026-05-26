from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g3_security import gate_G3_3_rbac
from scripts.ci.normalize_g3_rbac import rbac_status


def test_rbac_status_uses_rego_policy_and_tests() -> None:
    status = rbac_status("payroll")

    assert status["rego_policies_defined"] >= 1
    assert status["rbac_tests_defined"] >= 5
    assert status["default_deny_found"] == 1
    assert status["least_privilege_rules"] >= 3
    assert status["static_eval_passed"] == 1


def test_g3_3_gate_requires_t1_rbac_verification_fields() -> None:
    result = gate_G3_3_rbac("G3-3", "payroll")

    assert result.status == "pass"


def test_all_modules_have_rbac_policy_directories() -> None:
    policies = sorted(Path("policies").glob("*/routes.rego"))

    assert len(policies) == 47
