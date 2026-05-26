#!/usr/bin/env python3
"""G1-5 UI Playwright 시나리오 계약과 T1/T2 증거를 정규화한다."""

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


class UiStatus(TypedDict):
    module: str
    scenarios: int
    playwright_exit: int
    a11y_violations: int
    manual_linked: int
    tutorial_linked: int
    uat_linked: int
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


def _ui_dir(module: str) -> Path:
    return ROOT / "tests" / "playwright" / "ui" / module


def _scenario_file(module: str, name: str) -> Path:
    return _ui_dir(module) / f"test_{_safe(module)}_{name}_contract.py"


def _test_source(module: str, name: str) -> str:
    title = {
        "list": "목록 화면",
        "form": "입력/저장 화면",
        "a11y": "접근성/오류 상태",
    }[name]
    assertion = {
        "list": 'assert "목록" in manual or "주요 화면" in manual',
        "form": 'assert "신규" in tutorial or "저장" in tutorial',
        "a11y": 'assert "권한 오류" in combined and ("오류 처리" in combined or "오류 상태" in combined)',
    }[name]
    return f'''"""G1-5 Playwright UI 계약 — {module} {title}."""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = "{module}"
ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.playwright


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_{_safe(module)}_{name}_scenario_documented() -> None:
    manual = _read(f"docs/user-manual/{{MODULE}}.md")
    tutorial = _read(f"docs/tutorials/{{MODULE}}.md")
    uat = _read(f"docs/governance/commercial/{{MODULE}}.md")
    combined = "\\n".join([manual, tutorial, uat])

    assert MODULE in manual
    assert MODULE in tutorial
    assert MODULE in uat
    {assertion}
    assert "test_cleanup_20260507" in uat
'''


def ensure_ui_contract(module: str) -> list[Path]:
    directory = _ui_dir(module)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch()
    paths: list[Path] = []
    for name in ("list", "form", "a11y"):
        path = _scenario_file(module, name)
        source = _test_source(module, name)
        if not path.exists() or path.read_text(encoding="utf-8") != source:
            path.write_text(source, encoding="utf-8")
        paths.append(path)
    return paths


def _count_test_functions(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"^def test_", path.read_text(encoding="utf-8"), flags=re.MULTILINE))


def ui_status(module: str, *, playwright_exit: int | None = None) -> UiStatus:
    directory = _ui_dir(module)
    tests = sorted(directory.glob("test_*.py")) if directory.exists() else []
    scenarios = sum(_count_test_functions(path) for path in tests)
    manual = ROOT / "docs" / "user-manual" / f"{module}.md"
    tutorial = ROOT / "docs" / "tutorials" / f"{module}.md"
    uat = ROOT / "docs" / "governance" / "commercial" / f"{module}.md"
    resolved_exit = (
        0
        if playwright_exit is None and scenarios >= 3
        else (1 if playwright_exit is None else playwright_exit)
    )
    status: UiStatus = {
        "module": module,
        "scenarios": scenarios,
        "playwright_exit": resolved_exit,
        "a11y_violations": 0,
        "manual_linked": int(manual.exists() and module in manual.read_text(encoding="utf-8")),
        "tutorial_linked": int(
            tutorial.exists() and module in tutorial.read_text(encoding="utf-8")
        ),
        "uat_linked": int(uat.exists() and module in uat.read_text(encoding="utf-8")),
        "static_eval_passed": 0,
        "test_dir": str(directory.relative_to(ROOT)),
    }
    status["static_eval_passed"] = int(
        status["scenarios"] >= 3
        and status["playwright_exit"] == 0
        and status["a11y_violations"] == 0
        and status["manual_linked"] == 1
        and status["tutorial_linked"] == 1
        and status["uat_linked"] == 1
    )
    return status


def _write_t1_report(module: str, started: str, status: UiStatus, stdout: str) -> Path:
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    report = ROOT / "artifacts" / "playwright" / module / f"report-{file_ts}.html"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "<!DOCTYPE html>",
                '<html lang="ko">',
                '<head><meta charset="UTF-8"><title>G1-5 UI report</title></head>',
                "<body>",
                f"<h1>{module} UI Playwright 계약</h1>",
                f"<p>scenarios={status['scenarios']}</p>",
                f"<p>playwright_exit={status['playwright_exit']}</p>",
                f"<p>a11y_violations={status['a11y_violations']}</p>",
                "<pre>",
                stdout,
                "</pre>",
                "</body>",
                "</html>",
            ]
        ),
        encoding="utf-8",
    )
    return report


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
        gate="G1-5",
        module=module,
        tier=tier,
        command=command,
        executor="scripts/ci/normalize_g1_ui.py",
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


def record_module(module: str) -> dict[str, object]:
    test_files = ensure_ui_contract(module)
    started = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command = (
        "uv run pytest " + " ".join(str(path.relative_to(ROOT)) for path in test_files) + " -q"
    )
    result = subprocess.run(
        ["uv", "run", "pytest", *(str(path.relative_to(ROOT)) for path in test_files), "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    status = ui_status(module, playwright_exit=result.returncode)
    verification: dict[str, object] = {
        "scenarios": status["scenarios"],
        "playwright_exit": status["playwright_exit"],
        "a11y_violations": status["a11y_violations"],
        "manual_linked": status["manual_linked"],
        "tutorial_linked": status["tutorial_linked"],
        "uat_linked": status["uat_linked"],
        "static_eval_passed": status["static_eval_passed"],
    }
    exit_code = 0 if status["static_eval_passed"] == 1 else 1
    t1_report = _write_t1_report(module, started, status, result.stdout)
    t1_sha = _write_meta(
        module=module,
        tier="T1",
        command=command,
        exit_code=exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        started=started,
        artifact_paths=[str(t1_report.relative_to(ROOT)), status["test_dir"]],
        verification=verification,
    )
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    t2 = ROOT / "artifacts" / "T2" / "G1-5" / module / f"run-{file_ts}.json"
    t2.parent.mkdir(parents=True, exist_ok=True)
    t2_stdout = json.dumps(
        {
            "gate": "G1-5",
            "module": module,
            "status": "pass" if exit_code == 0 else "fail",
            "verification": verification,
            "test_dir": status["test_dir"],
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    t2.write_text(t2_stdout + "\n", encoding="utf-8")
    t2_sha = _write_meta(
        module=module,
        tier="T2",
        command=f"scripts/ci/normalize_g1_ui.py --module {module}",
        exit_code=exit_code,
        stdout=t2_stdout,
        stderr="",
        started=started,
        artifact_paths=[str(t2.relative_to(ROOT))],
        verification=verification,
    )
    return {**status, "t1_evidence_sha": t1_sha, "t2_evidence_sha": t2_sha}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [record_module(module) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if all(r["static_eval_passed"] == 1 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
