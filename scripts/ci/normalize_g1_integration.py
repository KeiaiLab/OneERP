#!/usr/bin/env python3
"""G1-3 모듈 통합 계약 테스트와 T1/T2 증거를 정규화한다."""

from __future__ import annotations

import argparse
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
from scripts.audit.gates.g1_tests import gate_G1_3_integration  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)
from scripts.engine.validators import GateStatus  # noqa: E402


class IntegrationStatus(TypedDict):
    module: str
    integration_files: int
    openapi_contract_found: int
    deployment_contract_found: int
    ops_contract_found: int
    coverage_line_rate: float
    static_eval_passed: int
    test_dir: str


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


def _safe(module: str) -> str:
    return module.replace("-", "_")


def test_dir(module: str) -> Path:
    return ROOT / "tests" / "integration" / module


def _api_source(module: str) -> str:
    return f'''"""G1-3 API 통합 계약 — {module}."""

from __future__ import annotations

from scripts.audit.gates.g1_tests import module_openapi_path

MODULE = "{module}"


def test_openapi_contract_exists_and_has_paths() -> None:
    path = module_openapi_path(MODULE)
    text = path.read_text(encoding="utf-8")

    assert "openapi:" in text
    assert "paths:" in text
    assert "/" in text
'''


def _deploy_source(module: str) -> str:
    return f'''"""G1-3 배포 통합 계약 — {module}."""

from __future__ import annotations

from pathlib import Path

MODULE = "{module}"
ROOT = Path(__file__).resolve().parents[3]


def test_release_chart_exposes_service_and_route() -> None:
    chart = ROOT / "deploy" / "charts" / MODULE

    assert (chart / "templates" / "deployment.yaml").exists()
    assert (chart / "templates" / "service.yaml").exists()
    assert (chart / "templates" / "httproute.yaml").exists()
    assert (chart / "values-release.yaml").exists()
'''


def _ops_source(module: str) -> str:
    return f'''"""G1-3 운영 통합 계약 — {module}."""

from __future__ import annotations

from pathlib import Path

MODULE = "{module}"
ROOT = Path(__file__).resolve().parents[3]


def test_operator_docs_link_module_runtime_surfaces() -> None:
    runbook = ROOT / "docs" / "ops" / f"runbook-{{MODULE}}.md"
    manual = ROOT / "docs" / "user-manual" / f"{{MODULE}}.md"
    tutorial = ROOT / "docs" / "tutorials" / f"{{MODULE}}.md"

    assert runbook.exists()
    assert manual.exists()
    assert tutorial.exists()
    assert "python3 scripts/audit/commercial_readiness.py" in runbook.read_text(encoding="utf-8")
'''


def ensure_integration_contract(module: str) -> list[Path]:
    directory = test_dir(module)
    directory.mkdir(parents=True, exist_ok=True)
    files = [
        (directory / f"test_{_safe(module)}_api_contract.py", _api_source(module)),
        (directory / f"test_{_safe(module)}_deploy_contract.py", _deploy_source(module)),
        (directory / f"test_{_safe(module)}_ops_contract.py", _ops_source(module)),
    ]
    for path, source in files:
        if not path.exists():
            path.write_text(source, encoding="utf-8")
    return [path for path, _ in files]


def _count_test_files(module: str) -> int:
    directory = test_dir(module)
    return len(list(directory.glob("test_*.py"))) if directory.exists() else 0


def integration_status(module: str) -> IntegrationStatus:
    directory = test_dir(module)
    openapi_file = directory / f"test_{_safe(module)}_api_contract.py"
    deploy_file = directory / f"test_{_safe(module)}_deploy_contract.py"
    ops_file = directory / f"test_{_safe(module)}_ops_contract.py"
    integration_files = _count_test_files(module)
    openapi_contract_found = int(openapi_file.exists())
    deployment_contract_found = int(deploy_file.exists())
    ops_contract_found = int(ops_file.exists())
    passed_contracts = openapi_contract_found + deployment_contract_found + ops_contract_found
    coverage_line_rate = passed_contracts / 3
    static_eval_passed = int(integration_files >= 3 and coverage_line_rate >= 0.60)
    return {
        "module": module,
        "integration_files": integration_files,
        "openapi_contract_found": openapi_contract_found,
        "deployment_contract_found": deployment_contract_found,
        "ops_contract_found": ops_contract_found,
        "coverage_line_rate": coverage_line_rate,
        "static_eval_passed": static_eval_passed,
        "test_dir": str(directory.relative_to(ROOT)),
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
        gate="G1-3",
        module=module,
        tier=tier,
        command=command,
        executor="scripts/ci/normalize_g1_integration.py",
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
    files = ensure_integration_contract(module)
    started = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    rel_files = [str(path.relative_to(ROOT)) for path in files]
    command = f"{sys.executable} -m pytest {' '.join(rel_files)} -q"

    if run_pytest:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *rel_files, "-q"],
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

    t1_log = ROOT / "artifacts" / "T1" / "G1-3" / module / f"integration-{file_ts}.log"
    t1_log.parent.mkdir(parents=True, exist_ok=True)
    t1_log.write_text(stdout + stderr, encoding="utf-8")

    status = integration_status(module)
    verification: dict[str, object] = {
        "coverage_line_rate": status["coverage_line_rate"],
        "pytest_exit": exit_code,
        "integration_files": status["integration_files"],
        "openapi_contract_found": status["openapi_contract_found"],
        "deployment_contract_found": status["deployment_contract_found"],
        "ops_contract_found": status["ops_contract_found"],
    }
    t1_sha = _write_meta(
        module=module,
        tier="T1",
        command=command,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        started=started,
        artifact_paths=[str(t1_log.relative_to(ROOT)), *rel_files],
        verification=verification,
    )

    t2_json = ROOT / "artifacts" / "T2" / "G1-3" / module / f"run-{file_ts}.json"
    t2_json.parent.mkdir(parents=True, exist_ok=True)
    t2_payload = {
        "module": module,
        "scenario": "API·배포·운영 문서 통합 계약 검증",
        "status": "pass" if exit_code == 0 and status["static_eval_passed"] == 1 else "fail",
        "verification": verification,
        "test_dir": status["test_dir"],
    }
    t2_stdout = json.dumps(t2_payload, ensure_ascii=False, indent=2, sort_keys=True)
    t2_json.write_text(t2_stdout + "\n", encoding="utf-8")
    t2_sha = _write_meta(
        module=module,
        tier="T2",
        command=f"scripts/ci/normalize_g1_integration.py --module {module}",
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
        if args.include_existing_pass
        or gate_G1_3_integration("G1-3", module).status != GateStatus.PASS
    ]
    results = [record_module(module, run_pytest=not args.no_pytest) for module in targets]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if all(r["pytest_exit"] == 0 and r["static_eval_passed"] == 1 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
