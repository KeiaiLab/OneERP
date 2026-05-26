"""G1-4 수동 mutation catalog — audit_hooks 모듈의 kill rate 측정.

mutmut 3.5.0 이 OneERP conftest(parents[2] 기반 service_root 탐지) 와
호환되지 않는 환경 제약(2026-04-22 확인) 때문에 bounded scope 로 수동 mutation
catalog 를 집행한다. 각 mutation 을 소스에 주입 → pytest 실행 → kill/survive
판정 → 복원 순으로 진행.

Mutation 종류:
- arithmetic: 산술 연산자 치환 — 대상 파일에는 없음
- boolean: `in` → `not in`
- return / assignment: prefix 문자열, 기본값 None
- literal: 허용 액션 tuple 요소 제거·변형, prefix 문자열 변형

결과:
- accounting: artifacts/T1/G1-4/accounting/mutmut-summary.json
- hr:         artifacts/T1/G1-4/hr/mutmut-summary.json
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Mutation:
    mid: str
    description: str
    old: str
    new: str


ACCOUNTING_FILE = REPO / "services/finance/accounting/oneerp_accounting_app/audit_hooks.py"
ACCOUNTING_TEST = "tests/unit/test_audit_mutation.py"
ACCOUNTING_CWD = REPO / "services/finance/accounting"
ACCOUNTING_PKG = "oneerp-accounting"

HR_FILE = REPO / "services/hr/hr/oneerp_hr_app/audit_hooks.py"
HR_TEST = "tests/unit/test_audit_hooks_mutation.py"
HR_CWD = REPO / "services/hr/hr"
HR_PKG = "oneerp-hr"

# 각 Mutation 은 대상 파일의 unique substring 을 치환한다.
ACCOUNTING_MUTATIONS: list[Mutation] = [
    Mutation(
        "M01",
        "boolean: `action not in MODULE_ACTIONS` → `action in MODULE_ACTIONS`",
        "if action not in MODULE_ACTIONS:",
        "if action in MODULE_ACTIONS:",
    ),
    Mutation(
        "M02",
        "literal: `accounting.unknown.` → `accounting.KNOWN.` (prefix 변조)",
        'action = f"accounting.unknown.{action}"',
        'action = f"accounting.KNOWN.{action}"',
    ),
    Mutation(
        "M03",
        "literal: unknown prefix 제거 — f-string 을 action 원본으로 치환",
        'action = f"accounting.unknown.{action}"',
        "action = action",
    ),
    Mutation(
        "M04",
        "literal: MODULE_ACTIONS 에서 accounting.post 제거",
        '    "accounting.post",\n',
        "",
    ),
    Mutation(
        "M05",
        "literal: accounting.create → accounting.CREATE",
        '    "accounting.create",',
        '    "accounting.CREATE",',
    ),
    Mutation(
        "M06",
        "default: details or {} → details (None 누수)",
        "details=details or {},",
        "details=details,",
    ),
    Mutation(
        "M07",
        'identity: actor=actor → actor=""',
        "actor=actor,",
        'actor="",',
    ),
    Mutation(
        "M08",
        'identity: tenant_id=tenant_id → tenant_id=""',
        "tenant_id=tenant_id,",
        'tenant_id="",',
    ),
    Mutation(
        "M09",
        'identity: resource=resource → resource=""',
        "resource=resource,",
        'resource="",',
    ),
    Mutation(
        "M10",
        "call 삭제: emit_audit_event 호출 전체 제거 (pass 로 치환)",
        "    emit_audit_event(\n"
        "        AuditEvent(\n"
        "            actor=actor,\n"
        "            action=action,\n"
        "            resource=resource,\n"
        "            tenant_id=tenant_id,\n"
        "            details=details or {},\n"
        "        ),\n"
        "    )",
        "    pass",
    ),
]

HR_MUTATIONS: list[Mutation] = [
    Mutation(
        "M01",
        "boolean: `action not in MODULE_ACTIONS` → `action in MODULE_ACTIONS`",
        "if action not in MODULE_ACTIONS:",
        "if action in MODULE_ACTIONS:",
    ),
    Mutation(
        "M02",
        "literal: hr.unknown. prefix → hr.KNOWN.",
        'action = f"hr.unknown.{action}"',
        'action = f"hr.KNOWN.{action}"',
    ),
    Mutation(
        "M03",
        "literal: unknown prefix 제거",
        'action = f"hr.unknown.{action}"',
        "action = action",
    ),
    Mutation(
        "M04",
        "literal: hr.create 제거",
        '    "hr.create",\n',
        "",
    ),
    Mutation(
        "M05",
        "literal: hr.update → hr.UPDATE",
        '    "hr.update",',
        '    "hr.UPDATE",',
    ),
    Mutation(
        "M06",
        "default: details or {} → details",
        "details=details or {},",
        "details=details,",
    ),
    Mutation(
        "M07",
        'identity: actor=actor → actor=""',
        "actor=actor,",
        'actor="",',
    ),
    Mutation(
        "M08",
        'identity: tenant_id=tenant_id → tenant_id=""',
        "tenant_id=tenant_id,",
        'tenant_id="",',
    ),
    Mutation(
        "M09",
        'identity: action=action → action="hr.create"',
        "action=action,",
        'action="hr.create",',
    ),
    Mutation(
        "M10",
        "call 삭제: emit_audit_event 호출 제거",
        "    emit_audit_event(\n"
        "        AuditEvent(\n"
        "            actor=actor,\n"
        "            action=action,\n"
        "            resource=resource,\n"
        "            tenant_id=tenant_id,\n"
        "            details=details or {},\n"
        "        ),\n"
        "    )",
        "    pass",
    ),
]


def run_tests(cwd: Path, pkg: str, test_path: str) -> int:
    """pytest 실행 후 exit code 반환 (0 = pass, non-0 = fail)."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "--package",
            pkg,
            "pytest",
            "-x",
            "-q",
            "--no-header",
            test_path,
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return result.returncode


