# OneERP Graphify CI Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** OneERP 코드/핵심 설계 문서를 대상으로 `graphify` 지식 그래프를 생성하고, 저장소에는 요약본만 남기며 원본 산출물은 CI artifact로 보관하는 파이프라인을 추가한다.

**Architecture:** 실행 정본은 `scripts/graphify/run.sh` 하나로 고정하고, 입력 범위는 별도 빌더가 스테이징한다. 결과는 `artifacts/graphify/latest/`에 생성한 뒤 `docs/generated/graphify/GRAPH_REPORT.md`와 `INDEX.md`만 저장소에 동기화한다. CI는 `.gitea/workflows/graphify-knowledge-graph.yml`에서 이 스크립트를 호출하고 아티팩트 업로드와 요약본 커밋만 담당한다.

**Tech Stack:** Bash, Python 3.14 표준 라이브러리, pytest, Gitea Actions YAML, Makefile, `graphifyy`/`graphify` CLI

---

### Task 1: graphify 입력 트리 빌더와 실행 스크립트 골격을 만든다

**Files:**
- Create: `tests/unit/test_graphify_runner_contract.py`
- Create: `scripts/graphify/build_input_tree.py`
- Create: `scripts/graphify/run.sh`
- Modify: `Makefile`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_graphify_runner_contract.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_graphify_runner가_입력범위와_출력경로를_고정한다() -> None:
    script = (ROOT / "scripts" / "graphify" / "run.sh").read_text(encoding="utf-8")
    for snippet in (
        "core",
        "services",
        "planes",
        "web",
        "docs/governance",
        "docs/engineering",
        "docs/product/roadmap",
        "artifacts/graphify/latest",
        "docs/generated/graphify/GRAPH_REPORT.md",
        "docs/generated/graphify/INDEX.md",
    ):
        assert snippet in script


def test_graphify_input_builder가_제외경로를_강제한다() -> None:
    script = (ROOT / "scripts" / "graphify" / "build_input_tree.py").read_text(encoding="utf-8")
    for snippet in (
        "node_modules",
        ".venv",
        ".next",
        "artifacts",
        "docs/generated",
        ".worktrees",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".planning",
    ):
        assert snippet in script


def test_makefile이_graphify_타깃을_노출한다() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "graphify:" in text
    assert "scripts/graphify/run.sh" in text
```

- [ ] **Step 2: 테스트가 실제로 실패하는지 확인**

Run:
```bash
uv run pytest tests/unit/test_graphify_runner_contract.py -v
```

Expected:
- `scripts/graphify/run.sh` / `build_input_tree.py` 부재로 FAIL

- [ ] **Step 3: 입력 트리 빌더 작성**

`scripts/graphify/build_input_tree.py` 생성:

```python
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "artifacts" / "graphify" / "input"
INCLUDE_DIRS = [
    ROOT / "core",
    ROOT / "services",
    ROOT / "planes",
    ROOT / "web",
    ROOT / "docs" / "governance",
    ROOT / "docs" / "engineering",
    ROOT / "docs" / "product" / "roadmap",
]
EXCLUDE_NAMES = {
    "node_modules",
    ".venv",
    ".next",
    "artifacts",
    "generated",
    ".worktrees",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".planning",
}


def should_ignore(path: Path) -> bool:
    return any(part in EXCLUDE_NAMES for part in path.parts)


def copy_tree(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if should_ignore(item.relative_to(src)):
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True, exist_ok=True)
    for source in INCLUDE_DIRS:
        copy_tree(source, TARGET / source.relative_to(ROOT))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 실행 스크립트와 Make 타깃 작성**

`scripts/graphify/run.sh` 생성:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

INPUT_DIR="$ROOT_DIR/artifacts/graphify/input"
OUTPUT_DIR="$ROOT_DIR/artifacts/graphify/latest"
DOC_DIR="$ROOT_DIR/docs/generated/graphify"

command -v graphify >/dev/null 2>&1 || {
  echo "graphify CLI가 없습니다. 'pip install graphifyy && graphify install' 필요"
  exit 1
}

python3 scripts/graphify/build_input_tree.py
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR" "$DOC_DIR"

