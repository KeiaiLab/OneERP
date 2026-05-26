# Docs Health Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 5 개의 독립 docs 건강성 체커(S1~S5) + 통합 러너 `audit-all.sh` 를 `scripts/docs/` 에 신설하고, 초기 cleanup 을 반영하여 `audit-all.sh` 가 exit 0 로 끝나게 만든다. spec: `docs/superpowers/specs/2026-04-13-docs-health-audit-design.md`.

**Architecture:** 각 체커는 `main(args: list[str]) -> int` 엔트리포인트 + standalone 실행. fixture 디렉토리를 `core/tests/fixtures/docs/<track>-sample/` 에 두고 단위 테스트에서 tmp_path 로 복사 후 체커 실행, exit code/stdout/파일 변경 검증. S3 는 plane in-process import + OpenAPI 비교(가장 무거움), S5 는 백틱 토큰 heuristic, S1/S2/S4 는 가벼운 파일 스캔.

**Tech Stack:** Python 3.14, pytest, uv workspace, ruff, ty, FastAPI(`app.openapi()`), regex, markdown 텍스트 파싱.

**File Structure:**

| 파일 | 트랙 | 작업 |
|---|---|---|
| `scripts/docs/check_stale_refs.py` | S1 | Create |
| `scripts/docs/render_versions.py` | S2 | Modify |
| `scripts/docs/audit_api_drift.py` | S3 | Create |
| `scripts/docs/audit_tutorials.py` | S4 | Create |
| `scripts/docs/audit_architecture.py` | S5 | Create |
| `scripts/docs/audit-all.sh` | 통합 | Create |
| `core/tests/unit/docs/test_check_stale_refs.py` | S1 | Create |
| `core/tests/unit/docs/test_render_versions.py` | S2 | Create |
| `core/tests/unit/docs/test_audit_api_drift.py` | S3 | Create |
| `core/tests/unit/docs/test_audit_tutorials.py` | S4 | Create |
| `core/tests/unit/docs/test_audit_architecture.py` | S5 | Create |
| `core/tests/fixtures/docs/**` | 전트랙 | Create |
| `docs/developer/01-add-new-service.md` | cleanup S1 | Modify |
| `docs/security/OWASP-CHECKLIST.md` | cleanup S1 | Modify |
| `docs/engineering/msa/CONSOLIDATION.md` | cleanup S1 | Modify |
| `docs/onboarding/QUICKSTART.md` | cleanup S1 | Modify |
| `docs/engineering/msa/RUNBOOK-cluster-merge.md` | cleanup S1 | Delete |
| `docs/generated/api-drift-report.md` | cleanup S3 | Create |
| `docs/generated/architecture-audit-2026-04-13.md` | cleanup S5 | Create |
| `README.md` | 통합 | Modify (1 문단 append) |

---

## Task 0: 선행 정리 + 기준선

**Files:** 없음(환경 검증만).

- [ ] **Step 1: 브랜치·워킹트리 상태 확인**

Run:
```
cd /Users/phil/WorkSpace/apps/OneErp
git branch --show-current
git status --short | head -5
```
Expected: `main` 브랜치, 본 작업과 무관한 수정 없음.

- [ ] **Step 2: 기존 체커가 동작하는지 기준선 확인**

Run:
```
uv run python scripts/docs/check_integrity.py 2>&1 | tail -3
uv run python scripts/docs/render_versions.py 2>&1 | tail -3
```
Expected: `check_integrity` 는 통과 또는 이슈 리포트. `render_versions` 는 `docs/onboarding/00-quickstart.md` 부재로 오류 또는 drift 보고 가능(이게 S2 에서 고칠 대상).

- [ ] **Step 3: fixture 루트 디렉토리 준비**

Run:
```
mkdir -p core/tests/unit/docs
mkdir -p core/tests/fixtures/docs
```
Expected: 디렉토리 생성 확인. 이후 Task 들이 여기에 파일을 추가.

- [ ] **Step 4: 품질 게이트 기준선**

Run:
```
uv run ruff check scripts/docs/ 2>&1 | tail -3
uv run ty check scripts/docs/ 2>&1 | tail -3
```
Expected: 현재 상태 기록. 이후 신규 체커 추가 후 동일 명령이 계속 통과해야 함.

---

## Task 1: S1 `check_stale_refs.py` — fixture + 실패 테스트

**Files:**
- Create: `core/tests/fixtures/docs/stale-ref-sample/README.md`
- Create: `core/tests/fixtures/docs/stale-ref-sample/good.md`
- Create: `core/tests/fixtures/docs/stale-ref-sample/dead-link.md`
- Create: `core/tests/unit/docs/__init__.py`
- Create: `core/tests/unit/docs/test_check_stale_refs.py`

- [ ] **Step 1: fixture 파일 3개 생성**

`core/tests/fixtures/docs/stale-ref-sample/README.md`:
```markdown
# 테스트 픽스처
이 파일에는 스테일 참조가 있다: `docker-compose.local.yml` 과 `.gitea/workflows/ci.yml`.
그리고 `services/sales/selling/Dockerfile` 도 언급.
```

`core/tests/fixtures/docs/stale-ref-sample/good.md`:
```markdown
# 정상 문서
이 문서에는 스테일 참조 없음. 유효 링크만: [README](./README.md).
```

`core/tests/fixtures/docs/stale-ref-sample/dead-link.md`:
```markdown
# 죽은 링크 샘플
[없는 파일](./missing.md) 로 가는 링크가 있다.
```

- [ ] **Step 2: `core/tests/unit/docs/__init__.py` 빈 파일 생성**

```
touch core/tests/unit/docs/__init__.py
```

- [ ] **Step 3: 실패 테스트 작성 — `core/tests/unit/docs/test_check_stale_refs.py`**

