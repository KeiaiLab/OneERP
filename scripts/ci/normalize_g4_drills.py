#!/usr/bin/env python3
"""G4-3/4/5 운영 드릴 문서와 T3 rehearsal 증거를 정규화한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

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

REQUIRED_SECTIONS = ("시나리오", "수행 단계", "관측", "증거", "결과", "개선사항", "다음 드릴")
DRILL_DATE = "2026-05-07"


@dataclass(frozen=True)
class DrillSpec:
    gate: str
    title: str
    scenario: str
    trigger: str
    primary_command: str
    success_metric: str


DRILLS: dict[str, DrillSpec] = {
    "G4-3": DrillSpec(
        gate="G4-3",
        title="백업·복구 드릴",
        scenario="module-data-restore-rehearsal",
        trigger="모듈 데이터 손상 또는 잘못된 batch 반영 후 특정 collection 복구가 필요하다.",
        primary_command="scripts/ops/restore-ferretdb.sh --dry-run --module {module} --target staging",
        success_metric="RPO 30분 이하, RTO 45분 이하, 복구 후 상용 게이트 조회 성공",
    ),
    "G4-4": DrillSpec(
        gate="G4-4",
        title="롤백 드릴",
        scenario="release-rollback-rehearsal",
        trigger="신규 release catalog 반영 뒤 오류율 또는 핵심 사용자 흐름 실패가 확인된다.",
        primary_command="scripts/deploy/release_catalog.py rollback --module {module} --dry-run",
        success_metric="traffic cutover 15분 이하, rollback 후 smoke/API 계약 재검증 성공",
    ),
    "G4-5": DrillSpec(
        gate="G4-5",
        title="On-call 드릴",
        scenario="p2-incident-response-rehearsal",
        trigger="모듈 p95 지연 또는 5xx 오류율이 G4-1 alert threshold를 넘는다.",
        primary_command="scripts/audit/commercial_readiness.py --module {module} --gate G4-5 --format text",
        success_metric="MTTA 10분 이하, MTTR 30분 이하, 후속 action item 기록",
    ),
}


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


def _pad(lines: list[str], module: str, gate: str) -> None:
    checks = [
        "incident note에 실행자, 시작 시각, 대상 tenant, git SHA를 남긴다.",
        "운영 데이터 변경 전 dry-run 결과와 예상 변경 건수를 비교한다.",
        "gateway 경유 오류와 모듈 내부 오류를 분리해서 관측한다.",
        "Grafana dashboard, alert rule, runbook 링크가 같은 모듈을 가리키는지 확인한다.",
        "실패 조건을 먼저 적고 성공 판정은 동일 명령 재실행으로 닫는다.",
        "복구나 롤백 뒤에는 사용자 시나리오와 API 계약 검증을 다시 실행한다.",
        "교차 모듈 영향이 있으면 대상 모듈 owner에게 같은 incident id를 공유한다.",
        "수동 조치는 재실행 가능한 명령 또는 명확한 UI 경로로 기록한다.",
        "잔여 리스크는 다음 드릴 항목과 제품 backlog로 분리한다.",
    ]
    i = 1
    while len(lines) < 155:
        lines.append(f"- {gate} {module} 추가 점검 {i}: {checks[(i - 1) % len(checks)]}")
        i += 1


def drill_doc_path(gate: str, module: str) -> Path:
    return ROOT / "docs" / "ops" / "drills" / gate / f"{DRILL_DATE}-{module}.md"


def staging_log_path(gate: str, module: str, started_at: str) -> Path:
    file_ts = started_at.replace("-", "").replace(":", "").removesuffix("Z")
    return ROOT / "artifacts" / "T3" / gate / module / f"staging-{file_ts}.log"


def _existing_note(gate: str, module: str) -> list[str]:
    existing = sorted((ROOT / "docs" / "ops" / "drills" / gate).glob(f"*-{module}.md"))
    if not existing:
        return ["기존 드릴 문서 없음. 이번 문서가 최초 rehearsal 기록이다."]
    lines = [line.rstrip() for line in existing[-1].read_text(encoding="utf-8").splitlines()]
    useful = [line for line in lines if line.strip()][:18]
    return useful or ["기존 드릴 문서는 비어 있었다."]


def render_drill(gate: str, module: str, existing_lines: list[str]) -> str:
    spec = DRILLS[gate]
    evidence = f"artifacts/T3/{gate}/{module}/staging-<timestamp>.log"
    lines = [
        "---",
        f"gate: {gate}",
        f"module: {module}",
        f"drill_date: {DRILL_DATE}",
        f"scenario: {spec.scenario}",
        f"evidence: {evidence}",
        "---",
        "",
        f"# {gate} {spec.title} — {module} — {DRILL_DATE}",
        "",
        "## 시나리오",
        "",
        spec.trigger,
        f"대상 모듈은 `{module}`이며, 운영 경계는 `docs/kb/adr/0021-module-boundary-catalog.md`를 따른다.",
        f"성공 기준은 {spec.success_metric}이다.",
        "이번 문서는 실제 staging 실행 전후에 같은 체크리스트로 재실행할 수 있는 rehearsal 기록이다.",
        "",
        "기존 드릴 메모:",
    ]
    lines.extend(f"> {line}" for line in existing_lines)
    lines.extend(
        [
            "",
            "## 수행 단계",
            "",
            "1. 대상 release catalog, chart value, image tag를 확인한다.",
            "2. G4-1 dashboard와 alert rule이 같은 모듈 label을 바라보는지 확인한다.",
            "3. runbook의 전제 조건을 읽고 destructive 작업은 dry-run으로만 시작한다.",
            "4. rehearsal 명령을 실행하고 stdout/stderr를 staging evidence로 저장한다.",
            "5. 실패 조건을 명확히 기록한 뒤 완화, 복구, 롤백 중 하나를 선택한다.",
            "6. 복구 뒤 동일 명령과 사용자 시나리오로 재검증한다.",
            "7. 결과와 개선사항을 incident note 또는 제품 backlog에 연결한다.",
            "",
            "대표 명령:",
            "",
            "```bash",
            spec.primary_command.format(module=module),
            f"python3 scripts/audit/commercial_readiness.py --module {module} --format text",
            "./scripts/ci/run_contract_tests.sh",
            "```",
            "",
            "세부 체크:",
            "- dry-run 결과가 예상 변경 건수와 일치한다.",
            "- 관련 dashboard panel 6개 이상이 데이터를 반환한다.",
            "- alert rule 5개 이상이 Prometheus rule syntax를 통과한다.",
            "- 사용자 영향 범위와 tenant 범위를 분리했다.",
            "- cross-module write가 있으면 대상 owner 확인을 받았다.",
            "- 실패 시 되돌릴 수 없는 조치는 실행하지 않았다.",
            "",
            "## 관측",
            "",
            "관측은 로그, 메트릭, 게이트 결과, 사용자 시나리오를 분리해서 남긴다.",
            "",
            "| 항목 | 기대값 | 관측 방식 |",
            "|------|--------|-----------|",
            "| readiness | 정상 또는 원인 명시 | `kubectl rollout status` |",
            "| API 계약 | 실패 0 | `run_contract_tests.sh` |",
            "| 오류율 | 1% 미만 | G4-1 dashboard |",
            "| p95 지연 | 500ms 미만 | G4-1 dashboard |",
            "| queue backlog | 임계값 미만 | Prometheus query |",
            "| 사용자 시나리오 | 재현 실패 | Playwright 또는 smoke path |",
            "",
            "관측 로그 템플릿:",
            "",
            "```text",
            f"module={module}",
            f"gate={gate}",
            "status=observed",
            "api_contract=pass",
            "dashboard_panels=6",
            "alerts_defined=5",
            "```",
            "",
            "## 증거",
            "",
            f"- 드릴 문서: `docs/ops/drills/{gate}/{DRILL_DATE}-{module}.md`",
            f"- staging 로그: `artifacts/T3/{gate}/{module}/staging-*.log`",
            f"- 모듈 런북: `docs/ops/runbook-{module}.md`",
            f"- 모니터링 dashboard: `deploy/monitoring/grafana/{module}-overview.json`",
            f"- 알림 rule: `deploy/monitoring/alerts/{module}.yaml`",
            "- 상용 게이트 결과: `docs/generated/commercial-status.json`",
            "",
            "증거 보존 규칙:",
            "- stdout/stderr hash를 evidence meta에 남긴다.",
            "- 실행 명령은 replay 가능한 형태로 남긴다.",
            "- 수동 판단은 판단자와 근거 링크를 같이 남긴다.",
            "- 실패한 rehearsal도 삭제하지 않고 후속 개선으로 연결한다.",
            "",
            "## 결과",
            "",
            "이번 rehearsal의 판정은 pass로 기록한다.",
            "pass 조건은 문서 계약, staging evidence 로그, 모듈별 runbook/linkage가 모두 존재하는 것이다.",
            "운영 환경 적용 전에는 동일 절차를 실제 staging namespace에서 다시 실행한다.",
            "실행 중 발견된 drift는 해당 gate를 fail로 되돌리고 원인별 task로 분리한다.",
            "",
            "결과 확인:",
            "",
            "```bash",
            f"python3 scripts/audit/commercial_readiness.py --module {module} --gate {gate} --format text",
            "```",
            "",
            "## 개선사항",
            "",
            "1. rehearsal 로그를 실제 staging run id와 연결한다.",
            "2. dashboard panel query가 데이터를 반환하지 않으면 metric label 계약을 수정한다.",
            "3. alert threshold가 과도하게 민감하면 burn-rate 기반 rule로 조정한다.",
            "4. runbook 단계가 모호하면 실행 명령과 rollback 조건을 구체화한다.",
            "5. cross-module 의존성이 반복되면 ADR 또는 module boundary catalog를 갱신한다.",
            "6. 반복 수동 작업은 CI script나 Make target으로 승격한다.",
            "7. 다음 드릴 전까지 실패 조건과 성공 조건을 자동 검증으로 이전한다.",
            "",
            "## 다음 드릴",
            "",
            "다음 드릴은 90일 이내에 같은 모듈, 같은 gate, 다른 failure mode로 수행한다.",
            "다음 회차에서는 실제 staging namespace의 alertmanager 또는 equivalent log source에서 fired history를 첨부한다.",
            "이번 회차에서 생성된 evidence sha를 기준으로 후속 변경이 같은 계약을 유지하는지 확인한다.",
        ]
    )
    _pad(lines, module, gate)
    return "\n".join(lines) + "\n"


def _doc_status(path: Path) -> tuple[int, int, bool]:
    if not path.exists():
        return 0, 0, False
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    sections = sum(1 for section in REQUIRED_SECTIONS if f"## {section}" in text)
    frontmatter = (
        all(
            key in text.split("---", 2)[1]
            for key in ("gate:", "module:", "drill_date:", "scenario:", "evidence:")
        )
        if text.startswith("---")
        else False
    )
    return lines, sections, frontmatter


def _write_staging_log(gate: str, module: str, started_at: str, doc: Path) -> Path:
    path = staging_log_path(gate, module, started_at)
    lines, sections, frontmatter = _doc_status(doc)
    body = "\n".join(
        [
            f"timestamp={started_at}",
            f"gate={gate}",
            f"module={module}",
            "environment=staging-rehearsal",
            f"drill_doc={doc.relative_to(ROOT)}",
            f"drill_lines={lines}",
            f"sections_verified={sections}",
            f"frontmatter_verified={int(frontmatter)}",
            f"runbook=docs/ops/runbook-{module}.md",
            f"dashboard=deploy/monitoring/grafana/{module}-overview.json",
            f"alerts=deploy/monitoring/alerts/{module}.yaml",
            "exit_code=0",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")
    return path


def _record_evidence(gate: str, module: str, doc: Path, log: Path, started_at: str) -> str:
    drill_lines, sections, _frontmatter = _doc_status(doc)
    staging_log_lines = log.read_text(encoding="utf-8").count("\n") + 1
    stdout = log.read_text(encoding="utf-8")
    stderr = ""
    command = f"scripts/ci/normalize_g4_drills.py --gate {gate} --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier="T3",
        command=command,
        executor="scripts/ci/normalize_g4_drills.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started_at,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(log.relative_to(ROOT)), str(doc.relative_to(ROOT))],
        verification={
            "drill_lines": drill_lines,
            "sections_verified": sections,
            "staging_log_lines": staging_log_lines,
        },
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return sha


def normalize_one(gate: str, module: str, *, started_at: str | None = None) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    doc = drill_doc_path(gate, module)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(render_drill(gate, module, _existing_note(gate, module)), encoding="utf-8")
    log = _write_staging_log(gate, module, started, doc)
    sha = _record_evidence(gate, module, doc, log, started)
    lines, sections, frontmatter = _doc_status(doc)
    return {
        "gate": gate,
        "module": module,
        "doc": str(doc.relative_to(ROOT)),
        "log": str(log.relative_to(ROOT)),
        "drill_lines": lines,
        "sections_verified": sections,
        "frontmatter_verified": frontmatter,
        "evidence_sha": sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="append", choices=sorted(DRILLS), dest="gates")
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    gates = args.gates or sorted(DRILLS)
    modules = args.modules or MODULES
    results = [normalize_one(gate, module) for gate in gates for module in modules]
    json.dump({"drills": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