def apply_mutation(file: Path, mutation: Mutation) -> None:
    content = file.read_text(encoding="utf-8")
    if mutation.old not in content:
        raise RuntimeError(
            f"mutation {mutation.mid} old_string not found: {mutation.old!r}",
        )
    if content.count(mutation.old) != 1:
        raise RuntimeError(
            f"mutation {mutation.mid} old_string not unique "
            f"({content.count(mutation.old)} occurrences)",
        )
    file.write_text(content.replace(mutation.old, mutation.new), encoding="utf-8")


def run_module(
    module_name: str,
    file: Path,
    test_path: str,
    cwd: Path,
    pkg: str,
    mutations: list[Mutation],
    out_path: Path,
) -> dict:
    original = file.read_text(encoding="utf-8")
    baseline_rc = run_tests(cwd, pkg, test_path)
    if baseline_rc != 0:
        raise RuntimeError(f"baseline tests fail for {module_name} (rc={baseline_rc})")

    results = []
    killed = 0
    for mutation in mutations:
        try:
            apply_mutation(file, mutation)
            rc = run_tests(cwd, pkg, test_path)
        finally:
            file.write_text(original, encoding="utf-8")
        status = "killed" if rc != 0 else "survived"
        if status == "killed":
            killed += 1
        results.append(
            {
                "id": mutation.mid,
                "description": mutation.description,
                "status": status,
                "exit_code": rc,
            },
        )

    total = len(mutations)
    survived = total - killed
    score_pct = round(killed / total * 100, 2) if total else 0.0
    summary = {
        "module": module_name,
        "tool": "manual-mutation-catalog",
        "note": (
            "mutmut 3.5.0 이 OneERP conftest 와 호환 실패 → 수동 mutation catalog 로 대체. "
            "실제 소스 치환 후 pytest 실행 · 결과 실측."
        ),
        "target_file": str(file.relative_to(REPO)),
        "test_file": test_path,
        "total": total,
        "killed": killed,
        "survived": survived,
        "score_pct": score_pct,
        "timestamp": datetime.now(UTC).isoformat(),
        "mutations": results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    art_root = REPO / "artifacts/T1/G1-4"
    acc = run_module(
        "accounting",
        ACCOUNTING_FILE,
        ACCOUNTING_TEST,
        ACCOUNTING_CWD,
        ACCOUNTING_PKG,
        ACCOUNTING_MUTATIONS,
        art_root / "accounting/mutmut-summary.json",
    )
    hr = run_module(
        "hr",
        HR_FILE,
        HR_TEST,
        HR_CWD,
        HR_PKG,
        HR_MUTATIONS,
        art_root / "hr/mutmut-summary.json",
    )
    print(f"accounting: killed {acc['killed']}/{acc['total']} = {acc['score_pct']}%")
    print(f"hr:         killed {hr['killed']}/{hr['total']} = {hr['score_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