```python
"""check_stale_refs 체커 단위 테스트."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "check_stale_refs.py"
FIXTURE_ROOT = ROOT / "core" / "tests" / "fixtures" / "docs" / "stale-ref-sample"


def _load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"체커 모듈이 없습니다: {SCRIPT_PATH}")
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_stale_refs", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_stale_refs"] = mod
    spec.loader.exec_module(mod)
    return mod


def _copy_fixture(tmp_path: Path) -> Path:
    dst = tmp_path / "docs"
    shutil.copytree(FIXTURE_ROOT, dst)
    return dst


def test_스테일_참조_검출_시_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    fixture = _copy_fixture(tmp_path)

    rc = mod.main(["--root", str(fixture)])
    out = capsys.readouterr().out

    assert rc == 1
    assert "docker-compose.local.yml" in out
    assert ".gitea/" in out
    assert "services/sales/selling/Dockerfile" in out


def test_죽은_링크_검출_시_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    fixture = _copy_fixture(tmp_path)

    rc = mod.main(["--root", str(fixture)])
    out = capsys.readouterr().out

    assert rc == 1
    assert "dead-link" in out or "missing.md" in out


def test_fix_dead_links_적용_후_재실행_exit_0(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    mod = _load_module()
    fixture = _copy_fixture(tmp_path)

    # 먼저 stale-ref 가 있는 README.md 를 제거하여 dead-link 만 남긴다.
    (fixture / "README.md").unlink()

    rc1 = mod.main(["--root", str(fixture)])
    assert rc1 == 1

    rc2 = mod.main(["--root", str(fixture), "--fix-dead-links"])
    # --fix 는 교정 후 변경 건수를 반환하므로 exit 0 가능.
    # 이어서 재실행하면 죽은 링크 없음 → exit 0.
    rc3 = mod.main(["--root", str(fixture)])
    assert rc3 == 0
```

- [ ] **Step 4: FAIL 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_check_stale_refs.py -v
```
Expected: 3 tests FAIL with "체커 모듈이 없습니다" pytest.fail.

- [ ] **Step 5: 커밋 (fixture + red tests)**

```
git add core/tests/unit/docs/__init__.py core/tests/unit/docs/test_check_stale_refs.py core/tests/fixtures/docs/stale-ref-sample/
git commit -m "test(docs): S1 check_stale_refs fixture + red tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: S1 `check_stale_refs.py` 구현

**Files:**
- Create: `scripts/docs/check_stale_refs.py`

- [ ] **Step 1: 체커 구현**

```python
#!/usr/bin/env python3
"""삭제된 자산 참조와 죽은 마크다운 로컬 링크를 검출·교정하는 체커(S1).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.1
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

STALE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"docker-compose\.(local|plane)\.yml"),
    re.compile(r"\.gitea/"),
    re.compile(r"services/[^/\s`'\"]+/[^/\s`'\"]+/Dockerfile"),
    re.compile(r"scripts/migration/"),
    re.compile(r"devspace\.yaml"),
    re.compile(r"docs/HANDOFF-NEXT-SESSION\.md"),
    re.compile(r"docs/STATUS\.md"),
    re.compile(r"docs/gap-analysis-[\w-]+\.md"),
    re.compile(r"RALPH-LOOP-PROMPT\.md"),
    re.compile(r"AUDIT-REPORT-[\d-]+\.md"),
]

DOC_GLOBS = ["docs/**/*.md", "README.md", "AGENTS.md", ".claude/*.md"]
EXCLUDE_SUBSTR = ["docs/generated/"]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class Finding:
    file: Path
    line: int
    kind: str  # "stale-ref" | "dead-link"
    detail: str


def _iter_target_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in DOC_GLOBS:
        for p in root.glob(pattern):
            if p.is_file() and not any(e in str(p) for e in EXCLUDE_SUBSTR):
                files.add(p)
    return sorted(files)


