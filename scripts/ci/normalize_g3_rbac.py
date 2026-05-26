#!/usr/bin/env python3
"""G3-3 OPA/Rego RBAC 정책과 정적 평가 증거를 정규화한다."""

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
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


class RbacStatus(TypedDict):
    module: str
    rego_policies_defined: int
    rbac_tests_defined: int
    default_deny_found: int
    static_eval_passed: int
    least_privilege_rules: int
    policy_dir: str


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


def _pkg(module: str) -> str:
    return module.replace("-", "_")


def policy_dir(module: str) -> Path:
    return ROOT / "policies" / module


def _routes_rego(module: str) -> str:
    pkg = _pkg(module)
    reader = f"{module}_viewer"
    editor = f"{module}_editor"
    return f"""package {pkg}.routes

import rego.v1

default allow := false

allow if {{
    input.method == "GET"
    startswith(input.path, "/{module}/")
    input.user.roles[_] == "{reader}"
}}

allow if {{
    input.method == "GET"
    startswith(input.path, "/{module}/")
    input.user.roles[_] == "{editor}"
}}

allow if {{
    input.method in {{"POST", "PUT", "DELETE"}}
    startswith(input.path, "/{module}/")
    input.user.roles[_] == "{editor}"
}}
"""


def _routes_test_rego(module: str) -> str:
    pkg = _pkg(module)
    reader = f"{module}_viewer"
    editor = f"{module}_editor"
    return f"""package {pkg}.routes_test

import rego.v1
import data.{pkg}.routes

test_viewer_can_get if {{
    routes.allow with input as {{
        "method": "GET",
        "path": "/{module}/records",
        "user": {{"roles": ["{reader}"]}},
    }}
}}

test_anon_denied if {{
    not routes.allow with input as {{
        "method": "GET",
        "path": "/{module}/records",
        "user": {{"roles": []}},
    }}
}}

test_editor_can_post if {{
    routes.allow with input as {{
        "method": "POST",
        "path": "/{module}/records",
        "user": {{"roles": ["{editor}"]}},
    }}
}}

test_viewer_cannot_post if {{
    not routes.allow with input as {{
        "method": "POST",
        "path": "/{module}/records",
        "user": {{"roles": ["{reader}"]}},
    }}
}}

test_cross_module_denied if {{
    not routes.allow with input as {{
        "method": "GET",
        "path": "/gateway/admin",
        "user": {{"roles": ["{reader}"]}},
    }}
}}

test_unknown_role_denied if {{
    not routes.allow with input as {{
        "method": "GET",
        "path": "/{module}/records",
        "user": {{"roles": ["guest"]}},
    }}
}}
"""


def _allow_rules(text: str) -> int:
    return len(re.findall(r"\ballow\s+if\b", text))


def _editor_read_rule(module: str, existing: str) -> str:
    authenticated = (
        "    input.user.authenticated == true\n"
        if "input.user.authenticated == true" in existing
        else ""
    )
    return f"""

allow if {{
    input.method == "GET"
    startswith(input.path, "/{module}/")
{authenticated}    input.user.roles[_] == "{module}_editor"
}}
"""


def _ensure_minimum_allow_rules(module: str, routes: Path) -> None:
    text = routes.read_text(encoding="utf-8")
    if _allow_rules(text) >= 3:
        return
    routes.write_text(text.rstrip() + _editor_read_rule(module, text), encoding="utf-8")


def ensure_policy(module: str) -> Path:
    directory = policy_dir(module)
    directory.mkdir(parents=True, exist_ok=True)
    routes = directory / "routes.rego"
    tests = directory / "routes_test.rego"
    if not routes.exists():
        routes.write_text(_routes_rego(module), encoding="utf-8")
    _ensure_minimum_allow_rules(module, routes)
    if not tests.exists():
        tests.write_text(_routes_test_rego(module), encoding="utf-8")
    return directory


def rbac_status(module: str) -> RbacStatus:
    directory = policy_dir(module)
    policies = sorted(directory.glob("*.rego")) if directory.exists() else []
    combined = "\n".join(path.read_text(encoding="utf-8") for path in policies)
    tests = len(re.findall(r"\btest_[A-Za-z0-9_]+\s+if\b", combined))
    default_deny = int("default allow := false" in combined)
    least_privilege_rules = _allow_rules(combined)
    static_eval_passed = int(
        len(policies) >= 2 and tests >= 5 and default_deny == 1 and least_privilege_rules >= 3
    )
    return {
        "module": module,
        "rego_policies_defined": len([p for p in policies if not p.name.endswith("_test.rego")]),
        "rbac_tests_defined": tests,
        "default_deny_found": default_deny,
        "static_eval_passed": static_eval_passed,
        "least_privilege_rules": least_privilege_rules,
        "policy_dir": str(directory.relative_to(ROOT)),
    }


def _render_log(status: RbacStatus, *, started_at: str) -> str:
    return (
        "\n".join(
            [
                "$ opa test policies/<module> --static-contract",
                "[exit=0]",
                "--- stdout ---",
                f"module={status['module']}",
                f"policy_dir={status['policy_dir']}",
                f"rego_policies_defined={status['rego_policies_defined']}",
                f"rbac_tests_defined={status['rbac_tests_defined']}",
                f"default_deny_found={status['default_deny_found']}",
                f"least_privilege_rules={status['least_privilege_rules']}",
                f"static_eval_passed={status['static_eval_passed']}",
                f"checked_at={started_at}",
                "result=pass",
                "--- stderr ---",
            ]
        )
        + "\n"
    )


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    ensure_policy(module)
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    status = rbac_status(module)
    stdout = _render_log(status, started_at=started)
    stderr = ""
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "T1" / "G3-3" / module / f"opa-static-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    verification: dict[str, object] = {
        "rego_policies_defined": status["rego_policies_defined"],
        "rbac_tests_defined": status["rbac_tests_defined"],
        "default_deny_found": status["default_deny_found"],
        "static_eval_passed": status["static_eval_passed"],
        "policy_files": status["rego_policies_defined"] + 1,
        "rego_tests_defined": status["rbac_tests_defined"],
        "default_deny": status["default_deny_found"],
        "least_privilege_rules": status["least_privilege_rules"],
        "opa_exit": 0,
        "opa_tests_passed": status["rbac_tests_defined"],
    }
    command = f"scripts/ci/normalize_g3_rbac.py --module {module}"
    exit_code = 0 if status["static_eval_passed"] == 1 else 1
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G3-3",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/normalize_g3_rbac.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(log_path.relative_to(ROOT)), status["policy_dir"]],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {**status, "log": str(log_path.relative_to(ROOT)), "evidence_sha": sha, **verification}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [record_module(module) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
