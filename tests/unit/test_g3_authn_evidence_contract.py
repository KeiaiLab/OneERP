from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g3_security import gate_G3_1_authn
from scripts.ci.normalize_g3_authn import authn_status


def test_authn_status_uses_module_security_contract() -> None:
    status = authn_status("payroll")

    assert status["auth_tests_defined"] >= 7
    assert status["core_issuer_audience_verified"] == 1
    assert status["oidc_inventory_claims"] == 1
    assert status["externalsecret_defined"] == 1
    assert status["jwt_secret_externalized"] == 1
    assert status["httproute_defined"] == 1
    assert status["rbac_default_deny"] == 1
    assert status["runbook_auth_triage"] == 1
    assert status["static_eval_passed"] == 1


def test_g3_1_gate_requires_t1_t2_authn_evidence() -> None:
    result = gate_G3_1_authn("G3-1", "payroll")

    assert result.status == "pass"


def test_all_modules_have_authn_security_tests() -> None:
    paths = sorted(Path("tests/security").glob("*/test_auth_*.py"))
    modules = {path.parts[2] for path in paths}

    assert len(modules) == 47
