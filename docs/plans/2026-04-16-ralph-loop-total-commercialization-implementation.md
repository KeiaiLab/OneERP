# OneERP Ralph-Loop 전체 상용 완성 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ralph-loop를 `47모듈 × 23 게이트 = 1,081/1,081 GREEN`과 출시급 실측 기준으로 운영할 수 있게 정본 문서, audit, 상태 보드, 릴리즈 게이트, 제어 파일을 정렬한다.

**Architecture:** 구현은 `정본 정합화 → audit 의미 정렬 → roadmap/status 보드 확장 → 출시급 실측 게이트 추가 → loop 제어 파일 전환` 순서로 진행한다. 각 단계는 TDD로 잠그고, 기존 M7/Wave 1 전용 계약을 전체 상용 완성 계약으로 바꾸되 기존 사용자 작업 영역은 건드리지 않는다.

**Tech Stack:** Python 3.14, pytest, bash, Makefile, Markdown docs, `scripts/audit/commercial_readiness.py`, `scripts/roadmap/status_render.py`, Playwright 기반 E2E

---

## Task 1: 정본 완료 정의와 문서 참조 경로를 맞춘다

**Files:**
- Create: `tests/unit/test_total_commercialization_contract.py`
- Modify: `docs/governance/adr/0012-commercialization-wave-mapping.md`
- Modify: `docs/product/roadmap/engineering/waves/wave-4.md`
- Modify: `docs/product/roadmap/milestones.md`
- Modify: `docs/product/roadmap/matrix.md`
- Modify: `docs/INDEX.md`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_total_commercialization_contract.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_wave4가_beta_예외가_아니라_23_23_전수통과를_요구한다() -> None:
    adr = (ROOT / "docs/governance/adr/0012-commercialization-wave-mapping.md").read_text(
        encoding="utf-8",
    )
    wave4 = (ROOT / "docs/product/roadmap/engineering/waves/wave-4.md").read_text(
        encoding="utf-8",
    )
    assert "beta 이상 (commercial 강제 X" not in adr
    assert "8 모듈 전부 23/23 기준 통과" in adr
    assert "8 모듈 전부 23/23 기준 통과" in wave4


