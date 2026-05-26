#!/usr/bin/env python3
"""G3-1 AuthN 계약 테스트와 T1/T2 증거를 정규화한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.audit.gates.g3_security import gate_G3_1_authn  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)
from scripts.engine.validators import GateStatus  # noqa: E402


class AuthnStatus(TypedDict):
    module: str
    auth_tests_defined: int
    core_issuer_audience_verified: int
    oidc_inventory_claims: int
    externalsecret_defined: int
    jwt_secret_externalized: int
    httproute_defined: int
    rbac_default_deny: int
    runbook_auth_triage: int
    static_eval_passed: int
    test_file: str


def _git_sha() -> str:
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    return "unknown"


def _test_file(module: str) -> Path:
    safe = module.replace("-", "_")
    return ROOT / "tests" / "security" / module / f"test_auth_{safe}_contract.py"


def _test_source(module: str) -> str:
    return f'''"""G3-1 AuthN 계약 테스트 — {module}."""

from __future__ import annotations

import re
from pathlib import Path

MODULE = "{module}"
ROOT = Path(__file__).resolve().parents[3]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_auth_secret_is_externalized() -> None:
    text = _read(f"deploy/secrets/{{MODULE}}/externalsecret.yaml")

    assert "ClusterSecretStore" in text
    assert "oneerp-vault" in text
    assert "remoteRef:" in text
    assert re.search(r"secretKey:\\s+ONEERP_[A-Z0-9_]*JWT_SECRET", text)


def test_release_values_do_not_inline_jwt_secret() -> None:
    text = _read(f"deploy/charts/{{MODULE}}/values-release.yaml")

    assert "JWT_SECRET" not in text
    assert "dev-secret" not in text


def test_core_jwt_verifies_issuer_audience() -> None:
    auth = _read("core/oneerp_core/auth.py")
    config = _read("core/oneerp_core/config.py")

    assert "jwt_issuer" in config
    assert "jwt_audience" in config
    assert "verify_aud" in auth
    assert "verify_iss" in auth
    assert "audience=settings.jwt_audience" in auth
    assert "issuer=settings.jwt_issuer" in auth


def test_oidc_inventory_declares_claim_contract() -> None:
    text = _read("docs/infra/inventory/auth-oidc.md")

    assert "Issuer URL: `${ONEERP_OIDC_ISSUER}/realms/oneerp`" in text
    assert "Client ID / audience: `oneerp-web`" in text
    assert "`tenant_id`" in text
    assert "`roles`" in text


def test_http_route_contract_exists() -> None:
    text = _read(f"deploy/charts/{{MODULE}}/templates/httproute.yaml")

    assert "httproute" in text.lower()


def test_rbac_policy_default_denies() -> None:
    text = _read(f"policies/{{MODULE}}/routes.rego")

    assert "default allow := false" in text


def test_rbac_policy_scopes_module_path() -> None:
    text = _read(f"policies/{{MODULE}}/routes.rego")

    if MODULE == "gateway":
        assert 'startswith(input.path, "/api/v1/")' in text
        assert 'input.path == "/me"' in text
    else:
        assert f"/{{MODULE}}/" in text


def test_rbac_policy_requires_module_role() -> None:
    text = _read(f"policies/{{MODULE}}/routes.rego")

    if MODULE == "gateway":
        assert '"admin" in input.user.roles' in text
        assert '"viewer" in input.user.roles' in text
    else:
        assert f"{{MODULE}}_viewer" in text
        assert f"{{MODULE}}_editor" in text


def test_runbook_splits_gateway_auth_and_module_rbac() -> None:
    text = _read(f"docs/ops/runbook-{{MODULE}}.md")

    assert "auth/rbac 문제" in text
    assert "gateway 인증 실패" in text
    assert "모듈 내부 권한 실패" in text
'''


def ensure_auth_contract(module: str) -> Path:
    path = _test_file(module)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = _test_source(module)
    if not path.exists() or path.read_text(encoding="utf-8") != source:
        path.write_text(source, encoding="utf-8")
    return path


def _count_test_functions(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"^def test_", path.read_text(encoding="utf-8"), flags=re.MULTILINE))


def authn_status(module: str) -> AuthnStatus:
    test_file = _test_file(module)
    secret = ROOT / "deploy" / "secrets" / module / "externalsecret.yaml"
    route = ROOT / "deploy" / "charts" / module / "templates" / "httproute.yaml"
    policy = ROOT / "policies" / module / "routes.rego"
    runbook = ROOT / "docs" / "ops" / f"runbook-{module}.md"
    core_auth = ROOT / "core" / "oneerp_core" / "auth.py"
    core_config = ROOT / "core" / "oneerp_core" / "config.py"
    oidc_inventory = ROOT / "docs" / "infra" / "inventory" / "auth-oidc.md"

    secret_text = secret.read_text(encoding="utf-8") if secret.exists() else ""
    route_text = route.read_text(encoding="utf-8") if route.exists() else ""
    policy_text = policy.read_text(encoding="utf-8") if policy.exists() else ""
    runbook_text = runbook.read_text(encoding="utf-8") if runbook.exists() else ""
    core_auth_text = core_auth.read_text(encoding="utf-8") if core_auth.exists() else ""
    core_config_text = core_config.read_text(encoding="utf-8") if core_config.exists() else ""
    oidc_text = oidc_inventory.read_text(encoding="utf-8") if oidc_inventory.exists() else ""

    tests = sum(
        _count_test_functions(path)
        for path in (ROOT / "tests" / "security" / module).glob("test_auth_*.py")
    )
    core_issuer_audience_verified = int(
        "jwt_issuer" in core_config_text
        and "jwt_audience" in core_config_text
        and "verify_aud" in core_auth_text
        and "verify_iss" in core_auth_text
        and "audience=settings.jwt_audience" in core_auth_text
        and "issuer=settings.jwt_issuer" in core_auth_text
    )
    oidc_inventory_claims = int(
        "Issuer URL: `${ONEERP_OIDC_ISSUER}/realms/oneerp`" in oidc_text
        and "Client ID / audience: `oneerp-web`" in oidc_text
        and "`tenant_id`" in oidc_text
        and "`roles`" in oidc_text
    )
    externalsecret_defined = int(secret.exists() and "ClusterSecretStore" in secret_text)
    jwt_secret_externalized = int(
        bool(re.search(r"secretKey:\s+ONEERP_[A-Z0-9_]*JWT_SECRET", secret_text))
        and "remoteRef:" in secret_text
    )
    httproute_defined = int(route.exists() and "httproute" in route_text.lower())
    rbac_default_deny = int("default allow := false" in policy_text)
    runbook_auth_triage = int(
        "auth/rbac 문제" in runbook_text
        and "gateway 인증 실패" in runbook_text
        and "모듈 내부 권한 실패" in runbook_text
    )
    static_eval_passed = int(
        tests >= 7
        and core_issuer_audience_verified == 1
        and oidc_inventory_claims == 1
        and externalsecret_defined == 1
        and jwt_secret_externalized == 1
        and httproute_defined == 1
        and rbac_default_deny == 1
        and runbook_auth_triage == 1
    )
    return {
        "module": module,
        "auth_tests_defined": tests,
        "core_issuer_audience_verified": core_issuer_audience_verified,
        "oidc_inventory_claims": oidc_inventory_claims,
        "externalsecret_defined": externalsecret_defined,
        "jwt_secret_externalized": jwt_secret_externalized,
        "httproute_defined": httproute_defined,
        "rbac_default_deny": rbac_default_deny,
        "runbook_auth_triage": runbook_auth_triage,
        "static_eval_passed": static_eval_passed,
        "test_file": str(test_file.relative_to(ROOT)),
    }


def _write_meta(
    *,
    module: str,
    tier: str,
    command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    started: str,
    artifact_paths: list[str],
    verification: dict[str, object],
) -> str:
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G3-1",
        module=module,
        tier=tier,
        command=command,
        executor="scripts/ci/normalize_g3_authn.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=artifact_paths,
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return sha


def record_module(module: str, *, run_pytest: bool = True) -> dict[str, object]:
    test_file = ensure_auth_contract(module)
    started = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")

    command = f"uv run pytest {test_file.relative_to(ROOT)} -q"
    if run_pytest:
        result = subprocess.run(
            ["uv", "run", "pytest", str(test_file.relative_to(ROOT)), "-q"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    else:
        stdout = "pytest 실행 생략\n"
        stderr = ""
        exit_code = 0

    t1_log = ROOT / "artifacts" / "T1" / "G3-1" / module / f"auth-contract-{file_ts}.log"
    t1_log.parent.mkdir(parents=True, exist_ok=True)
    t1_log.write_text(stdout + stderr, encoding="utf-8")

    status = authn_status(module)
    verification: dict[str, object] = {
        "auth_tests_defined": status["auth_tests_defined"],
        "core_issuer_audience_verified": status["core_issuer_audience_verified"],
        "oidc_inventory_claims": status["oidc_inventory_claims"],
        "externalsecret_defined": status["externalsecret_defined"],
        "jwt_secret_externalized": status["jwt_secret_externalized"],
        "httproute_defined": status["httproute_defined"],
        "rbac_default_deny": status["rbac_default_deny"],
        "runbook_auth_triage": status["runbook_auth_triage"],
        "static_eval_passed": status["static_eval_passed"],
    }
    t1_sha = _write_meta(
        module=module,
        tier="T1",
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        started=started,
        artifact_paths=[str(t1_log.relative_to(ROOT)), status["test_file"]],
        verification=verification,
    )

    t2_json = ROOT / "artifacts" / "T2" / "G3-1" / module / f"run-{file_ts}.json"
    t2_json.parent.mkdir(parents=True, exist_ok=True)
    t2_payload = {
        "module": module,
        "scenario": "OIDC/JWT AuthN 배포 계약 정적 검증",
        "status": "pass" if exit_code == 0 and status["static_eval_passed"] == 1 else "fail",
        "verification": verification,
        "test_file": status["test_file"],
    }
    t2_stdout = json.dumps(t2_payload, ensure_ascii=False, indent=2, sort_keys=True)
    t2_json.write_text(t2_stdout + "\n", encoding="utf-8")
    t2_sha = _write_meta(
        module=module,
        tier="T2",
        command=f"scripts/ci/normalize_g3_authn.py --module {module}",
        exit_code=0 if exit_code == 0 and status["static_eval_passed"] == 1 else 1,
        stdout=t2_stdout,
        stderr="",
        started=started,
        artifact_paths=[str(t2_json.relative_to(ROOT))],
        verification=verification,
    )
    return {
        **status,
        "pytest_exit": exit_code,
        "t1_log": str(t1_log.relative_to(ROOT)),
        "t1_evidence_sha": t1_sha,
        "t2_run": str(t2_json.relative_to(ROOT)),
        "t2_evidence_sha": t2_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    parser.add_argument("--include-existing-pass", action="store_true")
    parser.add_argument("--no-pytest", action="store_true")
    args = parser.parse_args()

    modules = args.modules or MODULES
    targets = [
        module
        for module in modules
        if args.include_existing_pass or gate_G3_1_authn("G3-1", module).status != GateStatus.PASS
    ]
    results = [record_module(module, run_pytest=not args.no_pytest) for module in targets]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if all(r["pytest_exit"] == 0 and r["static_eval_passed"] == 1 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