graphify "$INPUT_DIR" --output "$OUTPUT_DIR"
cp "$OUTPUT_DIR/GRAPH_REPORT.md" "$DOC_DIR/GRAPH_REPORT.md"
```

`Makefile` 수정:

```make
.PHONY: graphify

graphify:  ## graphify 지식 그래프 생성
	./scripts/graphify/run.sh
```

- [ ] **Step 5: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_graphify_runner_contract.py -v
```

Expected:
- PASS

- [ ] **Step 6: 커밋**

```bash
git add tests/unit/test_graphify_runner_contract.py \
        scripts/graphify/build_input_tree.py \
        scripts/graphify/run.sh \
        Makefile
git commit -m "feat(graphify): add local graph generation runner"
```

### Task 2: 저장소 커밋용 요약본과 인덱스 렌더를 추가한다

**Files:**
- Create: `tests/unit/test_graphify_generated_docs_contract.py`
- Create: `scripts/graphify/render_index.py`
- Create: `docs/generated/graphify/INDEX.md`
- Modify: `docs/generated/INDEX.md`
- Modify: `scripts/graphify/run.sh`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_graphify_generated_docs_contract.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_graphify_index가_요약본과_원본보관정책을_기록한다() -> None:
    text = (ROOT / "docs" / "generated" / "graphify" / "INDEX.md").read_text(encoding="utf-8")
    assert "GRAPH_REPORT.md" in text
    assert "artifacts/graphify/latest" in text
    assert "main" in text
    assert "schedule" in text


def test_generated_index가_graphify_요약본을_링크한다() -> None:
    text = (ROOT / "docs" / "generated" / "INDEX.md").read_text(encoding="utf-8")
    assert "graphify/GRAPH_REPORT.md" in text


def test_runner가_index_renderer를_호출한다() -> None:
    script = (ROOT / "scripts" / "graphify" / "run.sh").read_text(encoding="utf-8")
    assert "render_index.py" in script
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run pytest tests/unit/test_graphify_generated_docs_contract.py -v
```

Expected:
- `INDEX.md` 부재 또는 링크 누락으로 FAIL

- [ ] **Step 3: 인덱스 렌더러 작성**

`scripts/graphify/render_index.py` 생성:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "docs" / "generated" / "graphify" / "INDEX.md"


def main() -> None:
    trigger = os.environ.get("GRAPHIFY_TRIGGER", "local")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        "\n".join(
            [
                "# Graphify 생성 인덱스",
                "",
                f"- 생성 시각: {generated_at}",
                f"- 실행 소스: {trigger}",
                "- 요약본: [GRAPH_REPORT.md](./GRAPH_REPORT.md)",
                "- 원본 산출물: `artifacts/graphify/latest/` (CI artifact 보관)",
                "- 입력 범위: `core/`, `services/`, `planes/`, `web/`, `docs/governance/`, `docs/engineering/`, `docs/product/roadmap/`",
                "- 제외 범위: `node_modules/`, `.venv/`, `.next/`, `artifacts/`, `docs/generated/`, `.worktrees/`, 캐시류",
                "- CI 트리거: `main`, `schedule`",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 실행 스크립트와 문서 인덱스 연결**

`scripts/graphify/run.sh` 수정:

```bash
python3 scripts/graphify/render_index.py
```

`docs/generated/INDEX.md`에 graphify 링크 추가:

```md
| `graphify` | [문서](./graphify/GRAPH_REPORT.md) |
```

- [ ] **Step 5: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_graphify_generated_docs_contract.py -v
```

Expected:
- PASS

- [ ] **Step 6: 커밋**

```bash
git add tests/unit/test_graphify_generated_docs_contract.py \
        scripts/graphify/render_index.py \
        docs/generated/graphify/INDEX.md \
        docs/generated/INDEX.md \
        scripts/graphify/run.sh
git commit -m "feat(graphify): add generated summary index"
```

### Task 3: CI workflow와 아티팩트/요약본 반영 경로를 추가한다

**Files:**
- Create: `tests/unit/test_graphify_workflow_contract.py`
- Create: `.gitea/workflows/graphify-knowledge-graph.yml`

- [ ] **Step 1: 실패 테스트 먼저 작성**