def test_docs_index가_실재하는_마스터_플랜을_가리킨다() -> None:
    text = (ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "docs/product/plans/2026-02-09-master-plan.md" not in text
    assert ".planning/ROADMAP.md" in text
```

- [ ] **Step 2: 테스트가 실제로 실패하는지 확인**

Run:
```bash
uv run pytest tests/unit/test_total_commercialization_contract.py -v
```

Expected:
- `beta 이상 (commercial 강제 X` 문구 때문에 FAIL
- 누락된 마스터 플랜 경로 때문에 FAIL

- [ ] **Step 3: 정본 문서를 최소 범위로 수정**

수정 원칙:
- `ADR-0012`의 Wave 4 완료 조건을 `8 모듈 전부 commercial-ready(23/23)`로 바꾼다.
- `wave-4.md`, `milestones.md`, `matrix.md`의 `80%` 완료 문구 중 **전체 상용 완성**에 연결된 부분만 정렬한다.
- `docs/INDEX.md`의 누락 경로는 실제 운용 정본인 `.planning/ROADMAP.md`로 치환한다.

- [ ] **Step 4: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_total_commercialization_contract.py -v
```

Expected:
- PASS

- [ ] **Step 5: 커밋**

```bash
git add tests/unit/test_total_commercialization_contract.py \
        docs/governance/adr/0012-commercialization-wave-mapping.md \
        docs/product/roadmap/engineering/waves/wave-4.md \
        docs/product/roadmap/milestones.md \
        docs/product/roadmap/matrix.md \
        docs/INDEX.md
git commit -m "docs(roadmap): 전체 상용 완성 정의를 47모듈 23/23로 정렬"
```

---

## Task 2: audit 스크립트가 전체 상용 완성 의미를 직접 계산하게 만든다

**Files:**
- Create: `tests/unit/test_commercial_readiness_total_completion.py`
- Modify: `scripts/audit/commercial_readiness.py`
- Modify: `scripts/audit/wave_entry_check.py`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_commercial_readiness_total_completion.py` 생성:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_commercial_readiness_json이_전체_완료_요약을_포함한다() -> None:
    result = subprocess.run(
        ["python3", "scripts/audit/commercial_readiness.py", "--format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    summary = payload["summary"]
    assert summary["total_judgments"] == 1081
    assert "overall_complete" in summary
    assert "commercial_ready_modules" in summary


def test_wave_entry_check가_완료를_100퍼센트_기준으로_표현한다() -> None:
    text = (ROOT / "scripts/audit/wave_entry_check.py").read_text(encoding="utf-8")
    assert "80%" not in text
    assert "23/23" in text
```

- [ ] **Step 2: 테스트가 실제로 실패하는지 확인**

Run:
```bash
uv run pytest tests/unit/test_commercial_readiness_total_completion.py -v
```

Expected:
- `summary["total_judgments"]` 또는 `overall_complete` 누락으로 FAIL
- `wave_entry_check.py`의 기존 80% 기준 때문에 FAIL

- [ ] **Step 3: `commercial_readiness.py`에 전체 완료 요약 추가**

최소 구현 방향:
- JSON 출력의 `summary` 아래에 아래 키를 추가한다.

```python
summary = {
    "passed": total_passed,
    "total_judgments": TOTAL_MODULES * TOTAL_GATES,
    "commercial_ready_modules": commercial_ready_modules,
    "overall_complete": total_passed == TOTAL_MODULES * TOTAL_GATES and commercial_ready_modules == TOTAL_MODULES,
}
```

- [ ] **Step 4: `wave_entry_check.py`의 완료 기준 문구와 계산을 100% 기준으로 맞춘다**

구현 원칙:
- 다음 Wave 진입 전환과 현재 Wave 완료 표현에서 `80%`를 제거한다.
- 완료는 항상 `모든 대상 모듈이 23/23`일 때만 참으로 계산한다.

- [ ] **Step 5: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_commercial_readiness_total_completion.py -v
python3 scripts/audit/commercial_readiness.py --format json >/tmp/commercial-status.json
```

Expected:
- pytest PASS
- `/tmp/commercial-status.json`의 `summary.total_judgments == 1081`

- [ ] **Step 6: 커밋**

```bash
git add tests/unit/test_commercial_readiness_total_completion.py \
        scripts/audit/commercial_readiness.py \
        scripts/audit/wave_entry_check.py
git commit -m "feat(audit): 전체 상용 완성 요약과 100퍼센트 완료 기준 추가"
```

---

## Task 3: roadmap 상태 보드에 전역/출시/정지 뷰를 추가한다

**Files:**
- Create: `tests/unit/test_total_commercialization_status_render.py`
- Modify: `scripts/roadmap/status_render.py`
- Modify: `docs/product/roadmap/status.md`
- Modify: `docs/product/roadmap/README.md`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_total_commercialization_status_render.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

from scripts.roadmap.status_render import ModuleRow, RenderContext, render_section

ROOT = Path(__file__).resolve().parents[2]


def test_progress_섹션은_1081_분모를_사용한다() -> None:
    modules = [ModuleRow(module="demo", label="alpha", passed=23, failed=0, implemented=23)]
    ctx = RenderContext(modules=modules, waves=[], active_wave=1)
    text = render_section("progress", ctx)
    assert "1081" in text


def test_status_md가_출시와_정지_자동섹션을_가진다() -> None:
    text = (ROOT / "docs/product/roadmap/status.md").read_text(encoding="utf-8")
    assert "<!-- status-auto:release-rehearsal -->" in text
    assert "<!-- status-auto:blockers -->" in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run pytest tests/unit/test_total_commercialization_status_render.py -v
```

Expected:
- `status.md` 자동 섹션 누락으로 FAIL

- [ ] **Step 3: 상태 보드 섹션을 추가한다**

`docs/product/roadmap/status.md`에 아래 자동 섹션을 추가한다.

```md
<!-- status-auto:release-rehearsal -->
_출시급 실측 상태 렌더 대기._
<!-- /status-auto:release-rehearsal -->

<!-- status-auto:blockers -->
_정지 조건 상태 렌더 대기._
<!-- /status-auto:blockers -->
```

- [ ] **Step 4: `status_render.py`에 두 섹션 렌더러를 추가한다**

최소 구현 방향:
- `release-rehearsal`: 최근 릴리즈 게이트 스크립트 결과와 증거 디렉토리 요약
- `blockers`: 현재 활성 블로커 개수와 마지막 갱신 시각

예시:

```python
if key == "release-rehearsal":
    return "- 최근 출시급 실측: PASS/FAIL\n- 근거: artifacts/rehearsal/latest/"
if key == "blockers":
    return "- 활성 블로커: 0건\n- 근거: HANDOFF.md"
```

- [ ] **Step 5: 로드맵 렌더 검증**

Run:
```bash
uv run pytest tests/unit/test_total_commercialization_status_render.py -v
python3 scripts/roadmap/status_render.py --check
```

Expected:
- pytest PASS
- `status_render.py --check` exit 0

- [ ] **Step 6: 커밋**

```bash
git add tests/unit/test_total_commercialization_status_render.py \
        scripts/roadmap/status_render.py \
        docs/product/roadmap/status.md \
        docs/product/roadmap/README.md
git commit -m "feat(roadmap): 전체 상용 완성용 상태 보드 섹션 추가"
```

---

## Task 4: 출시급 실측 게이트 스크립트를 추가한다

**Files:**
- Create: `scripts/ci/check_release_rehearsal_evidence.py`
- Create: `scripts/ci/run_total_commercial_gate.sh`
- Create: `tests/unit/test_run_total_commercial_gate.py`
- Modify: `Makefile`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_run_total_commercial_gate.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_total_commercial_gate_script가_핵심_단계를_포함한다() -> None:
    path = ROOT / "scripts/ci/run_total_commercial_gate.sh"
    assert path.exists(), f"스크립트 없음: {path}"
    text = path.read_text(encoding="utf-8")
    for snippet in (
        "./scripts/ci/run_release_gate.sh",
        "check_release_rehearsal_evidence.py",
        "성능",
        "복구",
        "운영",
    ):
        assert snippet in text


def test_makefile이_total_commercial_gate_타깃을_노출한다() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "total-commercial-gate:" in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run pytest tests/unit/test_run_total_commercial_gate.py -v
```

Expected:
- 스크립트 부재로 FAIL

- [ ] **Step 3: 증거 검사기 작성**

`scripts/ci/check_release_rehearsal_evidence.py`에 아래 최소 검사부터 넣는다.

```python
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

required = [
    ROOT / "docs/infra/ops/backup-restore.md",
    ROOT / "docs/ops/runbook-db-backup-restore.md",
    ROOT / "docs/generated/commercial-status.md",
]

missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
if missing:
    print("missing rehearsal evidence:")
    for item in missing:
        print(f"- {item}")
    raise SystemExit(1)
print("release rehearsal evidence ok")
```

- [ ] **Step 4: 총합 게이트 스크립트 작성**

`scripts/ci/run_total_commercial_gate.sh` 생성:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

printf '\n=== 기본 릴리즈 게이트 ===\n'
./scripts/ci/run_release_gate.sh

printf '\n=== 성능/복구/운영 증거 검증 ===\n'
python3 scripts/ci/check_release_rehearsal_evidence.py

printf '\n=== total commercial gate 통과 ===\n'
```

- [ ] **Step 5: Makefile 타깃 연결**

`Makefile`에 아래 타깃을 추가한다.

```make
total-commercial-gate:  ## 전체 상용 완성용 출시급 실측 게이트
	./scripts/ci/run_total_commercial_gate.sh
```

- [ ] **Step 6: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_run_total_commercial_gate.py -v
python3 scripts/ci/check_release_rehearsal_evidence.py
```

Expected:
- pytest PASS
- 증거 문서가 존재하면 evidence checker exit 0

- [ ] **Step 7: 커밋**

```bash
git add scripts/ci/check_release_rehearsal_evidence.py \
        scripts/ci/run_total_commercial_gate.sh \
        tests/unit/test_run_total_commercial_gate.py \
        Makefile
git commit -m "feat(ci): 전체 상용 완성용 출시급 실측 게이트 추가"
```

---

## Task 5: Ralph-loop 제어 파일을 Wave 1 전용에서 전체 상용 완성 기준으로 바꾼다

**Files:**
- Create: `tests/unit/test_ralph_loop_total_commercialization_docs.py`
- Modify: `RALPH-LOOP-PROMPT.md`
- Modify: `PROGRESS.md`
- Modify: `HANDOFF.md`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_ralph_loop_total_commercialization_docs.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ralph_loop_prompt가_전체_상용_완성_계약을_명시한다() -> None:
    text = (ROOT / "RALPH-LOOP-PROMPT.md").read_text(encoding="utf-8")
    assert "1,081" in text
    assert "47모듈" in text
    assert "run_total_commercial_gate.sh" in text
    assert "Wave 1 × 23/23 전수 PASS" not in text


def test_progress_md가_최종_목표를_1081셀로_적는다() -> None:
    text = (ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    assert "1,081" in text
    assert "47모듈" in text
    assert "276 셀" not in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run pytest tests/unit/test_ralph_loop_total_commercialization_docs.py -v
```

Expected:
- Wave 1 / 276 전용 문구 때문에 FAIL

- [ ] **Step 3: 프롬프트와 진행 문서를 전체 상용 기준으로 전환**

수정 원칙:
- `RALPH-LOOP-PROMPT.md`의 완료 조건을 `1,081/1,081 + total-commercial-gate`로 바꾼다.
- `PROGRESS.md`의 목표, 진행률, 품질 추적을 `47모듈` 기준으로 바꾼다.
- `HANDOFF.md`의 상태 설명도 Wave 1 전용 문구 대신 전체 상용 완성 기준으로 바꾼다.

- [ ] **Step 4: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_ralph_loop_total_commercialization_docs.py -v
```

Expected:
- PASS

- [ ] **Step 5: 커밋**

```bash
git add tests/unit/test_ralph_loop_total_commercialization_docs.py \
        RALPH-LOOP-PROMPT.md \
        PROGRESS.md \
        HANDOFF.md
git commit -m "docs(ralph-loop): 전체 상용 완성 기준으로 제어 파일 전환"
```

---

## Task 6: 종단 검증과 렌더 결과를 확인한다

**Files:**
- Modify: `docs/generated/commercial-status.md` (자동 생성)
- Modify: `docs/product/roadmap/status.md` (자동 렌더 결과)

- [ ] **Step 1: 단위 테스트 일괄 실행**

Run:
```bash
uv run pytest \
  tests/unit/test_total_commercialization_contract.py \
  tests/unit/test_commercial_readiness_total_completion.py \
  tests/unit/test_total_commercialization_status_render.py \
  tests/unit/test_run_total_commercial_gate.py \
  tests/unit/test_ralph_loop_total_commercialization_docs.py -v
```

Expected:
- 전부 PASS

- [ ] **Step 2: audit 산출물 재생성**

Run:
```bash
python3 scripts/audit/commercial_readiness.py --write
python3 scripts/audit/commercial_readiness.py --format json > docs/generated/commercial-status.json
```

Expected:
- `docs/generated/commercial-status.md`
- `docs/generated/commercial-status.json`

- [ ] **Step 3: roadmap 렌더와 게이트 검증**

Run:
```bash
python3 scripts/roadmap/status_render.py
make verify-roadmap
```

Expected:
- 렌더 성공
- verify-roadmap exit 0

- [ ] **Step 4: 출시급 실측 게이트 dry run**

Run:
```bash
python3 scripts/ci/check_release_rehearsal_evidence.py
bash scripts/ci/run_total_commercial_gate.sh
```

Expected:
- evidence check PASS
- 전체 게이트가 현재 저장소 상태에 맞는 범위까지 실행

- [ ] **Step 5: 최종 커밋**

```bash
git add docs/generated/commercial-status.md \
        docs/generated/commercial-status.json \
        docs/product/roadmap/status.md
git commit -m "chore(roadmap): 전체 상용 완성 상태 산출물 재생성"
```

---

Plan complete and saved to `docs/plans/2026-04-16-ralph-loop-total-commercialization-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