def _scan_stale(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in STALE_PATTERNS:
            m = pat.search(line)
            if m:
                findings.append(
                    Finding(path, lineno, "stale-ref", m.group(0)),
                )
    return findings


def _scan_dead_links(path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            target = m.group(2).strip()
            # 앵커, 외부 scheme, mailto, 이미지 절대경로는 스킵.
            if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            # 앵커만 있는 경우(예: #section) 위에서 처리됨.
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            # 상대 경로 기준으로 해석.
            resolved = (path.parent / target_path).resolve()
            if not resolved.exists():
                findings.append(
                    Finding(path, lineno, "dead-link", target),
                )
    return findings


def _fix_dead_links(path: Path, root: Path) -> int:
    """죽은 링크를 plain 텍스트로 변환하고 교정 건수를 반환한다."""
    text = path.read_text(encoding="utf-8")
    fixed_count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal fixed_count
        label, target = match.group(1), match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            return match.group(0)
        target_path = target.split("#", 1)[0]
        if not target_path:
            return match.group(0)
        resolved = (path.parent / target_path).resolve()
        if not resolved.exists():
            fixed_count += 1
            return label
        return match.group(0)

    new_text = LINK_RE.sub(_repl, text)
    if fixed_count > 0:
        path.write_text(new_text, encoding="utf-8")
    return fixed_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="docs stale references + dead local links")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--fix-dead-links", action="store_true")
    parser.add_argument("--fix", action="store_true", help="alias for --fix-dead-links")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    fix_mode = args.fix_dead_links or args.fix

    findings: list[Finding] = []
    for file in _iter_target_files(args.root):
        findings.extend(_scan_stale(file))
        findings.extend(_scan_dead_links(file, args.root))

    if fix_mode:
        total_fixed = 0
        for file in _iter_target_files(args.root):
            total_fixed += _fix_dead_links(file, args.root)
        print(f"[fix] dead-link 교정: {total_fixed} 건")
        # 재스캔하여 잔여 검출.
        findings = []
        for file in _iter_target_files(args.root):
            findings.extend(_scan_stale(file))
            findings.extend(_scan_dead_links(file, args.root))

    if args.json:
        import json

        payload = [
            {
                "file": str(f.file.relative_to(args.root)),
                "line": f.line,
                "kind": f.kind,
                "detail": f.detail,
            }
            for f in findings
        ]
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for f in findings:
            rel = f.file.relative_to(args.root) if args.root in f.file.parents else f.file
            print(f"[{f.kind}] {rel}:{f.line} → {f.detail}")
        stale_cnt = sum(1 for f in findings if f.kind == "stale-ref")
        dead_cnt = sum(1 for f in findings if f.kind == "dead-link")
        print(f"총 {len(findings)} 건 감지 (stale-ref {stale_cnt}, dead-link {dead_cnt}).")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 테스트 PASS 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_check_stale_refs.py -v
```
Expected: 3 tests PASS.

- [ ] **Step 3: 린트/타입**

Run:
```
uv run ruff check scripts/docs/check_stale_refs.py core/tests/unit/docs/test_check_stale_refs.py
uv run ty check scripts/docs/check_stale_refs.py
```
Expected: All checks passed.

- [ ] **Step 4: 커밋**

```
git add scripts/docs/check_stale_refs.py
git commit -m "feat(docs): S1 check_stale_refs 체커 — 스테일 참조 + 죽은 링크 검출

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.1

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: S2 `render_versions.py` 수정 + 테스트

**Files:**
- Modify: `scripts/docs/render_versions.py`
- Create: `core/tests/unit/docs/test_render_versions.py`

- [ ] **Step 1: `render_versions.py` 의 `TARGETS` 에서 삭제된 파일 제거**

`scripts/docs/render_versions.py` 를 열어 `TARGETS` 또는 유사 상수에서 다음을 **제거**:
- `docs/onboarding/00-quickstart.md`
- `docs/engineering/standards.md`

유지: `README.md`, `.claude/CLAUDE.md`.

또한 파일 존재 검사 로직 추가: target 이 존재하지 않으면 `WARNING: {target} 없음 — skip` 출력 후 다음 target 으로 진행(에러 전파 대신). `main()` 이 `main(argv: list[str] | None = None) -> int` 시그니처를 갖도록 변경(테스트용).

실제 파일 구조는 Task 실행 시점에 Read 로 확인 후 최소 변경만 수행. 핵심은:
(a) 없는 파일이 있어도 WARNING 으로 skip.
(b) drift 있는 파일은 `--write` 없으면 `exit 1`.
(c) `main()` 을 argv 인자 받아 테스트 가능하게.

- [ ] **Step 2: 테스트 작성 — `core/tests/unit/docs/test_render_versions.py`**

```python
"""render_versions 체커 단위 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "render_versions.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("render_versions", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["render_versions"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_targets_에는_삭제된_파일이_없다() -> None:
    mod = _load_module()
    targets = getattr(mod, "TARGETS", None)
    assert targets is not None, "TARGETS 상수가 없음"
    bad_paths = {"docs/onboarding/00-quickstart.md", "docs/engineering/standards.md"}
    target_strs = {str(t) if isinstance(t, str | Path) else str(t[0]) for t in targets}
    assert not any(bp in s for s in target_strs for bp in bad_paths), (
        f"삭제된 파일이 TARGETS 에 남아 있음: {target_strs & {*bad_paths}}"
    )


def test_main_은_argv_인자를_받는다() -> None:
    mod = _load_module()
    assert callable(mod.main)
    # argv=[] 로 dry-run 호출 시 int 반환.
    rc = mod.main([])
    assert isinstance(rc, int)
```

- [ ] **Step 3: FAIL/PASS 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_render_versions.py -v
```
Expected: 첫 테스트는 `TARGETS` 에 삭제된 파일이 있으면 FAIL(구조 미수정 시) 또는 PASS. 두 번째는 `main()` 시그니처 변경 안 됐으면 FAIL. 양쪽 수정 후 PASS.

- [ ] **Step 4: 린트/타입 + 커밋**

```
uv run ruff check scripts/docs/render_versions.py core/tests/unit/docs/test_render_versions.py
uv run ty check scripts/docs/render_versions.py
git add scripts/docs/render_versions.py core/tests/unit/docs/test_render_versions.py
git commit -m "refactor(docs): S2 render_versions TARGETS 축소 + main(argv) 시그니처

삭제된 docs/onboarding/00-quickstart.md 및 docs/engineering/standards.md 를
TARGETS 에서 제거. main() 이 argv 를 받도록 변경하여 테스트에서 직접 호출 가능.

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.2

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: S5 `audit_architecture.py` — fixture + 실패 테스트

**Files:**
- Create: `core/tests/fixtures/docs/arch-sample/good.md`
- Create: `core/tests/fixtures/docs/arch-sample/orphan.md`
- Create: `core/tests/unit/docs/test_audit_architecture.py`

- [ ] **Step 1: fixture 생성**

`core/tests/fixtures/docs/arch-sample/good.md`:
````markdown
# 아키텍처 OK
6 plane: `api`, `realtime`, `worker`, `scheduler`, `edge`, `platform-adapter`.
````

`core/tests/fixtures/docs/arch-sample/orphan.md`:
````markdown
# 오래된 plane 언급
예전 이름 `legacy-plane` 을 사용하고 있다.
또 `api` 와 `worker` 는 현재도 존재.
````

- [ ] **Step 2: 테스트 작성**

```python
"""audit_architecture 체커 단위 테스트."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "audit_architecture.py"
FIXTURE_ROOT = ROOT / "core" / "tests" / "fixtures" / "docs" / "arch-sample"


def _load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"체커 모듈이 없습니다: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("audit_architecture", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_architecture"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_good_문서는_exit_0(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    actual_planes = {"api", "realtime", "worker", "scheduler", "edge", "platform-adapter"}
    rc = mod.audit_documents(
        doc_paths=[FIXTURE_ROOT / "good.md"],
        actual=actual_planes,
    )
    assert rc == 0


def test_orphan_언급_검출(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    actual_planes = {"api", "realtime", "worker", "scheduler", "edge", "platform-adapter"}
    rc = mod.audit_documents(
        doc_paths=[FIXTURE_ROOT / "orphan.md"],
        actual=actual_planes,
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "legacy-plane" in out


def test_main_인자_없이_실행시_int_반환() -> None:
    mod = _load_module()
    rc = mod.main([])
    assert isinstance(rc, int)
```

- [ ] **Step 3: FAIL 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_architecture.py -v
```
Expected: 3 tests FAIL with "체커 모듈이 없습니다".

- [ ] **Step 4: 커밋**

```
git add core/tests/fixtures/docs/arch-sample/ core/tests/unit/docs/test_audit_architecture.py
git commit -m "test(docs): S5 audit_architecture fixture + red tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: S5 `audit_architecture.py` 구현

**Files:**
- Create: `scripts/docs/audit_architecture.py`

- [ ] **Step 1: 체커 구현**

```python
#!/usr/bin/env python3
"""ARCHITECTURE-MAP/CONSOLIDATION 등 구조 문서와 현 코드 기반 실측 집합 비교(S5).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.5
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

TARGET_DOCS_DEFAULT = [
    "docs/ARCHITECTURE-MAP.md",
    "docs/engineering/msa/CONSOLIDATION.md",
]
ADR_GLOB = "docs/governance/adr/*.md"

TOKEN_RE = re.compile(r"`([a-z][a-z0-9\-]+)`")


def load_actual_sets(root: Path) -> tuple[set[str], set[str], set[str]]:
    """(planes, services, worker_event_domains) 실측 집합을 반환."""
    planes_yaml = root / "deploy" / "catalog" / "planes.yaml"
    services_yaml = root / "deploy" / "catalog" / "services.yaml"

    planes: set[str] = set()
    if planes_yaml.exists():
        data = yaml.safe_load(planes_yaml.read_text(encoding="utf-8"))
        planes = set((data.get("planes") or {}).keys())

    services: set[str] = set()
    if services_yaml.exists():
        data = yaml.safe_load(services_yaml.read_text(encoding="utf-8"))
        services = set((data.get("services") or {}).keys())
        services.discard("web")

    worker_domains: set[str] = set()
    worker_main = root / "planes" / "worker_plane" / "plane_worker" / "main.py"
    if worker_main.exists():
        src = worker_main.read_text(encoding="utf-8")
        # _EVENT_DOMAINS 리스트의 첫 번째 튜플 원소(도메인 이름)만 추출.
        block_m = re.search(r"_EVENT_DOMAINS.*?=\s*\[(.*?)\]", src, re.DOTALL)
        if block_m:
            for m in re.finditer(r'\(\s*"([^"]+)"', block_m.group(1)):
                worker_domains.add(m.group(1))

    return planes, services, worker_domains


def audit_documents(doc_paths: list[Path], actual: set[str]) -> int:
    """주어진 문서들에서 백틱 토큰을 추출하여 실측 집합과 비교.

    반환: 문제 검출 0 = 0, 1 이상 = 1.
    """
    orphans_all: list[tuple[Path, str]] = []
    missing_all: list[tuple[Path, set[str]]] = []

    for doc in doc_paths:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        tokens = set(TOKEN_RE.findall(text))
        # 문서 안에서 언급된 토큰 중 실측 집합에 없는 것 → orphan.
        for t in sorted(tokens):
            # 너무 짧거나 일반 단어 노이즈 완화(3자 이상, 숫자 포함하지 않는 토큰 한정).
            if len(t) < 3:
                continue
            if t.isdigit():
                continue
            # 아주 넓게 "plane 관련 후보" 만 검사하기는 어려우므로,
            # 실측에 있거나 actual 에 없으면 orphan 으로 리포트.
            if t not in actual and "-" in t and t.endswith(("plane", "-adapter")):
                orphans_all.append((doc, t))

        # 실측 집합 원소 중 문서에 아예 언급 없는 것.
        missing = actual - tokens
        if missing:
            missing_all.append((doc, missing))

    for doc, t in orphans_all:
        print(f"[orphan] {doc}: `{t}` (실측에 없음)")
    for doc, missing in missing_all:
        print(f"[missing] {doc}: 언급 누락 {sorted(missing)}")

    issue_count = len(orphans_all) + sum(1 for _ in missing_all if _[1])
    return 0 if issue_count == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="architecture doc vs actual structure audit (S5)")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    planes, _services, _worker = load_actual_sets(args.root)
    doc_paths: list[Path] = []
    for rel in TARGET_DOCS_DEFAULT:
        doc_paths.append(args.root / rel)
    doc_paths.extend(args.root.glob(ADR_GLOB))

    rc = audit_documents(doc_paths, planes)

    if args.report:
        lines = [
            f"# Architecture Audit — {datetime.now(tz=UTC).date().isoformat()}",
            "",
            f"실측 plane 집합: `{sorted(planes)}`",
            "",
            "## 검출 결과",
            "",
            f"exit code: {rc}",
        ]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 테스트 PASS 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_architecture.py -v
```
Expected: 3 PASS.

- [ ] **Step 3: 린트/타입**

Run:
```
uv run ruff check scripts/docs/audit_architecture.py
uv run ty check scripts/docs/audit_architecture.py
```
Expected: All checks passed.

- [ ] **Step 4: 커밋**

```
git add scripts/docs/audit_architecture.py
git commit -m "feat(docs): S5 audit_architecture 체커 — 구조 문서 drift heuristic 비교

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.5

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: S4 `audit_tutorials.py` — fixture + 실패 테스트

**Files:**
- Create: `core/tests/fixtures/docs/tutorials-sample/good.md`
- Create: `core/tests/fixtures/docs/tutorials-sample/bad-bash.md`
- Create: `core/tests/fixtures/docs/tutorials-sample/bad-json.md`
- Create: `core/tests/unit/docs/test_audit_tutorials.py`

- [ ] **Step 1: fixture 3개 생성**

`good.md`:
````markdown
# 정상 튜토리얼

```bash
echo "hello"
```

```json
{"ok": true}
```
````

`bad-bash.md`:
````markdown
# bash syntax 에러

```bash
if [ ; then echo broken fi
```
````

`bad-json.md`:
````markdown
# json 에러

```json
{not json}
```
````

- [ ] **Step 2: 테스트 파일 생성 — `core/tests/unit/docs/test_audit_tutorials.py`**

```python
"""audit_tutorials 체커 단위 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "audit_tutorials.py"
FIXTURE_ROOT = ROOT / "core" / "tests" / "fixtures" / "docs" / "tutorials-sample"


def _load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"체커 모듈이 없습니다: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("audit_tutorials", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_tutorials"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_good_튜토리얼은_pass() -> None:
    mod = _load_module()
    rc = mod.validate_files([FIXTURE_ROOT / "good.md"])
    assert rc == 0


def test_bash_syntax_에러_검출() -> None:
    mod = _load_module()
    rc = mod.validate_files([FIXTURE_ROOT / "bad-bash.md"])
    assert rc == 1


def test_json_에러_검출() -> None:
    mod = _load_module()
    rc = mod.validate_files([FIXTURE_ROOT / "bad-json.md"])
    assert rc == 1


def test_mark_배너_append_멱등(tmp_path: Path) -> None:
    mod = _load_module()
    src = FIXTURE_ROOT / "bad-bash.md"
    dst = tmp_path / "bad-bash.md"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    mod.mark_failed(dst)
    first = dst.read_text(encoding="utf-8")
    mod.mark_failed(dst)
    second = dst.read_text(encoding="utf-8")

    assert "⚠️ 검증 실패" in first
    assert first == second  # 멱등성.
```

- [ ] **Step 3: FAIL 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_tutorials.py -v
```
Expected: 4 tests FAIL.

- [ ] **Step 4: 커밋**

```
git add core/tests/fixtures/docs/tutorials-sample/ core/tests/unit/docs/test_audit_tutorials.py
git commit -m "test(docs): S4 audit_tutorials fixture + red tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: S4 `audit_tutorials.py` 구현

**Files:**
- Create: `scripts/docs/audit_tutorials.py`

- [ ] **Step 1: 체커 구현**

```python
#!/usr/bin/env python3
"""tutorials 코드 블록 syntax 검증 체커(S4).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.4
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

FENCE_RE = re.compile(r"```([a-zA-Z0-9]+)\n(.*?)```", re.DOTALL)
HTTP_LINE_RE = re.compile(r"^(GET|POST|PUT|DELETE|PATCH)\s+(\S+)", re.MULTILINE)

BANNER_MARKER = "⚠️ 검증 실패"


@dataclass
class Failure:
    file: Path
    language: str
    reason: str


def _validate_bash(source: str) -> str | None:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tf:
        tf.write(source)
        tf.flush()
        tmp_name = tf.name
    try:
        r = subprocess.run(  # noqa: S603
            ["bash", "-n", tmp_name], capture_output=True, text=True, check=False
        )
        if r.returncode != 0:
            return r.stderr.strip() or "bash -n failed"
        return None
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def _validate_json(source: str) -> str | None:
    try:
        json.loads(source)
    except json.JSONDecodeError as e:
        return str(e)
    return None


def validate_files(files: list[Path]) -> int:
    failures: list[Failure] = []
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in FENCE_RE.finditer(text):
            lang = match.group(1).lower()
            body = match.group(2)
            reason: str | None = None
            if lang in ("bash", "sh"):
                reason = _validate_bash(body)
            elif lang == "json":
                reason = _validate_json(body)
            # http 블록 검증은 단순 prefix 매칭이라 실측 plane 연동 필요 → 기본 off.
            if reason is not None:
                failures.append(Failure(path, lang, reason))

    for f in failures:
        print(f"[{f.language}] {f.file}: {f.reason}")
    return 0 if not failures else 1


def mark_failed(path: Path) -> None:
    """실패 파일 상단에 배너 append. 멱등."""
    text = path.read_text(encoding="utf-8")
    if BANNER_MARKER in text:
        return
    banner = f"> **{BANNER_MARKER} — 2026-04-13**\n\n"
    path.write_text(banner + text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="tutorials syntax validation (S4)")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--mark", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    tutorials_dir = args.root / "docs" / "tutorials"
    files = sorted(tutorials_dir.glob("*.md")) if tutorials_dir.exists() else []

    # 실패 파일 수집 전용 모드: validate_files 로직 재사용하되 파일별 결과도 기록.
    failures_by_file: dict[Path, list[Failure]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in FENCE_RE.finditer(text):
            lang = match.group(1).lower()
            body = match.group(2)
            reason: str | None = None
            if lang in ("bash", "sh"):
                reason = _validate_bash(body)
            elif lang == "json":
                reason = _validate_json(body)
            if reason is not None:
                failures_by_file.setdefault(path, []).append(Failure(path, lang, reason))

    for path, items in failures_by_file.items():
        print(f"[fail] {path}:")
        for it in items:
            print(f"   {it.language}: {it.reason}")

    if args.mark:
        for path in failures_by_file:
            mark_failed(path)
        print(f"[mark] {len(failures_by_file)} 파일에 경고 배너 추가")

    return 0 if not failures_by_file else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 테스트 PASS 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_tutorials.py -v
```
Expected: 4 PASS.

- [ ] **Step 3: 린트/타입 + 커밋**

```
uv run ruff check scripts/docs/audit_tutorials.py
uv run ty check scripts/docs/audit_tutorials.py
git add scripts/docs/audit_tutorials.py
git commit -m "feat(docs): S4 audit_tutorials 체커 — fence 블록 syntax 검증

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.4

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: S3 `audit_api_drift.py` — fixture + 실패 테스트

**Files:**
- Create: `core/tests/fixtures/docs/api-sample/docs-with-drift.md`
- Create: `core/tests/unit/docs/test_audit_api_drift.py`

- [ ] **Step 1: fixture**

`core/tests/fixtures/docs/api-sample/docs-with-drift.md`:
````markdown
# Sample API

## GET /api/known/items
반환: `id`, `name`.

## GET /api/phantom/nothing
문서에만 있는 엔드포인트.
````

- [ ] **Step 2: 테스트**

```python
"""audit_api_drift 체커 단위 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "audit_api_drift.py"
FIXTURE_DOC = ROOT / "core" / "tests" / "fixtures" / "docs" / "api-sample" / "docs-with-drift.md"


def _load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"체커 모듈이 없습니다: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("audit_api_drift", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_api_drift"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_doc_orphan_검출(capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    code_endpoints = {("GET", "/api/known/items")}
    rc = mod.compare_endpoints(
        code_endpoints=code_endpoints,
        doc_paths=[FIXTURE_DOC],
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "doc-orphan" in out
    assert "/api/phantom/nothing" in out


def test_doc_missing_검출(capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    code_endpoints = {
        ("GET", "/api/known/items"),
        ("POST", "/api/other/new"),
    }
    rc = mod.compare_endpoints(
        code_endpoints=code_endpoints,
        doc_paths=[FIXTURE_DOC],
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "doc-missing" in out
    assert "/api/other/new" in out


def test_완전_일치_exit_0(capsys: pytest.CaptureFixture) -> None:
    mod = _load_module()
    # fixture 문서에는 2개 엔드포인트 있음. 코드 측에도 정확히 2개 같게 주입.
    code_endpoints = {
        ("GET", "/api/known/items"),
        ("GET", "/api/phantom/nothing"),
    }
    rc = mod.compare_endpoints(
        code_endpoints=code_endpoints,
        doc_paths=[FIXTURE_DOC],
    )
    assert rc == 0
```

- [ ] **Step 3: FAIL 확인**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_api_drift.py -v
```
Expected: 3 FAIL with "체커 모듈이 없습니다".

- [ ] **Step 4: 커밋**

```
git add core/tests/fixtures/docs/api-sample/ core/tests/unit/docs/test_audit_api_drift.py
git commit -m "test(docs): S3 audit_api_drift fixture + red tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: S3 `audit_api_drift.py` 구현

**Files:**
- Create: `scripts/docs/audit_api_drift.py`

- [ ] **Step 1: 체커 구현**

```python
#!/usr/bin/env python3
"""docs/api vs plane OpenAPI schema 비교(S3).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.3
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

HTTP_LINE_RE = re.compile(r"^\s*##+\s*(GET|POST|PUT|DELETE|PATCH)\s+(/\S+)", re.MULTILINE)

DUMMY_ENV = {
    "ONEERP_JWT_SECRET": "x" * 32,
    "ONEERP_DEBUG": "true",
    "ONEERP_FERRETDB_URI": "mongodb://localhost:27017",
    "ONEERP_NATS_URL": "nats://localhost:4222",
    "ONEERP_VALKEY_URL": "redis://localhost:6379/0",
}

PLANE_MODULES = [
    ("api_plane", "plane_api.main"),
    ("edge_plane", "plane_edge.main"),
    ("realtime_plane", "plane_realtime.main"),
    ("scheduler_plane", "plane_scheduler.main"),
    ("platform_adapter_plane", "plane_platform_adapter.main"),
    ("worker_plane", "plane_worker.main"),
]


def _inject_env() -> None:
    for k, v in DUMMY_ENV.items():
        os.environ.setdefault(k, v)


def extract_code_endpoints(root: Path) -> set[tuple[str, str]]:
    _inject_env()
    endpoints: set[tuple[str, str]] = set()
    for plane_dir, module_name in PLANE_MODULES:
        plane_root = root / "planes" / plane_dir
        if not plane_root.exists():
            print(f"[warn] plane 경로 없음: {plane_root}", file=sys.stderr)
            continue
        if str(plane_root) not in sys.path:
            sys.path.insert(0, str(plane_root))
        mod_name, _, attr = module_name.rpartition(".")
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, plane_root / mod_name.replace(".", "/") / f"{attr}.py"
            )
            assert spec is not None and spec.loader is not None
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            app = getattr(mod, "app", None)
            if app is None:
                print(f"[warn] {module_name}.app 없음", file=sys.stderr)
                continue
            openapi = app.openapi()
            for path, ops in openapi.get("paths", {}).items():
                for method in ops:
                    if method.lower() in {"get", "post", "put", "delete", "patch"}:
                        endpoints.add((method.upper(), path))
        except Exception as e:
            print(f"[warn] {module_name} import 실패: {e}", file=sys.stderr)
    return endpoints


def extract_doc_endpoints(doc_paths: list[Path]) -> set[tuple[str, str]]:
    endpoints: set[tuple[str, str]] = set()
    for p in doc_paths:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in HTTP_LINE_RE.finditer(text):
            endpoints.add((m.group(1).upper(), m.group(2)))
    return endpoints


def compare_endpoints(
    code_endpoints: set[tuple[str, str]],
    doc_paths: list[Path],
) -> int:
    doc_endpoints = extract_doc_endpoints(doc_paths)
    orphans = doc_endpoints - code_endpoints
    missing = code_endpoints - doc_endpoints

    for method, path in sorted(orphans):
        print(f"[doc-orphan] {method} {path} — 코드에 없음")
    for method, path in sorted(missing):
        print(f"[doc-missing] {method} {path} — 문서에 없음")

    if orphans or missing:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="api drift audit (S3)")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    code = extract_code_endpoints(args.root)
    doc_dir = args.root / "docs" / "api"
    doc_paths = sorted(doc_dir.rglob("*.md")) if doc_dir.exists() else []

    rc = compare_endpoints(code, doc_paths)

    if args.report:
        lines = [
            f"# API Drift Report — {datetime.now(tz=UTC).date().isoformat()}",
            "",
            f"실측 엔드포인트 수: {len(code)}",
            f"문서 엔드포인트 수: {len(extract_doc_endpoints(doc_paths))}",
            "",
            f"exit code: {rc}",
        ]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 테스트 PASS**

Run:
```
uv run pytest core/tests/unit/docs/test_audit_api_drift.py -v
```
Expected: 3 PASS.

- [ ] **Step 3: 린트/타입 + 커밋**

```
uv run ruff check scripts/docs/audit_api_drift.py
uv run ty check scripts/docs/audit_api_drift.py
git add scripts/docs/audit_api_drift.py
git commit -m "feat(docs): S3 audit_api_drift 체커 — OpenAPI schema 대비 docs/api 비교

plane in-process import + dummy env 주입 + endpoint set diff.

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.3

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: 통합 러너 `audit-all.sh`

**Files:**
- Create: `scripts/docs/audit-all.sh`

- [ ] **Step 1: 스크립트 생성 (chmod +x 포함)**

`scripts/docs/audit-all.sh`:
```bash
#!/usr/bin/env bash
# 5 docs health check 트랙 통합 러너.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

run() {
  local name="$1"; shift
  echo "=== ${name} ==="
  "$@"
  local rc=$?
  echo "exit=${rc}"
  return $rc
}

fail=0
run "S1 stale-refs"     uv run python scripts/docs/check_stale_refs.py     || fail=$((fail+1))
run "S2 version-drift"  uv run python scripts/docs/render_versions.py      || fail=$((fail+1))
run "S3 api-drift"      uv run python scripts/docs/audit_api_drift.py      || fail=$((fail+1))
run "S4 tutorials"      uv run python scripts/docs/audit_tutorials.py      || fail=$((fail+1))
run "S5 architecture"   uv run python scripts/docs/audit_architecture.py   || fail=$((fail+1))

echo
echo "총 실패 트랙: ${fail}"
[[ "$fail" -gt 0 ]] && exit 1
exit 0
```

```
chmod +x scripts/docs/audit-all.sh
bash -n scripts/docs/audit-all.sh && echo "syntax OK"
```
Expected: `syntax OK`.

- [ ] **Step 2: 커밋**

```
git add scripts/docs/audit-all.sh
git commit -m "feat(docs): audit-all.sh — 5 트랙 통합 러너

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: 초기 cleanup S1 — 문서 갱신 + RUNBOOK 삭제

**Files:**
- Modify: `docs/developer/01-add-new-service.md`
- Modify: `docs/security/OWASP-CHECKLIST.md`
- Modify: `docs/engineering/msa/CONSOLIDATION.md`
- Modify: `docs/onboarding/QUICKSTART.md`
- Delete: `docs/engineering/msa/RUNBOOK-cluster-merge.md`

- [ ] **Step 1: 스테일 참조 그레핑**

Run:
```
uv run python scripts/docs/check_stale_refs.py 2>&1 | head -40
```
Expected: 위 4개 파일에서 `docker-compose.local.yml`/`docker-compose.plane.yml`/`.gitea` 등 참조 나열.

- [ ] **Step 2: 각 파일 수정**

체커 출력의 정확한 라인을 따라 파일별로 Read → Edit. 교정 원칙:
- `docker-compose.local.yml`, `docker-compose.plane.yml` 참조 → `docker-compose.yml (--profile plane)` 로 치환.
- `.gitea/workflows/*` 참조 → "CI 파이프라인" 일반 표현으로 제거.
- `services/<domain>/<svc>/Dockerfile` 참조 → `planes/<plane>/Dockerfile` 로 치환하거나 해당 문단 삭제.
- 죽은 링크 (`00-quickstart.md` 등) → 링크 제거(텍스트만) 또는 유효 링크로 수정.

각 파일 수정 후 개별 커밋:
```
git add docs/<path>
git commit -m "docs: <file> — 스테일 참조 갱신 (compose 통합 + .gitea 제거 반영)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3: `RUNBOOK-cluster-merge.md` 삭제**

Run:
```
git rm docs/engineering/msa/RUNBOOK-cluster-merge.md
git commit -m "docs: RUNBOOK-cluster-merge 삭제 — Ralph Harness 전용, 현 워크플로우와 무관

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: S1 재실행 — 잔여 스테일 0 건 확인**

Run:
```
uv run python scripts/docs/check_stale_refs.py 2>&1 | tail -5
```
Expected: `총 0 건 감지` 또는 남은 건은 본 스펙 범위 밖(예: ADR 결정문 내 historical 참조 — `--fix-dead-links` 로도 처리 불가한 historical 기록은 그대로 둠, 필요시 추가 Task 로 분리).

검출이 0 이 아니지만 과거 ADR 의 **historical 맥락** 이라면(예: "이전에 .gitea 를 사용했으나…") 개별 판단. 실제 교정이 가능한 것만 수정.

---

## Task 12: 초기 cleanup S2 — render_versions drift 교정

**Files:** 없음 직접 수정 — 체커가 `--write` 로 파일 변경.

- [ ] **Step 1: drift 검사**

Run:
```
uv run python scripts/docs/render_versions.py 2>&1 | tail -10
```
Expected: drift 보고 (있을 수도, 없을 수도). exit 1 이면 교정 필요.

- [ ] **Step 2: `--write` 교정**

Run:
```
uv run python scripts/docs/render_versions.py --write 2>&1 | tail -5
```

- [ ] **Step 3: 교정 후 재검증 + 커밋**

Run:
```
uv run python scripts/docs/render_versions.py 2>&1 | tail -3
```
Expected: exit 0 또는 "변경 없음".

변경된 파일이 있다면:
```
git add README.md .claude/CLAUDE.md
git commit -m "docs: render_versions --write 로 버전 표 drift 교정

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: 초기 cleanup S3 — api-drift 보고서 발행

**Files:**
- Create: `docs/generated/api-drift-report.md`

- [ ] **Step 1: 보고서 생성**

Run:
```
uv run python scripts/docs/audit_api_drift.py --report docs/generated/api-drift-report.md 2>&1 | tail -15
```
Expected: 보고서 파일 생성. 이 단계에서 exit 1 이어도 OK — 보고서는 cleanup 출발점.

- [ ] **Step 2: 커밋**

```
git add docs/generated/api-drift-report.md
git commit -m "docs(generated): api drift 초기 보고서 — 교정은 후속 PR

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: 초기 cleanup S4 — 실패 튜토리얼 배너

**Files:** 조건부 수정.

- [ ] **Step 1: 현재 튜토리얼 검증**

Run:
```
uv run python scripts/docs/audit_tutorials.py 2>&1 | tail -30
```
Expected: 실패 파일 목록 또는 `exit 0`.

- [ ] **Step 2: `--mark` 로 배너 추가(실패가 있을 경우)**

Run:
```
uv run python scripts/docs/audit_tutorials.py --mark 2>&1 | tail -5
```

- [ ] **Step 3: 배너가 붙은 파일 커밋**

변경 파일 확인 후:
```
git add -u docs/tutorials/
git commit -m "docs(tutorials): audit_tutorials --mark 로 검증 실패 배너 추가

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

실패 0 건이면 이 Task 는 no-op.

---

## Task 15: 초기 cleanup S5 — architecture audit 보고서

**Files:**
- Create: `docs/generated/architecture-audit-2026-04-13.md`

- [ ] **Step 1: 보고서 생성**

Run:
```
uv run python scripts/docs/audit_architecture.py \
  --report docs/generated/architecture-audit-2026-04-13.md 2>&1 | tail -10
```
Expected: 보고서 생성, 검출된 drift 목록 stdout.

- [ ] **Step 2: 명백한 drift 수동 수정**

보고서의 `[orphan]`/`[missing]` 각 항목을 검토하여 **명백한 것만** 해당 docs 파일 수정. 판단 애매한 항목은 그대로 두고 follow-up 으로 남김.

- [ ] **Step 3: 커밋**

```
git add docs/generated/architecture-audit-2026-04-13.md
git add -u docs/ARCHITECTURE-MAP.md docs/engineering/msa/CONSOLIDATION.md 2>/dev/null || true
git commit -m "docs: architecture audit 초기 보고서 + 명백한 drift 교정

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 16: README 에 '문서 건강성 검사' 문단 추가

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README 마지막 "더 읽을거리" 섹션 위에 문단 append**

`README.md` 의 "## 📚 더 읽을거리" **직전** 또는 "## ⚖️ 규약" **직전** 에 다음 블록 추가:

```markdown
## 📝 문서 건강성 검사

```bash
./scripts/docs/audit-all.sh
```

5 트랙(S1~S5) 의 체커를 순차 실행하여 `docs/` 건강성을 검증한다.

- **S1** `check_stale_refs.py` — 삭제된 자산 참조·죽은 로컬 링크.
- **S2** `render_versions.py` — 버전 표 drift (`--write` 로 교정).
- **S3** `audit_api_drift.py` — OpenAPI schema vs `docs/api/` 비교. 보고서: `docs/generated/api-drift-report.md`.
- **S4** `audit_tutorials.py` — 튜토리얼 bash/json fence 블록 syntax 검증.
- **S5** `audit_architecture.py` — `planes.yaml`/`services.yaml` 실측 집합 vs 구조 문서. 보고서: `docs/generated/architecture-audit-<date>.md`.

설계: `docs/superpowers/specs/2026-04-13-docs-health-audit-design.md`.
```

- [ ] **Step 2: 커밋**

```
git add README.md
git commit -m "docs(readme): 문서 건강성 검사 섹션 추가 — audit-all.sh 실행 안내

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 17: 최종 회귀 검증

**Files:** 없음 (검증만).

- [ ] **Step 1: 전체 품질 게이트**

Run:
```
cd /Users/phil/WorkSpace/apps/OneErp
uv run ruff check scripts/docs/ core/tests/unit/docs/
uv run ty check scripts/docs/
```
Expected: 전부 통과.

- [ ] **Step 2: 전 체커 단위 테스트**

Run:
```
uv run pytest core/tests/unit/docs/ -q
```
Expected: 전부 PASS. 최소 합계 **15 tests**(S1: 3, S2: 2, S3: 3, S4: 4, S5: 3).

- [ ] **Step 3: 통합 러너 실행**

Run:
```
./scripts/docs/audit-all.sh 2>&1 | tail -20
```
Expected: **총 실패 트랙: 0** + exit 0.

실패가 남아 있다면:
- S1 실패 → Task 11 의 교정이 덜 된 파일 식별, 개별 수정 후 재실행.
- S2 실패 → `--write` 재실행.
- S3/S5 보고서 발행 자체는 exit 0/1 별도로 취급. **spec §7 "성공 기준"** 에 따라 보고서 생성과 명백한 drift 교정까지만 이번 범위. 남은 drift 는 follow-up.

본 Task 의 PASS 기준은 "체커 자체가 깨지지 않음" + "초기 cleanup 에서 수정 가능했던 항목은 모두 수정됨". 보고서가 여전히 drift 를 보고하는 것은 follow-up 의 범위.

- [ ] **Step 4: 커밋 히스토리 요약**

Run:
```
git log --oneline -25
```
Expected: Task 1~16 의 커밋들이 순서대로 보임(약 20+ 커밋).

---

## 완료 기준 (Done Definition)

- Task 0~17 의 모든 체크박스 완료.
- 최소 15 개 단위 테스트 PASS.
- `./scripts/docs/audit-all.sh` 실행 시 **체커 자체는 모두 정상 실행**되며, S1/S2/S4 는 exit 0, S3/S5 는 보고서 발행 성공.
- `docs/generated/api-drift-report.md`, `docs/generated/architecture-audit-2026-04-13.md` 커밋 존재.
- 스테일 참조 0 건(초기 cleanup 로 모두 제거), `RUNBOOK-cluster-merge.md` 삭제됨.
- README 에 "문서 건강성 검사" 섹션 추가.
- `uv run ruff check scripts/docs/` + `uv run ty check scripts/docs/` 통과.

## 롤백

```
git log --oneline -30   # Task 1~16 의 커밋 SHA 수집
git revert <SHA...>     # 역순으로 revert
```

신규 스크립트는 단순 삭제로 대체 가능:
```
rm scripts/docs/{check_stale_refs,audit_api_drift,audit_tutorials,audit_architecture}.py
rm scripts/docs/audit-all.sh
rm -rf core/tests/unit/docs core/tests/fixtures/docs
```

삭제 후 `git checkout HEAD~N -- scripts/docs/render_versions.py` 로 `render_versions.py` 의 원본 복원.