`tests/unit/test_graphify_workflow_contract.py` 생성:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_graphify_workflow가_main과_schedule을_트리거한다() -> None:
    text = (ROOT / ".gitea" / "workflows" / "graphify-knowledge-graph.yml").read_text(encoding="utf-8")
    assert "branches:" in text
    assert "- main" in text
    assert "schedule:" in text
    assert "cron:" in text


def test_graphify_workflow가_아티팩트와_요약본_커밋을_포함한다() -> None:
    text = (ROOT / ".gitea" / "workflows" / "graphify-knowledge-graph.yml").read_text(encoding="utf-8")
    for snippet in (
        "artifacts/graphify/latest",
        "docs/generated/graphify/GRAPH_REPORT.md",
        "docs/generated/graphify/INDEX.md",
        "upload-artifact",
        "[skip ci]",
    ):
        assert snippet in text
```

- [ ] **Step 2: 실패 확인**

Run:
```bash
uv run pytest tests/unit/test_graphify_workflow_contract.py -v
```

Expected:
- workflow 부재로 FAIL

- [ ] **Step 3: workflow 작성**

`.gitea/workflows/graphify-knowledge-graph.yml` 생성:

```yaml
name: Graphify Knowledge Graph

on:
  push:
    branches:
      - main
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  graphify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
      - name: Install graphify
        run: |
          python -m pip install --upgrade pip
          pip install graphifyy
      - name: Run graphify
        env:
          GRAPHIFY_TRIGGER: ${{ github.event_name == 'schedule' && 'schedule' || 'main' }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          chmod +x scripts/graphify/run.sh
          ./scripts/graphify/run.sh
      - name: Upload graph artifacts
        uses: actions/upload-artifact@v4
        with:
          name: graphify-output
          path: artifacts/graphify/latest
      - name: Commit summary docs
        run: |
          git config user.name "oneerp-bot"
          git config user.email "oneerp-bot@users.noreply.local"
          git add docs/generated/graphify/GRAPH_REPORT.md docs/generated/graphify/INDEX.md docs/generated/INDEX.md
          git diff --cached --quiet && exit 0
          git commit -m "docs(graphify): refresh knowledge graph summary [skip ci]"
          git push
```

- [ ] **Step 4: 테스트 재실행**

Run:
```bash
uv run pytest tests/unit/test_graphify_workflow_contract.py -v
```

Expected:
- PASS

- [ ] **Step 5: 커밋**

```bash
git add tests/unit/test_graphify_workflow_contract.py \
        .gitea/workflows/graphify-knowledge-graph.yml
git commit -m "ci(graphify): add graph generation workflow"
```

### Task 4: 로컬/CI 검증 루프를 닫는다

**Files:**
- Modify: `docs/generated/graphify/GRAPH_REPORT.md` (생성 결과)
- Modify: `docs/generated/graphify/INDEX.md` (생성 결과)
- Modify: `docs/generated/INDEX.md`

- [ ] **Step 1: 로컬 계약 테스트 일괄 실행**

Run:
```bash
uv run pytest \
  tests/unit/test_graphify_runner_contract.py \
  tests/unit/test_graphify_generated_docs_contract.py \
  tests/unit/test_graphify_workflow_contract.py \
  -v
```

Expected:
- 전부 PASS

- [ ] **Step 2: 로컬 graphify 실행**

Run:
```bash
GRAPHIFY_TRIGGER=local ./scripts/graphify/run.sh
```

Expected:
- `artifacts/graphify/latest/graph.html`
- `artifacts/graphify/latest/graph.json`
- `artifacts/graphify/latest/GRAPH_REPORT.md`
- `docs/generated/graphify/GRAPH_REPORT.md`
- `docs/generated/graphify/INDEX.md`

- [ ] **Step 3: 산출물 존재 검증**

Run:
```bash
test -f artifacts/graphify/latest/graph.html
test -f artifacts/graphify/latest/graph.json
test -f docs/generated/graphify/GRAPH_REPORT.md
test -f docs/generated/graphify/INDEX.md
```

Expected:
- exit 0

- [ ] **Step 4: 최종 커밋**

```bash
git add docs/generated/graphify/GRAPH_REPORT.md \
        docs/generated/graphify/INDEX.md \
        docs/generated/INDEX.md
git commit -m "docs(graphify): generate initial knowledge graph summary"
```

Plan complete and saved to `docs/plans/2026-04-16-graphify-ci-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
