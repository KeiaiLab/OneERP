#!/usr/bin/env python3
"""G3-4 audit hook 구현을 스캔하고 T1 증거를 기록한다."""

from __future__ import annotations

import argparse
import ast
import contextlib
import getpass
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.audit.gates import module_service_dir  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


class AuditHookStatus(TypedDict):
    module: str
    service_dir: str
    audit_hooks_found: int
    audit_actions_defined: int
    emit_helper_found: int
    audit_hook_lines: int
    hook_paths: list[str]


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


def _actions_from_value(value: ast.AST) -> int:
    if isinstance(value, ast.Tuple):
        return sum(1 for item in value.elts if isinstance(item, ast.Constant))
    return 0


def _module_actions(tree: ast.AST) -> int:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "MODULE_ACTIONS":
                    return _actions_from_value(node.value)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "MODULE_ACTIONS"
            and node.value is not None
        ):
            return _actions_from_value(node.value)
    return 0


def audit_hook_status(module: str) -> AuditHookStatus:
    service_dir = ROOT / module_service_dir(module)
    hooks = sorted(service_dir.rglob("audit_hooks.py"))
    if not hooks:
        return {
            "module": module,
            "service_dir": str(service_dir.relative_to(ROOT)),
            "audit_hooks_found": 0,
            "audit_actions_defined": 0,
            "emit_helper_found": 0,
            "audit_hook_lines": 0,
            "hook_paths": [],
        }
    actions = 0
    emit_found = False
    line_count = 0
    for hook in hooks:
        text = hook.read_text(encoding="utf-8")
        line_count += text.count("\n") + 1
        tree = ast.parse(text)
        actions += _module_actions(tree)
        emit_found = emit_found or ("def emit(" in text and "emit_audit_event" in text)
    return {
        "module": module,
        "service_dir": str(service_dir.relative_to(ROOT)),
        "audit_hooks_found": len(hooks),
        "audit_actions_defined": actions,
        "emit_helper_found": int(emit_found),
        "audit_hook_lines": line_count,
        "hook_paths": [str(path.relative_to(ROOT)) for path in hooks],
    }


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    status = audit_hook_status(module)
    stdout = "\n".join(f"{key}={value}" for key, value in status.items()) + "\n"
    stderr = ""
    command = f"scripts/ci/record_g3_audit_evidence.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "T1" / "G3-4" / module / f"audit-hooks-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    verification: dict[str, object] = {
        "audit_hooks_found": status["audit_hooks_found"],
        "audit_actions_defined": status["audit_actions_defined"],
        "emit_helper_found": status["emit_helper_found"],
        "audit_hook_lines": status["audit_hook_lines"],
    }
    meta = EvidenceMeta(
        sha256=sha,
        gate="G3-4",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/record_g3_audit_evidence.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(log_path.relative_to(ROOT)), *status["hook_paths"]],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {**status, "evidence_sha": sha, "log": str(log_path.relative_to(ROOT))}


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
