from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g3_security import gate_G3_2_secret
from scripts.ci.normalize_g3_secrets import secret_status


def test_secret_status_uses_externalsecret_and_rotation_log() -> None:
    status = secret_status("payroll")

    assert status["externalsecret_defined"] == 1
    assert status["vault_store_ref"] == 1
    assert status["remote_refs"] >= 3
    assert status["rotation_log_lines"] >= 8


def test_g3_2_gate_requires_t2_secret_rotation_verification_fields() -> None:
    result = gate_G3_2_secret("G3-2", "payroll")

    assert result.status == "pass"


def test_all_modules_have_externalsecret_manifests() -> None:
    manifests = sorted(Path("deploy/secrets").glob("*/externalsecret.yaml"))

    assert len(manifests) == 47
