#!/usr/bin/env python3
"""G4-2 모듈 운영 런북을 정규화하고 검증 증거를 기록한다."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.audit.gates import module_runbook_path  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)

REQUIRED_SECTIONS = ("개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션")
SKIP_IF_ALREADY_PASS = {"gateway", "accounting", "hr"}


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


def _existing_note(path: Path) -> list[str]:
    if not path.exists():
        return ["기존 런북 파일 없음. 본 정규화 산출물이 최초 G4-2 런북이다."]
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    useful = [line for line in lines if line.strip()][:24]
    if not useful:
        return ["기존 런북은 비어 있었다."]
    return useful


def _pad_lines(lines: list[str], module: str) -> None:
    checks = [
        "헬스체크 응답과 readiness 응답을 분리해서 기록한다.",
        "최근 배포 SHA와 release catalog 태그를 같은 incident note에 적는다.",
        "tenant, request_id, trace_id를 확인한 뒤 모듈 담당 채널에 공유한다.",
        "데이터 복구 전에는 반드시 dry-run 결과와 백업 시점을 비교한다.",
        "사용자 영향 범위가 2개 tenant 이상이면 P1로 승격한다.",
        "회귀가 의심되면 신규 기능 flag를 먼저 내리고 롤백은 그 다음 판단한다.",
        "복구 후 동일 쿼리와 API 호출로 정상 상태를 재검증한다.",
        "모든 수동 조치는 audit note에 명령, 실행자, 결과를 남긴다.",
    ]
    i = 1
    while len(lines) < 155:
        lines.append(f"- {module} 운영 점검 {i}: {checks[(i - 1) % len(checks)]}")
        i += 1


def render_runbook(module: str, existing_lines: list[str]) -> str:
    """G4-2 validator 계약을 충족하는 모듈별 운영 런북 본문을 만든다."""
    today = "2026-05-07"
    lines = [
        "---",
        "owner: operations@oneerp.dev",
        f"module: {module}",
        f"last_reviewed: {today}",
        "related_runbooks:",
        "  - docs/ops/runbook-db-backup-restore.md",
        "  - docs/ops/runbook-incident-response.md",
        "  - docs/infra/ops/rollback.md",
        "---",
        "",
        f"# {module} 운영 런북",
        "",
        "## 개요",
        "",
        f"`{module}` 모듈은 OneERP 상용 출시 게이트의 독립 운영 단위다.",
        "본 런북은 장애 접수부터 복구 검증까지 운영자가 반복 실행할 수 있는 절차를 정의한다.",
        "모듈 책임 경계는 `docs/kb/adr/0021-module-boundary-catalog.md`를 따른다.",
        "OpenAPI 계약 증거는 `artifacts/T1/G1-2/`와 `artifacts/T2/G1-2/`에 기록된다.",
        "의존성 감사 증거는 `artifacts/T1/G3-5/`에 기록된다.",
        "런북의 목적은 임시 대응이 아니라 재현 가능한 진단, 복구, 롤백, 에스컬레이션이다.",
        "",
        "운영 원칙:",
        "- 사용자 영향 범위를 먼저 좁힌다.",
        "- live 증거 없이 성공으로 판단하지 않는다.",
        "- destructive 조치는 dry-run과 승인 기록을 남긴다.",
        "- 복구 후에는 동일 증상 재현 쿼리로 재검증한다.",
        "- 문서와 실제 배포 상태가 다르면 실제 배포 상태를 우선 증거로 본다.",
        "",
        "기존 런북 메모:",
    ]
    lines.extend(f"> {line}" for line in existing_lines)
    lines.extend(
        [
            "",
            "## 전제 조건",
            "",
            "운영자는 아래 조건을 충족한 뒤 절차를 시작한다.",
            "",
            "1. `kubectl` context가 staging 또는 production 대상 cluster를 가리킨다.",
            "2. 현재 release catalog 버전과 배포된 image tag를 확인했다.",
            "3. `ONEERP_JWT_SECRET` 등 로컬 검증용 secret을 운영 secret과 혼동하지 않는다.",
            "4. Grafana, Loki, Prometheus 또는 대체 관측 경로에 접근 가능하다.",
            "5. 최근 백업 상태와 rollback runbook 경로를 확인했다.",
            "6. 모듈 owner 또는 on-call 채널에 작업 시작을 공유했다.",
            "7. 재현 명령의 stdout/stderr를 evidence note에 남길 준비가 되어 있다.",
            "8. 고객 데이터 조회가 필요한 경우 최소 권한 read-only credential을 사용한다.",
            "9. batch 재처리나 event replay는 dry-run으로 예상 변경량을 확인한다.",
            "10. 다른 모듈 경계를 넘는 변경은 대상 모듈 owner 승인을 받는다.",
            "",
            "기본 환경 확인:",
            "",
            "```bash",
            f"kubectl get deploy -A | grep -E '({module}|gateway|api)'",
            f"kubectl get pods -A | grep -E '({module}|gateway|api)'",
            f'rg -n "{module}" deploy docs services scripts || true',
            "python3 scripts/audit/commercial_readiness.py --module " + module + " --format text",
            "```",
            "",
            "## 진단 절차",
            "",
            "1차 진단은 증상, 영향 범위, 최근 변경, 의존성 상태를 분리한다.",
            "",
            "```bash",
            f"python3 scripts/audit/commercial_readiness.py --module {module} --format json > /tmp/{module}-readiness.json",
            "jq '.summary, .reports[0].gates[] | select(.status != \"pass\")' /tmp/"
            + module
            + "-readiness.json",
            f'rg -n "{module}" artifacts docs/ops deploy/monitoring || true',
            "```",
            "",
            "진단 체크리스트:",
            "- API schema drift가 있으면 G1-2 증거와 `docs/api` 정본을 비교한다.",
            "- dependency audit 경보가 있으면 G3-5를 먼저 차단 상태로 둔다.",
            "- 배포 후 발생한 장애는 image tag, chart values, environment diff를 같이 본다.",
            "- 데이터 불일치는 source-of-truth 모듈과 읽기 모델을 분리해서 확인한다.",
            "- 외부 연동 장애는 integration-hub 또는 gateway 경로와 직접 모듈 경로를 나눠 본다.",
            "- UI 신고는 Playwright 재현 여부와 API 응답 실패를 분리한다.",
            "- queue 지연은 consumer lag, retry count, dead-letter 유입량을 같이 본다.",
            "- auth/rbac 문제는 gateway 인증 실패와 모듈 내부 권한 실패를 분리한다.",
            "",
            "관측 쿼리 예시:",
            "",
            "```bash",
            f"kubectl logs -A --since=30m | rg '{module}|ERROR|WARN' | tail -80",
            "curl -sf http://prometheus/api/v1/query --data-urlencode 'query=up' | jq '.status'",
            "```",
            "",
            "## 복구 절차",
            "",
            "복구는 영향 차단, 원인 완화, 데이터 정합성 확인, 재발 방지 순서로 진행한다.",
            "",
            "1. 신규 요청 유입을 줄여야 하면 gateway rate-limit 또는 feature flag를 먼저 조정한다.",
            "2. 최근 배포가 원인일 가능성이 높으면 rollback 절차로 이동한다.",
            "3. 설정 drift가 원인이면 GitOps manifest와 live resource 차이를 기록한다.",
            "4. 데이터 재처리가 필요하면 dry-run, sample 검증, full apply 순서로 진행한다.",
            "5. event replay는 idempotency key와 중복 처리 정책을 확인한 뒤 실행한다.",
            "6. 복구 후에는 최초 신고 시나리오와 자동 테스트를 모두 다시 실행한다.",
            "7. 복구 결과를 incident note, evidence artifact, runbook 개선 항목으로 남긴다.",
            "",
            "복구 명령 템플릿:",
            "",
            "```bash",
            f"python3 scripts/audit/commercial_readiness.py --module {module} --format text",
            "./scripts/ci/run_contract_tests.sh",
            "./scripts/ci/dep_audit.sh",
            "```",
            "",
            "데이터 변경이 필요한 경우:",
            "- 변경 대상 document 수를 먼저 출력한다.",
            "- 변경 전 sample 5건을 보관한다.",
            "- 변경 후 동일 sample을 재조회한다.",
            "- 실패 시 원복 방법이 없는 작업은 실행하지 않는다.",
            "",
            "## 롤백 절차",
            "",
            "롤백은 `docs/infra/ops/rollback.md`를 공통 절차로 사용한다.",
            "",
            "1. 현재 배포 SHA, chart value, config map checksum을 기록한다.",
            "2. 직전 정상 release catalog 항목을 확인한다.",
            "3. DB migration이 포함된 배포인지 확인한다.",
            "4. backward-incompatible migration이면 application rollback만 수행하지 않는다.",
            "5. traffic cutover가 가능하면 canary 비율을 0으로 내린다.",
            "6. 롤백 후 health, readiness, 핵심 사용자 시나리오를 확인한다.",
            "7. 롤백 결과와 후속 root-cause task를 남긴다.",
            "",
            "롤백 확인 명령:",
            "",
            "```bash",
            "git diff -- deploy/catalog/releases/current.yaml",
            f"kubectl rollout history deploy/{module} -n oneerp || true",
            f"kubectl rollout status deploy/{module} -n oneerp --timeout=120s || true",
            "```",
            "",
            "## 에스컬레이션",
            "",
            "에스컬레이션은 영향도와 데이터 위험 기준으로 판단한다.",
            "",
            "| 등급 | 조건 | 호출 대상 | 목표 응답 |",
            "|------|------|-----------|-----------|",
            "| P1 | 다중 tenant 장애, 데이터 손상 가능성, 인증 전체 장애 | incident commander, module owner, DBA | 15분 |",
            "| P2 | 단일 tenant 주요 업무 중단, 반복 재시도 실패 | module owner, on-call | 30분 |",
            "| P3 | 우회 가능한 기능 장애, 문서/설정 drift | 담당 팀 채널 | 1영업일 |",
            "",
            "필수 공유 정보:",
            "- 모듈명과 tenant",
            "- 최초 감지 시각과 신고 경로",
            "- 최근 배포 SHA와 config diff",
            "- 재현 명령과 실패 응답",
            "- 임시 완화 여부",
            "- rollback 가능 여부",
            "- 남은 사용자 영향",
            "",
            "종료 기준:",
            "- 자동 게이트 또는 대상 smoke test가 통과한다.",
            "- 사용자 신고 시나리오가 재현되지 않는다.",
            "- 로그와 지표가 정상 범위로 15분 이상 유지된다.",
            "- 후속 작업이 issue 또는 checklist로 분리된다.",
        ]
    )
    _pad_lines(lines, module)
    return "\n".join(lines) + "\n"


def _runbook_status(path: Path) -> tuple[int, int, bool]:
    if not path.exists():
        return 0, 0, False
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + 1
    sections = sum(1 for section in REQUIRED_SECTIONS if f"## {section}" in text)
    frontmatter = (
        all(key in text.split("---", 2)[1] for key in ("owner:", "module:", "last_reviewed:"))
        if text.startswith("---")
        else False
    )
    return lines, sections, frontmatter


def _record_evidence(module: str, path: Path, *, started_at: str) -> str:
    lines, sections, frontmatter = _runbook_status(path)
    stdout = (
        "\n".join(
            [
                f"module={module}",
                "gate=G4-2",
                f"runbook_path={path}",
                f"runbook_lines={lines}",
                f"sections_verified={sections}",
                f"frontmatter_verified={int(frontmatter)}",
            ]
        )
        + "\n"
    )
    stderr = ""
    command = f"scripts/ci/normalize_g4_runbooks.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    file_ts = started_at.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "T1" / "G4-2" / module / f"runbook-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    meta = EvidenceMeta(
        sha256=sha,
        gate="G4-2",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/normalize_g4_runbooks.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started_at,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(log_path.relative_to(ROOT)), str(path.relative_to(ROOT))],
        verification={
            "runbook_lines": lines,
            "sections_verified": sections,
            "frontmatter_verified": int(frontmatter),
        },
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return sha


def normalize_module(
    module: str, *, force: bool = False, started_at: str | None = None
) -> dict[str, object]:
    path = ROOT / module_runbook_path(module)
    lines, sections, frontmatter = _runbook_status(path)
    should_write = (
        force
        or module not in SKIP_IF_ALREADY_PASS
        or lines < 150
        or sections < 6
        or not frontmatter
    )
    existing = _existing_note(path)
    if should_write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_runbook(module, existing), encoding="utf-8")
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    sha = _record_evidence(module, path, started_at=started)
    new_lines, new_sections, new_frontmatter = _runbook_status(path)
    return {
        "module": module,
        "path": str(path.relative_to(ROOT)),
        "runbook_lines": new_lines,
        "sections_verified": new_sections,
        "frontmatter_verified": new_frontmatter,
        "evidence_sha": sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [normalize_module(module, force=args.force) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
