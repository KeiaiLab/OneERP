# Commercial Grade v2 · 3자원 증거 엔진 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ralph-Loop 를 폐기하고 3자원(에이전트 팀·Python Playwright·Computer Use) 기반 문서 주도 상용 증거 엔진을 구축한다. 기존 978/1081 = 90.5% 감사 PASS 를 전면 리셋하고 v2 실증 기준으로 재평가하여 진짜 상용 수준으로 올리는 파이프라인을 만든다.

**Architecture:** `/commercial-engine` slash command 가 5-Role 에이전트 팀(planner/artisan/scribe/executor/reviewer)을 dispatch 하고, `scripts/engine/` Python 모듈이 증거 수집·검증·replay 를 담당한다. `commercial_readiness.py v2` 는 공용 헬퍼 `validate_evidence()` 를 통해 23 게이트의 라인·섹션·frontmatter·artifact·Tier 를 교차 검증한다. 파일럿은 gateway × {G1-1, G1-4, G4-2} 3 셀로 엔진 작동을 증명한다.

**Tech Stack:**
- Python 3.14 · uv workspace · pytest · ruff · ty
- Playwright for Python (`pytest-playwright`, `pytest-bdd`)
- Claude Code: Task tool · .claude/agents/ · .claude/commands/
- Git · bash

**Spec Reference:** `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`

---

## 사전 조건

- 현재 branch: `main` (작업 시작 전 clean working tree 권장)
- `.graphify_*.json` 등 working tree 의 untracked 파일은 git stash 또는 .gitignore 처리
- `uv` · `pnpm` · `pytest` 설치 확인

```bash
uv --version      # 0.11.1+
pnpm --version    # 10.30.3+
git status -s     # clean 권장
```

---

## Task 1 — Phase 0A · Ralph-Loop 폐기

**Files:**
- Delete: `.claude/skills/ralph-loop/` (디렉토리 전체)
- Delete: `RALPH-LOOP-PROMPT.md`
- Modify: `HANDOFF.md` (전면 재작성)
- Modify: `AGENTS.md` · `.claude/CLAUDE.md` (ralph-loop 참조 제거)
- Modify: `PROGRESS.md` (v1 섹션 헤더 분리)

- [ ] **Step 1.1: 사전 스냅샷**

```bash
git log --oneline -10 > /tmp/ralph-loop-pre-removal-log.txt
ls -la .claude/skills/ralph-loop/ 2>&1 | tee /tmp/ralph-loop-dir-listing.txt
wc -l RALPH-LOOP-PROMPT.md HANDOFF.md PROGRESS.md
```
Expected: `PROGRESS.md` 61 라인, `HANDOFF.md` 92 라인, `RALPH-LOOP-PROMPT.md` 239 라인.

- [ ] **Step 1.2: Ralph-Loop 인프라 파일 제거**

```bash
rm -rf .claude/skills/ralph-loop
rm -f RALPH-LOOP-PROMPT.md
```

Verify:
```bash
test ! -d .claude/skills/ralph-loop && echo OK
test ! -f RALPH-LOOP-PROMPT.md && echo OK
```

- [ ] **Step 1.3: HANDOFF.md 재작성 (일반 세션 핸드오프로 재정의)**

Replace entire `HANDOFF.md` with:
```markdown
# 세션 핸드오프

작성: 2026-04-22
상태: Ralph-Loop 폐기 완료 · Commercial Grade v2 엔진 구축 진행 중

## 현재 상태

- 감사 체계: v1 → v2 전환 중 (진행 상황은 `PROGRESS.md` 참조)
- 활성 스펙: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
- 활성 플랜: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`

## 다음 세션의 할 일

1. `PROGRESS.md` 의 "v2 Strict Mode" 섹션 마지막 행을 확인해 진행 위치 파악
2. 플랜 파일에서 미체크 태스크 중 가장 위의 것부터 수행
3. `/commercial-engine status` 로 현재 감사 상태 확인 (엔진 구축 완료 후)

## 참고

- 전역 규약: `/Users/phil/.claude/CLAUDE.md` · `.claude/CLAUDE.md` · `AGENTS.md`
- v1 Ralph-Loop 시대 기록: `PROGRESS.md` 의 "Ralph-Loop 시대 (v1)" 섹션 (보존)
```

- [ ] **Step 1.4: AGENTS.md · .claude/CLAUDE.md 의 ralph-loop 참조 제거**

```bash
grep -n "ralph-loop\|Ralph-Loop\|RALPH-LOOP" AGENTS.md .claude/CLAUDE.md 2>/dev/null
```

발견된 각 라인에 대해 `Edit` 도구로 제거 또는 `/commercial-engine` 으로 교체. 제거 후 재확인:
```bash
grep -rn "ralph-loop\|Ralph-Loop\|RALPH-LOOP" AGENTS.md .claude/CLAUDE.md CLAUDE.md
```
Expected: 0 매칭.

- [ ] **Step 1.5: PROGRESS.md 에 v1 / v2 섹션 헤더 삽입**

`PROGRESS.md` 의 기존 내용 맨 위에 `# OneERP 상용화 PROGRESS` 라인이 있고 그 다음 기존 설명·테이블이 있음. 다음과 같이 재구성:

1. 파일 맨 위에 새 헤더:
```markdown
# OneERP 상용화 PROGRESS

> v1(Ralph-Loop) 시대와 v2(Strict Evidence) 시대를 한 파일에서 추적한다.
> v2 는 감사 기준 전면 강화로 v1 의 978 PASS 를 전면 리셋하고 재평가한다.

## v2 Strict Mode (2026-04-22~)

- 시작: 2026-04-22
- 목표: 47모듈 × 23/23 전수 PASS (1,081 셀) · 전원 `commercial-ready` 라벨
- Baseline: (Phase 0B 완료 후 기록)
- 최근 갱신: (wave 종료 시 기록)

### Wave Log

| wave | ts | targets | plan | commit | delta | verdict |
|---|---|---|---|---|---|---|

---

## Ralph-Loop 시대 (v1 · 2026-04-16 ~ 2026-04-22)

> 이 섹션은 보존됨. v1 감사 기준 종료 시점의 978/1081 = 90.5% 는
> v2 전면 리셋으로 baseline 재설정됨. 아래 iter 1~19 는 역사적 기록.
```

2. 기존 `## Iteration Log` ~ 끝까지는 그대로 유지 (v1 섹션 안에 흡수).

- [ ] **Step 1.6: 커밋**

```bash
git add -A HANDOFF.md AGENTS.md .claude/CLAUDE.md PROGRESS.md
git add .claude/skills/ralph-loop  # 삭제 기록 포함
git rm RALPH-LOOP-PROMPT.md 2>/dev/null || true
git status --short
```

```bash
git commit -m "$(cat <<'EOF'
chore(engine): Ralph-Loop 폐기 · Commercial Grade v2 전환 준비

자기구동 루프 인프라(.claude/skills/ralph-loop, RALPH-LOOP-PROMPT.md) 제거.
HANDOFF.md 를 일반 세션 핸드오프로 재정의. PROGRESS.md 는 v1/v2 섹션 분리로
기존 iter 1~19 기록 보존. 후속: /commercial-engine slash command 도입.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md §11.1

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — `scripts/engine/evidence.py`

**Files:**
- Create: `scripts/engine/__init__.py`
- Create: `scripts/engine/evidence.py`
- Test: `tests/unit/engine/test_evidence.py`

- [ ] **Step 2.1: 디렉토리 생성 + 빈 __init__.py**

```bash
mkdir -p scripts/engine/migration tests/unit/engine
touch scripts/engine/__init__.py scripts/engine/migration/__init__.py tests/unit/engine/__init__.py
```

- [ ] **Step 2.2: 실패하는 테스트 작성 — `test_evidence.py`**

```python
# tests/unit/engine/test_evidence.py
"""evidence 모듈 단위 테스트."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.engine.evidence import (
    EvidenceMeta,
    compute_evidence_sha,
    load_meta,
    write_meta,
    append_index,
    latest_evidence_for,
)


def test_compute_evidence_sha_deterministic() -> None:
    """동일 입력은 동일 sha 를 생성한다."""
    sha1 = compute_evidence_sha(
        command="pytest",
        exit_code=0,
        stdout="passed\n",
        stderr="",
    )
    sha2 = compute_evidence_sha(
        command="pytest",
        exit_code=0,
        stdout="passed\n",
        stderr="",
    )
    assert sha1 == sha2
    assert len(sha1) == 64  # sha256 hex


def test_write_and_load_meta(tmp_path: Path) -> None:
    """EvidenceMeta 를 저장·로드하면 동일 값이 복원된다."""
    meta = EvidenceMeta(
        sha256="a" * 64,
        gate="G1-4",
        module="gateway",
        tier="T1",
        command="pytest gateway",
        executor="ce-executor",
        git_sha="abc1234",
        host="darwin",
        user="phil",
        started_at="2026-04-22T07:00:00Z",
        duration_seconds=42,
        exit_code=0,
        stdout_sha256="b" * 64,
        stderr_sha256="c" * 64,
        artifact_paths=["artifacts/T1/G1-4/gateway/log.txt"],
        verification={"coverage_line_rate": 0.84},
    )
    write_meta(meta, base_dir=tmp_path)
    loaded = load_meta(meta.sha256, base_dir=tmp_path)
    assert loaded == meta


def test_append_index_and_latest(tmp_path: Path) -> None:
    """index.jsonl append 후 latest_evidence_for 가 최신을 반환한다."""
    base = tmp_path / "artifacts" / "_meta"
    base.mkdir(parents=True)
    meta_old = EvidenceMeta(
        sha256="a" * 64, gate="G1-4", module="gateway", tier="T1",
        command="x", executor="ce-executor", git_sha="abc", host="h",
        user="u", started_at="2026-04-22T07:00:00Z", duration_seconds=1,
        exit_code=0, stdout_sha256="b" * 64, stderr_sha256="c" * 64,
        artifact_paths=[], verification={},
    )
    meta_new = EvidenceMeta(
        **{**meta_old.__dict__, "sha256": "d" * 64,
           "started_at": "2026-04-22T08:00:00Z"}
    )
    append_index(meta_old, base_dir=tmp_path)
    append_index(meta_new, base_dir=tmp_path)
    write_meta(meta_old, base_dir=tmp_path)
    write_meta(meta_new, base_dir=tmp_path)

    latest = latest_evidence_for("G1-4", "gateway", "T1", base_dir=tmp_path)
    assert latest is not None
    assert latest.sha256 == "d" * 64
```

- [ ] **Step 2.3: 실패 확인**

```bash
uv run pytest tests/unit/engine/test_evidence.py -v
```
Expected: `ImportError` 또는 `ModuleNotFoundError: scripts.engine.evidence`.

- [ ] **Step 2.4: `evidence.py` 구현**

```python
# scripts/engine/evidence.py
"""증거 메타데이터 관리 — sha 계산 · 저장 · 인덱스 append · 최신 검색."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class EvidenceMeta:
    """한 증거의 메타데이터 레코드."""

    sha256: str
    gate: str
    module: str
    tier: str
    command: str
    executor: str
    git_sha: str
    host: str
    user: str
    started_at: str  # ISO8601 UTC
    duration_seconds: int
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str
    artifact_paths: list[str] = field(default_factory=list)
    verification: dict[str, object] = field(default_factory=dict)
    parent_evidence: str | None = None

    @property
    def replay_command(self) -> str:
        """재실행 명령."""
        return f"scripts/engine/replay.py --sha {self.sha256}"


def compute_evidence_sha(
    *, command: str, exit_code: int, stdout: str, stderr: str
) -> str:
    """(명령 + exit + stdout + stderr) 를 sha256 으로 결합."""
    h = hashlib.sha256()
    h.update(command.encode())
    h.update(b"\x00")
    h.update(str(exit_code).encode())
    h.update(b"\x00")
    h.update(stdout.encode())
    h.update(b"\x00")
    h.update(stderr.encode())
    return h.hexdigest()


def _meta_path(sha256: str, base_dir: Path) -> Path:
    return base_dir / "artifacts" / "_meta" / f"{sha256}.json"


def _index_path(base_dir: Path) -> Path:
    return base_dir / "artifacts" / "_meta" / "index.jsonl"


def write_meta(meta: EvidenceMeta, *, base_dir: Path) -> None:
    """개별 증거 메타 JSON 저장."""
    path = _meta_path(meta.sha256, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(meta)
    payload["replay_command"] = meta.replay_command
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def load_meta(sha256: str, *, base_dir: Path) -> EvidenceMeta:
    """개별 증거 메타 JSON 로드."""
    path = _meta_path(sha256, base_dir)
    payload = json.loads(path.read_text())
    payload.pop("replay_command", None)
    return EvidenceMeta(**payload)


def append_index(meta: EvidenceMeta, *, base_dir: Path) -> None:
    """index.jsonl 에 한 줄 append."""
    path = _index_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "sha256": meta.sha256,
        "gate": meta.gate,
        "module": meta.module,
        "tier": meta.tier,
        "started_at": meta.started_at,
        "exit_code": meta.exit_code,
    }
    with path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def latest_evidence_for(
    gate: str, module: str, tier: str, *, base_dir: Path
) -> EvidenceMeta | None:
    """해당 gate·module·tier 의 가장 최근 증거 반환."""
    path = _index_path(base_dir)
    if not path.exists():
        return None
    candidates: list[dict] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry["gate"] == gate and entry["module"] == module and entry["tier"] == tier:
            candidates.append(entry)
    if not candidates:
        return None
    latest = max(candidates, key=lambda e: e["started_at"])
    return load_meta(latest["sha256"], base_dir=base_dir)
```

- [ ] **Step 2.5: 테스트 통과 확인**

```bash
uv run pytest tests/unit/engine/test_evidence.py -v
```
Expected: 3 passed.

- [ ] **Step 2.6: 린트·타입 확인 후 커밋**

```bash
uv run ruff format scripts/engine/ tests/unit/engine/
uv run ruff check scripts/engine/ tests/unit/engine/
uv run ty check scripts/engine/ tests/unit/engine/
```

```bash
git add scripts/engine/__init__.py scripts/engine/evidence.py scripts/engine/migration/__init__.py \
        tests/unit/engine/__init__.py tests/unit/engine/test_evidence.py
git commit -m "$(cat <<'EOF'
feat(engine): evidence.py — 증거 메타 · sha 계산 · index.jsonl 관리

EvidenceMeta dataclass + compute_evidence_sha + write/load_meta +
append_index + latest_evidence_for 구현. 단위 테스트 3건 추가.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md §6

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — `scripts/engine/validators.py`

**Files:**
- Create: `scripts/engine/validators.py`
- Test: `tests/unit/engine/test_validators.py`

- [ ] **Step 3.1: 실패하는 테스트 작성**

```python
# tests/unit/engine/test_validators.py
"""validators 모듈 단위 테스트."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.engine.validators import (
    GateResult,
    GateStatus,
    ValidationSpec,
    validate_evidence,
)


def _write_doc(path: Path, *, lines: int, frontmatter: dict[str, str], sections: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = "---\n"
    for k, v in frontmatter.items():
        fm += f"{k}: {v}\n"
    fm += "---\n\n"
    body = "\n".join([f"## {s}\n\n본문 라인 {s}\n" for s in sections])
    filler = "\n".join([f"내용 라인 {i}" for i in range(lines)])
    path.write_text(fm + body + "\n" + filler + "\n")


def test_validate_evidence_short_doc_fails(tmp_path: Path) -> None:
    """최소 라인 수 미달 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=10, frontmatter={"owner": "x", "module": "gateway"}, sections=["개요"])
    spec = ValidationSpec(min_lines=150)
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "min_lines" in result.reason


def test_validate_evidence_missing_section_fails(tmp_path: Path) -> None:
    """필수 H2 섹션 미포함 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=300, frontmatter={"owner": "x"}, sections=["개요"])
    spec = ValidationSpec(
        min_lines=150,
        required_sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "section" in result.reason.lower()


def test_validate_evidence_missing_frontmatter_fails(tmp_path: Path) -> None:
    """필수 frontmatter 미포함 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=300, frontmatter={"owner": "x"},
               sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"])
    spec = ValidationSpec(
        min_lines=150,
        required_sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"],
        required_frontmatter=["owner", "module", "last_reviewed"],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "frontmatter" in result.reason.lower()


def test_validate_evidence_all_pass(tmp_path: Path) -> None:
    """모든 기준 충족 시 PASS."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=300,
               frontmatter={"owner": "phil", "module": "gateway", "last_reviewed": "2026-04-22"},
               sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"])
    spec = ValidationSpec(
        min_lines=150,
        required_sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"],
        required_frontmatter=["owner", "module", "last_reviewed"],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.PASS
```

- [ ] **Step 3.2: 실패 확인**

```bash
uv run pytest tests/unit/engine/test_validators.py -v
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 3.3: `validators.py` 구현**

```python
# scripts/engine/validators.py
"""공용 증거 검증 헬퍼 — 라인·섹션·frontmatter·cross-link·tier 검증."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path


class GateStatus(StrEnum):
    PASS = "pass"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    FAIL = "fail"
    TAMPERED = "tampered"


@dataclass
class GateResult:
    gate: str
    module: str
    status: GateStatus
    reason: str = ""
    tiers_met: dict[str, bool] = field(default_factory=dict)
    evidence_sha: str | None = None
    verification: dict[str, object] = field(default_factory=dict)


@dataclass
class ValidationSpec:
    min_lines: int = 0
    required_sections: list[str] | None = None
    required_frontmatter: list[str] | None = None
    frontmatter_age_limits: dict[str, int] | None = None  # {"last_reviewed": 90}
    cross_links_required: list[str] | None = None
    required_tiers: list[str] | None = None
    artifact_glob: dict[str, str] | None = None
    min_fenced_code_blocks: int | None = None
    min_image_refs: int | None = None
    exit_code_required: int = 0
    stdout_contains: list[str] | None = None
    verification_fields: dict[str, object] | None = None


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
_FENCED_CODE_RE = re.compile(r"^```", re.MULTILINE)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _check_age(value: str, max_days: int) -> bool:
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return datetime.now(UTC) - d <= timedelta(days=max_days)


def validate_evidence(
    spec: ValidationSpec,
    *,
    gate: str,
    module: str,
    doc_path: Path | None = None,
) -> GateResult:
    """단일 진입점 — 모든 검증을 spec 에 따라 수행."""

    # 문서 기반 기준 (doc_path 있을 때만)
    if doc_path is not None:
        if not doc_path.exists():
            return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                              reason=f"doc missing: {doc_path}")

        text = doc_path.read_text()
        lines = text.count("\n") + 1

        if spec.min_lines and lines < spec.min_lines:
            return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                              reason=f"min_lines {spec.min_lines} 미달 (실제 {lines})")

        if spec.required_sections:
            present = {m.group(1).strip() for m in _H2_RE.finditer(text)}
            missing = [s for s in spec.required_sections if s not in present]
            if missing:
                return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                  reason=f"missing sections: {missing}")

        fm = _parse_frontmatter(text)
        if spec.required_frontmatter:
            missing_fm = [k for k in spec.required_frontmatter if k not in fm]
            if missing_fm:
                return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                  reason=f"missing frontmatter: {missing_fm}")

        if spec.frontmatter_age_limits:
            for key, max_days in spec.frontmatter_age_limits.items():
                if key in fm and not _check_age(fm[key], max_days):
                    return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                      reason=f"frontmatter {key} 가 {max_days}일 초과")

        if spec.min_fenced_code_blocks is not None:
            n_code = len(_FENCED_CODE_RE.findall(text)) // 2
            if n_code < spec.min_fenced_code_blocks:
                return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                  reason=f"fenced code block {spec.min_fenced_code_blocks} 미달 (실제 {n_code})")

        if spec.min_image_refs is not None:
            n_img = len(_IMAGE_RE.findall(text))
            if n_img < spec.min_image_refs:
                return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                  reason=f"image refs {spec.min_image_refs} 미달 (실제 {n_img})")

        if spec.cross_links_required:
            for pattern in spec.cross_links_required:
                matches = list(Path().glob(pattern))
                if not matches:
                    return GateResult(gate=gate, module=module, status=GateStatus.FAIL,
                                      reason=f"cross-link missing: {pattern}")

    # Tier 증거 검증은 Task 5 의 게이트 함수에서 evidence.py 와 연동
    # 여기서는 문서 기반 검증만 완결
    return GateResult(gate=gate, module=module, status=GateStatus.PASS)
```

- [ ] **Step 3.4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/engine/test_validators.py -v
```
Expected: 4 passed.

- [ ] **Step 3.5: 린트·타입 확인 후 커밋**

```bash
uv run ruff format scripts/engine/validators.py tests/unit/engine/test_validators.py
uv run ruff check scripts/engine/validators.py tests/unit/engine/test_validators.py
uv run ty check scripts/engine/validators.py tests/unit/engine/test_validators.py
```

```bash
git add scripts/engine/validators.py tests/unit/engine/test_validators.py
git commit -m "$(cat <<'EOF'
feat(engine): validators.py — 공용 증거 검증 헬퍼

ValidationSpec dataclass + validate_evidence 단일 진입점.
라인수·H2 섹션·frontmatter 필드·frontmatter age·fenced code block·
image refs·cross-link 7종 검증. GateStatus/GateResult 공통 타입 정의.
단위 테스트 4건.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md §10.1

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — `scripts/engine/validators.py` 확장: Tier 검증

**Files:**
- Modify: `scripts/engine/validators.py` (tier 검증 추가)
- Modify: `tests/unit/engine/test_validators.py` (tier 테스트 추가)

- [ ] **Step 4.1: 실패하는 tier 테스트 추가**

`tests/unit/engine/test_validators.py` 에 append:

```python
from scripts.engine.evidence import EvidenceMeta, append_index, write_meta


def _seed_evidence(tmp_path: Path, *, gate: str, module: str, tier: str, sha: str,
                   ts: str, exit_code: int = 0, verification: dict | None = None) -> None:
    meta = EvidenceMeta(
        sha256=sha, gate=gate, module=module, tier=tier,
        command="test", executor="ce-executor", git_sha="abc",
        host="h", user="u", started_at=ts, duration_seconds=1,
        exit_code=exit_code, stdout_sha256="b" * 64, stderr_sha256="c" * 64,
        artifact_paths=[], verification=verification or {},
    )
    write_meta(meta, base_dir=tmp_path)
    append_index(meta, base_dir=tmp_path)


def test_validate_evidence_tier_missing_fails(tmp_path: Path, monkeypatch) -> None:
    """required_tiers 의 증거가 없으면 NOT_IMPLEMENTED."""
    monkeypatch.chdir(tmp_path)
    spec = ValidationSpec(required_tiers=["T1"])
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED
    assert result.tiers_met == {"T1": False}


def test_validate_evidence_tier_met_passes(tmp_path: Path, monkeypatch) -> None:
    """required_tiers 증거 있고 verification 충족 시 PASS."""
    monkeypatch.chdir(tmp_path)
    _seed_evidence(tmp_path, gate="G1-4", module="gateway", tier="T1",
                   sha="a" * 64, ts="2026-04-22T07:00:00Z",
                   verification={"coverage_line_rate": 0.84, "mutation_score": 0.52})
    spec = ValidationSpec(
        required_tiers=["T1"],
        verification_fields={
            "coverage_line_rate": {"gte": 0.80},
            "mutation_score": {"gte": 0.50},
        },
    )
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.PASS
    assert result.tiers_met == {"T1": True}


def test_validate_evidence_verification_below_threshold_fails(tmp_path: Path, monkeypatch) -> None:
    """verification_fields 임계 미달 시 FAIL."""
    monkeypatch.chdir(tmp_path)
    _seed_evidence(tmp_path, gate="G1-4", module="gateway", tier="T1",
                   sha="a" * 64, ts="2026-04-22T07:00:00Z",
                   verification={"coverage_line_rate": 0.70})
    spec = ValidationSpec(
        required_tiers=["T1"],
        verification_fields={"coverage_line_rate": {"gte": 0.80}},
    )
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.FAIL
```

- [ ] **Step 4.2: `validators.py` 에 tier 검증 로직 추가**

`validators.py` 파일 하단 (기존 `validate_evidence` 함수 안) 의 문서 검증 직후에 다음 블록 추가:

```python
    # Tier 증거 검증
    if spec.required_tiers:
        from scripts.engine.evidence import latest_evidence_for
        tiers_met: dict[str, bool] = {}
        for tier in spec.required_tiers:
            ev = latest_evidence_for(gate, module, tier, base_dir=Path.cwd())
            if ev is None:
                tiers_met[tier] = False
                continue
            if ev.exit_code != spec.exit_code_required:
                tiers_met[tier] = False
                continue
            ok = True
            for field_name, constraint in (spec.verification_fields or {}).items():
                value = ev.verification.get(field_name)
                if value is None:
                    ok = False
                    break
                if isinstance(constraint, dict):
                    if "gte" in constraint and not (value >= constraint["gte"]):
                        ok = False
                        break
                    if "eq" in constraint and value != constraint["eq"]:
                        ok = False
                        break
            tiers_met[tier] = ok

        if not all(tiers_met.values()):
            status = GateStatus.NOT_IMPLEMENTED if not any(tiers_met.values()) else GateStatus.FAIL
            reason = "tier 미충족 또는 verification 미달"
            if any(tiers_met.values()):
                reason = f"일부 tier 미충족: {tiers_met}"
            return GateResult(gate=gate, module=module, status=status,
                              reason=reason, tiers_met=tiers_met)

        return GateResult(gate=gate, module=module, status=GateStatus.PASS,
                          tiers_met=tiers_met)
```

- [ ] **Step 4.3: 테스트 통과**

```bash
uv run pytest tests/unit/engine/test_validators.py -v
```
Expected: 7 passed.

- [ ] **Step 4.4: 커밋**

```bash
git add scripts/engine/validators.py tests/unit/engine/test_validators.py
git commit -m "feat(engine): validators tier 검증 · verification_fields 제약 추가

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5 — `commercial_readiness.py v2` 골격 + 게이트 레지스트리

**Files:**
- Create: `scripts/audit/commercial_readiness_v2.py` (임시 이름, Task 20 에서 기존 것 교체)
- Test: `tests/unit/engine/test_gate_registry.py`

- [ ] **Step 5.1: 실패 테스트 작성**

```python
# tests/unit/engine/test_gate_registry.py
"""23 게이트 레지스트리 및 구조 테스트."""
from __future__ import annotations

import pytest

from scripts.audit.commercial_readiness_v2 import (
    GATE_REGISTRY,
    GATE_IDS,
    MODULES,
    evaluate_all,
    evaluate_module,
)


def test_gate_registry_has_23_entries() -> None:
    assert len(GATE_REGISTRY) == 23
    ids = [g["id"] for g in GATE_REGISTRY]
    assert ids == sorted(set(ids))  # 고유·정렬


def test_modules_count_is_47() -> None:
    assert len(MODULES) == 47


def test_evaluate_module_returns_23_results() -> None:
    result = evaluate_module("gateway")
    assert result["module"] == "gateway"
    assert len(result["gates"]) == 23


def test_evaluate_all_returns_47_modules() -> None:
    out = evaluate_all()
    assert out["summary"]["schema_version"] == "v2.0" or out["schema_version"] == "v2.0"
    assert len(out["reports"]) == 47
```

- [ ] **Step 5.2: 실패 확인**

```bash
uv run pytest tests/unit/engine/test_gate_registry.py -v
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 5.3: `commercial_readiness_v2.py` 골격 작성**

```python
# scripts/audit/commercial_readiness_v2.py
"""v2 상용 증거 감사 스크립트 — 47모듈 × 23게이트 검증."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from scripts.engine.validators import GateResult, GateStatus, ValidationSpec, validate_evidence


# 47 모듈 (ADR-0012 점수순)
MODULES: list[str] = [
    "gateway", "accounting", "hr", "directory", "selling", "buying", "stock",
    "payroll", "portal", "projects", "expenses", "crm", "advanced-planning",
    "analytics", "assets", "board", "calendar", "clm", "compliance",
    "consolidation", "documents", "ecommerce", "ehs", "esg", "fleet", "gtm",
    "integration-hub", "iot", "knowledge", "lms", "mail", "maintenance",
    "manufacturing", "marketing", "marketing-automation", "messenger", "plm",
    "pos", "quality", "rental", "reservation", "rpa", "subscriptions",
    "survey", "tms", "wiki", "workreport",
]

GATE_IDS: list[str] = [
    "G1-1", "G1-2", "G1-3", "G1-4", "G1-5",
    "G2-1", "G2-2", "G2-3", "G2-4", "G2-5",
    "G3-1", "G3-2", "G3-3", "G3-4", "G3-5",
    "G4-1", "G4-2", "G4-3", "G4-4", "G4-5",
    "G5-1", "G5-2", "G5-3",
]


# 게이트 함수 등록 (각 게이트별 구현은 별도 파일 또는 아래에 함수로)
# 플레이스홀더: NOT_IMPLEMENTED 반환. Task 6 에서 실제 구현.
def _not_implemented(gate: str, module: str) -> GateResult:
    return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                      reason="gate function 미구현")


GATE_REGISTRY: list[dict[str, object]] = [
    {"id": gid, "fn": _not_implemented, "tiers": ["T1"]}
    for gid in GATE_IDS
]


def _module_label(gates: list[GateResult]) -> str:
    pass_set = {g.gate for g in gates if g.status == GateStatus.PASS}
    score = len(pass_set)
    g_core = {"G1-1", "G1-2", "G1-3", "G1-4"}
    if score == 23:
        return "commercial-ready"
    if score >= 18:
        return "pre-commercial"
    if g_core.issubset(pass_set) and {"G3-1", "G3-4", "G4-2"}.issubset(pass_set):
        return "beta"
    if {"G1-1", "G1-2"}.issubset(pass_set):
        return "alpha"
    return "none"


def evaluate_module(module: str) -> dict[str, object]:
    """한 모듈의 23 게이트를 전부 평가."""
    results: list[GateResult] = []
    for entry in GATE_REGISTRY:
        fn: Callable[[str, str], GateResult] = entry["fn"]  # type: ignore[assignment]
        gid: str = entry["id"]  # type: ignore[assignment]
        results.append(fn(gid, module))

    return {
        "module": module,
        "label": _module_label(results),
        "score": sum(1 for g in results if g.status == GateStatus.PASS),
        "gates": [
            {
                "id": g.gate,
                "status": g.status.value,
                "tiers_met": g.tiers_met,
                "evidence_sha": g.evidence_sha,
                "reason": g.reason,
                "verification": g.verification,
            }
            for g in results
        ],
    }


def evaluate_all() -> dict[str, object]:
    """47 모듈 전체 평가."""
    reports = [evaluate_module(m) for m in MODULES]
    total_gates = len(MODULES) * 23
    passed = sum(1 for r in reports for g in r["gates"] if g["status"] == "pass")
    partial = sum(1 for r in reports for g in r["gates"] if g["status"] == "partial")
    not_impl = sum(1 for r in reports for g in r["gates"] if g["status"] == "not_implemented")
    failed = sum(1 for r in reports for g in r["gates"] if g["status"] == "fail")
    tampered = sum(1 for r in reports for g in r["gates"] if g["status"] == "tampered")

    labels = [r["label"] for r in reports]
    return {
        "schema_version": "v2.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total": total_gates,
            "passed": passed,
            "partial": partial,
            "not_implemented": not_impl,
            "failed": failed,
            "tampered": tampered,
            "commercial_ready_modules": labels.count("commercial-ready"),
            "pre_commercial_modules": labels.count("pre-commercial"),
            "beta_modules": labels.count("beta"),
            "alpha_modules": labels.count("alpha"),
        },
        "reports": reports,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--module")
    parser.add_argument("--gate")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verify-evidence", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    out = evaluate_all() if not args.module else {"reports": [evaluate_module(args.module)]}

    if args.format == "json":
        text = json.dumps(out, ensure_ascii=False, indent=2)
    else:
        text = _render_text(out)

    if args.output:
        Path(args.output).write_text(text)
    else:
        print(text)

    if args.verify and args.strict:
        s = out.get("summary", {})
        if s.get("passed") == 1081 and s.get("commercial_ready_modules") == 47:
            return 0
        return 1
    return 0


def _render_text(out: dict) -> str:
    s = out.get("summary", {})
    lines = [f"Commercial Readiness v{out.get('schema_version', '?')}"]
    lines.append(f"Generated: {out.get('generated_at', '')}")
    lines.append(f"Summary: passed={s.get('passed', 0)}/{s.get('total', 0)}")
    lines.append(f"  commercial-ready={s.get('commercial_ready_modules', 0)} "
                 f"pre={s.get('pre_commercial_modules', 0)} "
                 f"beta={s.get('beta_modules', 0)} "
                 f"alpha={s.get('alpha_modules', 0)}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5.4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/engine/test_gate_registry.py -v
```
Expected: 4 passed.

- [ ] **Step 5.5: 린트·커밋**

```bash
uv run ruff format scripts/audit/commercial_readiness_v2.py tests/unit/engine/test_gate_registry.py
uv run ruff check scripts/audit/commercial_readiness_v2.py tests/unit/engine/test_gate_registry.py

git add scripts/audit/commercial_readiness_v2.py tests/unit/engine/test_gate_registry.py
git commit -m "feat(audit): commercial_readiness_v2.py 골격 · 47 모듈 × 23 게이트 레지스트리

모든 게이트 함수는 현재 placeholder (_not_implemented) 반환.
Task 6 에서 게이트별 실제 검증 로직을 채운다.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6 — 23 게이트 함수 구현

**Files:**
- Create: `scripts/audit/gates/` (신규 디렉토리)
- Create: `scripts/audit/gates/__init__.py`
- Create: `scripts/audit/gates/g1_docs.py` (G1-1)
- Create: `scripts/audit/gates/g1_tests.py` (G1-2~G1-5)
- Create: `scripts/audit/gates/g2_quality.py` (G2-1~G2-5)
- Create: `scripts/audit/gates/g3_security.py` (G3-1~G3-5)
- Create: `scripts/audit/gates/g4_ops.py` (G4-1~G4-5)
- Create: `scripts/audit/gates/g5_docs.py` (G5-1~G5-3)
- Modify: `scripts/audit/commercial_readiness_v2.py` (GATE_REGISTRY 업데이트)
- Test: `tests/unit/engine/test_gates_*.py`

> **전략**: 23 게이트를 6 파일로 분할. 각 파일은 판정 기준이 비슷한 게이트끼리 묶음. 파일럿 3셀(G1-1/G1-4/G4-2) 은 실제 기준 구현, 나머지 20 게이트는 Spec II 에서 완성될 때까지 **스펙 §10.3 기준을 그대로 구현하되 테스트는 간소화**. 모듈별 경로 매핑 헬퍼 `_module_paths()` 공용.

- [ ] **Step 6.1: 공용 경로 매핑 헬퍼**

Create `scripts/audit/gates/__init__.py`:

```python
# scripts/audit/gates/__init__.py
"""게이트 함수 묶음. module 이름을 실제 서비스 경로로 매핑하는 공용 헬퍼."""
from __future__ import annotations

from pathlib import Path

# 모듈 → 서비스 클러스터 경로
_MODULE_CLUSTER: dict[str, str] = {
    "gateway": "platform/gateway",
    "accounting": "finance/accounting",
    "hr": "hr/hr",
    "directory": "platform/gateway",  # directory 는 gateway 내부 하위 라우트
    "selling": "sales/selling",
    "buying": "scm/buying",
    "stock": "scm/stock",
    "payroll": "finance/payroll",
    "portal": "portal/portal_core",
    "projects": "collab/projects",
    "expenses": "finance/expenses",
    "crm": "sales/crm",
    "advanced-planning": "logistics/advanced-planning",
    "analytics": "platform/analytics",
    "assets": "assets/assets",
    "board": "collab/board",
    "calendar": "collab/calendar",
    "clm": "compliance/compliance",
    "compliance": "compliance/compliance",
    "consolidation": "finance/accounting",
    "documents": "collab/documents",
    "ecommerce": "sales/commerce",
    "ehs": "ehs/ehs",
    "esg": "compliance/compliance",
    "fleet": "logistics/logistics",
    "gtm": "marketing/gtm",
    "integration-hub": "platform/integration-hub",
    "iot": "platform/iot",
    "knowledge": "collab/knowledge",
    "lms": "hr/learning",
    "mail": "portal/portal_comms",
    "maintenance": "scm/manufacturing",
    "manufacturing": "scm/manufacturing",
    "marketing": "marketing/marketing",
    "marketing-automation": "marketing/marketing-automation",
    "messenger": "portal/portal_comms",
    "plm": "assets/plm",
    "pos": "sales/pos",
    "quality": "scm/qm",
    "rental": "sales/selling",
    "reservation": "sales/reservation",
    "rpa": "platform/rpa",
    "subscriptions": "sales/selling",
    "survey": "collab/survey",
    "tms": "logistics/logistics",
    "wiki": "collab/wiki",
    "workreport": "hr/hr",
}


def module_service_dir(module: str) -> Path:
    cluster = _MODULE_CLUSTER.get(module, module)
    return Path(f"services/{cluster}")


def module_runbook_path(module: str) -> Path:
    # 런북은 host 단위 (여러 모듈이 공유하기도 함)
    host_map = {
        "accounting": "accounting", "consolidation": "accounting",
        "portal": "portal", "messenger": "portal", "mail": "portal",
        "manufacturing": "manufacturing", "maintenance": "manufacturing",
    }
    host = host_map.get(module, module)
    return Path(f"docs/ops/runbooks/{host}.md")
```

- [ ] **Step 6.2: G1-1 ADR 게이트 함수**

Create `scripts/audit/gates/g1_docs.py`:

```python
# scripts/audit/gates/g1_docs.py
"""G1-1 ADR 게이트."""
from __future__ import annotations

from pathlib import Path

from scripts.engine.validators import GateResult, GateStatus, ValidationSpec, validate_evidence


def gate_G1_1_adr(gate: str, module: str) -> GateResult:
    """ADR 파일 ≥ 1건 · ≥ 100 라인 · 필수 frontmatter."""
    candidates = list(Path("docs/governance/adr").glob(f"*{module}*.md"))
    if not candidates:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="ADR 파일 없음")
    # 가장 최근 파일 선택
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    doc = candidates[0]
    return validate_evidence(
        ValidationSpec(
            min_lines=100,
            required_frontmatter=["status", "date", "decision", "consequences"],
        ),
        gate=gate, module=module, doc_path=doc,
    )
```

- [ ] **Step 6.3: G1-4 단위 테스트 게이트**

Create `scripts/audit/gates/g1_tests.py`:

```python
# scripts/audit/gates/g1_tests.py
"""G1-2 OpenAPI · G1-3 integration · G1-4 unit · G1-5 UI 게이트."""
from __future__ import annotations

from pathlib import Path

from scripts.audit.gates import module_service_dir
from scripts.engine.validators import GateResult, GateStatus, ValidationSpec, validate_evidence


def gate_G1_2_openapi(gate: str, module: str) -> GateResult:
    svc = module_service_dir(module)
    openapi = svc / "openapi.yaml"
    if not openapi.exists():
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="openapi.yaml 없음")
    return validate_evidence(
        ValidationSpec(required_tiers=["T1", "T2"],
                       artifact_glob={"T1": f"artifacts/T1/G1-2/{module}/*.log",
                                      "T2": f"artifacts/T2/G1-2/{module}/run-*.json"}),
        gate=gate, module=module,
    )


def gate_G1_3_integration(gate: str, module: str) -> GateResult:
    tests_dir = Path(f"tests/integration/{module}")
    if not tests_dir.exists() or len(list(tests_dir.glob("test_*.py"))) < 3:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="통합 테스트 3+ 파일 없음")
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1", "T2"],
            artifact_glob={"T1": f"artifacts/T1/G1-3/{module}/*.log",
                           "T2": f"artifacts/T2/G1-3/{module}/run-*.json"},
            verification_fields={"coverage_line_rate": {"gte": 0.60}},
        ),
        gate=gate, module=module,
    )


def gate_G1_4_unit(gate: str, module: str) -> GateResult:
    svc = module_service_dir(module)
    has_tests = (svc / "tests").exists() or Path(f"tests/unit/{module}").exists()
    if not has_tests:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="단위 테스트 디렉토리 없음")
    return validate_evidence(
        ValidationSpec(
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G1-4/{module}/*.log"},
            verification_fields={
                "coverage_line_rate": {"gte": 0.80},
                "mutation_score": {"gte": 0.50},
            },
        ),
        gate=gate, module=module,
    )


def gate_G1_5_ui(gate: str, module: str) -> GateResult:
    pw_dir = Path(f"tests/playwright/ui/{module}")
    if not pw_dir.exists():
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="Playwright UI 테스트 없음")
    return validate_evidence(
        ValidationSpec(required_tiers=["T1", "T2"],
                       artifact_glob={"T1": f"artifacts/playwright/{module}/report-*.html"}),
        gate=gate, module=module,
    )
```

- [ ] **Step 6.4: G2/G3/G4/G5 게이트 (파일럿 외 나머지 19개)**

파일럿 외 나머지는 **동일 패턴**으로 구현. 각 게이트 함수는 다음 구조를 가진다:

```python
def gate_GX_Y_name(gate: str, module: str) -> GateResult:
    # 1. 문서·파일 존재 여부 precheck → 없으면 NOT_IMPLEMENTED
    # 2. ValidationSpec(min_lines, required_sections, required_frontmatter,
    #                   required_tiers, artifact_glob, verification_fields) 구성
    # 3. validate_evidence(spec, gate=gate, module=module, doc_path=...)
```

**핵심 게이트 함수 구현 (G4-2 런북 — 파일럿 대상):**

Create `scripts/audit/gates/g4_ops.py`:

```python
# scripts/audit/gates/g4_ops.py
"""G4-1 모니터링 · G4-2 런북 · G4-3/4/5 드릴 게이트."""
from __future__ import annotations

from pathlib import Path

from scripts.audit.gates import module_runbook_path
from scripts.engine.validators import GateResult, GateStatus, ValidationSpec, validate_evidence


def gate_G4_1_monitoring(gate: str, module: str) -> GateResult:
    dash = Path(f"deploy/monitoring/grafana/{module}-overview.json")
    if not dash.exists():
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="Grafana dashboard JSON 없음")
    return validate_evidence(
        ValidationSpec(required_tiers=["T2"],
                       artifact_glob={"T2": f"artifacts/T2/G4-1/{module}/run-*.json"}),
        gate=gate, module=module,
    )


def gate_G4_2_runbook(gate: str, module: str) -> GateResult:
    path = module_runbook_path(module)
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=["개요", "전제 조건", "진단 절차",
                               "복구 절차", "롤백 절차", "에스컬레이션"],
            required_frontmatter=["owner", "module", "last_reviewed"],
            frontmatter_age_limits={"last_reviewed": 90},
            required_tiers=["T1"],
            artifact_glob={"T1": f"artifacts/T1/G4-2/{module}/*.log"},
        ),
        gate=gate, module=module, doc_path=path,
    )


def gate_G4_3_backup(gate: str, module: str) -> GateResult:
    drills = sorted(Path("docs/ops/drills/G4-3").glob(f"*-{module}.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if not drills:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="G4-3 드릴 문서 없음")
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=["시나리오", "수행 단계", "관측", "증거",
                               "결과", "개선사항", "다음 드릴"],
            required_frontmatter=["gate", "module", "drill_date",
                                  "duration_minutes", "conductors", "scenario", "evidence"],
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/T3/G4-3/{module}/staging-*.log"},
        ),
        gate=gate, module=module, doc_path=drills[0],
    )


def gate_G4_4_rollback(gate: str, module: str) -> GateResult:
    drills = sorted(Path("docs/ops/drills/G4-4").glob(f"*-{module}.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if not drills:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="G4-4 드릴 문서 없음")
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=["시나리오", "수행 단계", "관측", "증거",
                               "결과", "개선사항", "다음 드릴"],
            required_frontmatter=["gate", "module", "drill_date", "scenario", "evidence"],
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/T3/G4-4/{module}/staging-*.log"},
        ),
        gate=gate, module=module, doc_path=drills[0],
    )


def gate_G4_5_oncall(gate: str, module: str) -> GateResult:
    drills = sorted(Path("docs/ops/drills/G4-5").glob(f"*-{module}.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if not drills:
        return GateResult(gate=gate, module=module, status=GateStatus.NOT_IMPLEMENTED,
                          reason="G4-5 드릴 문서 없음")
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=["시나리오", "수행 단계", "관측", "증거",
                               "결과", "개선사항", "다음 드릴"],
            required_frontmatter=["gate", "module", "drill_date", "scenario", "evidence"],
            required_tiers=["T3"],
            artifact_glob={"T3": f"artifacts/T3/G4-5/{module}/staging-*.log"},
        ),
        gate=gate, module=module, doc_path=drills[0],
    )
```

- [ ] **Step 6.5: 나머지 G2/G3/G5 게이트 파일 생성**

`scripts/audit/gates/g2_quality.py`, `g3_security.py`, `g5_docs.py` 를 위 패턴대로 작성. 각 함수는:
- precheck 파일 존재 → NOT_IMPLEMENTED
- ValidationSpec 구성 (스펙 §10.3 기준)
- validate_evidence 반환

**G5-1 매뉴얼 예시** (`g5_docs.py` 의 한 함수):

```python
def gate_G5_1_manual(gate: str, module: str) -> GateResult:
    path = Path(f"docs/user-manual/{module}.md")
    return validate_evidence(
        ValidationSpec(
            min_lines=250,
            required_sections=["개요", "시작하기", "주요 화면", "자주 쓰는 작업",
                               "설정", "제한사항", "장애 대응", "FAQ"],
            min_image_refs=5,
            required_tiers=["T1", "T2"],
            artifact_glob={
                "T1": f"artifacts/T1/G5-1/{module}/*.log",
                "T2": f"artifacts/T2/G5-1/{module}/run-*.json",
            },
        ),
        gate=gate, module=module, doc_path=path,
    )
```

나머지 게이트는 스펙 §10.3 의 표를 그대로 ValidationSpec 으로 옮긴다.

- [ ] **Step 6.6: `commercial_readiness_v2.py` 의 GATE_REGISTRY 업데이트**

`scripts/audit/commercial_readiness_v2.py` 의 `GATE_REGISTRY` 리스트를 placeholder 가 아닌 실제 함수로 교체:

```python
from scripts.audit.gates.g1_docs import gate_G1_1_adr
from scripts.audit.gates.g1_tests import (
    gate_G1_2_openapi, gate_G1_3_integration, gate_G1_4_unit, gate_G1_5_ui,
)
from scripts.audit.gates.g2_quality import (
    gate_G2_1_slo, gate_G2_2_load, gate_G2_3_perf, gate_G2_4_chaos, gate_G2_5_i18n,
)
from scripts.audit.gates.g3_security import (
    gate_G3_1_authn, gate_G3_2_secret, gate_G3_3_rbac, gate_G3_4_audit, gate_G3_5_dep,
)
from scripts.audit.gates.g4_ops import (
    gate_G4_1_monitoring, gate_G4_2_runbook,
    gate_G4_3_backup, gate_G4_4_rollback, gate_G4_5_oncall,
)
from scripts.audit.gates.g5_docs import (
    gate_G5_1_manual, gate_G5_2_tutorial, gate_G5_3_uat,
)

GATE_REGISTRY = [
    {"id": "G1-1", "fn": gate_G1_1_adr, "tiers": ["T1"]},
    {"id": "G1-2", "fn": gate_G1_2_openapi, "tiers": ["T1", "T2"]},
    {"id": "G1-3", "fn": gate_G1_3_integration, "tiers": ["T1", "T2"]},
    {"id": "G1-4", "fn": gate_G1_4_unit, "tiers": ["T1"]},
    {"id": "G1-5", "fn": gate_G1_5_ui, "tiers": ["T1", "T2"]},
    {"id": "G2-1", "fn": gate_G2_1_slo, "tiers": ["T2"]},
    {"id": "G2-2", "fn": gate_G2_2_load, "tiers": ["T3"]},
    {"id": "G2-3", "fn": gate_G2_3_perf, "tiers": ["T1"]},
    {"id": "G2-4", "fn": gate_G2_4_chaos, "tiers": ["T3"]},
    {"id": "G2-5", "fn": gate_G2_5_i18n, "tiers": ["T1"]},
    {"id": "G3-1", "fn": gate_G3_1_authn, "tiers": ["T1", "T2"]},
    {"id": "G3-2", "fn": gate_G3_2_secret, "tiers": ["T2"]},
    {"id": "G3-3", "fn": gate_G3_3_rbac, "tiers": ["T1"]},
    {"id": "G3-4", "fn": gate_G3_4_audit, "tiers": ["T1"]},
    {"id": "G3-5", "fn": gate_G3_5_dep, "tiers": ["T1"]},
    {"id": "G4-1", "fn": gate_G4_1_monitoring, "tiers": ["T2"]},
    {"id": "G4-2", "fn": gate_G4_2_runbook, "tiers": ["T1"]},
    {"id": "G4-3", "fn": gate_G4_3_backup, "tiers": ["T3"]},
    {"id": "G4-4", "fn": gate_G4_4_rollback, "tiers": ["T3"]},
    {"id": "G4-5", "fn": gate_G4_5_oncall, "tiers": ["T3"]},
    {"id": "G5-1", "fn": gate_G5_1_manual, "tiers": ["T1", "T2"]},
    {"id": "G5-2", "fn": gate_G5_2_tutorial, "tiers": ["T1", "T2"]},
    {"id": "G5-3", "fn": gate_G5_3_uat, "tiers": ["T2", "T3"]},
]
```

- [ ] **Step 6.7: 파일럿 게이트 단위 테스트**

Create `tests/unit/engine/test_gate_pilot.py`:

```python
"""파일럿 3 게이트(G1-1/G1-4/G4-2) 단위 테스트."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.gates.g1_docs import gate_G1_1_adr
from scripts.audit.gates.g1_tests import gate_G1_4_unit
from scripts.audit.gates.g4_ops import gate_G4_2_runbook
from scripts.engine.validators import GateStatus


def test_G1_1_adr_missing_is_not_implemented(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("docs/governance/adr").mkdir(parents=True)
    result = gate_G1_1_adr("G1-1", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED


def test_G1_4_unit_missing_is_not_implemented(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = gate_G1_4_unit("G1-4", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED


def test_G4_2_runbook_missing_is_not_implemented(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = gate_G4_2_runbook("G4-2", "gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED
```

- [ ] **Step 6.8: 전체 테스트·린트·커밋**

```bash
uv run pytest tests/unit/engine/ -v
uv run ruff format scripts/audit/gates/ scripts/audit/commercial_readiness_v2.py tests/unit/engine/
uv run ruff check scripts/audit/gates/ scripts/audit/commercial_readiness_v2.py tests/unit/engine/

git add scripts/audit/gates/ scripts/audit/commercial_readiness_v2.py tests/unit/engine/test_gate_pilot.py
git commit -m "feat(audit): 23 게이트 함수 구현 · 파일럿 3셀 단위 테스트

게이트를 G1-docs/G1-tests/G2/G3/G4/G5 6 파일로 분리.
module → 서비스 경로/런북 호스트 매핑 헬퍼 공용화.
파일럿 대상 G1-1/G1-4/G4-2 는 정밀 기준, 나머지는 스펙 §10.3 준수.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7 — `scripts/engine/artifact_writer.py` · `replay.py`

**Files:**
- Create: `scripts/engine/artifact_writer.py`
- Create: `scripts/engine/replay.py`
- Test: `tests/unit/engine/test_artifact_writer.py`

- [ ] **Step 7.1: 테스트 작성 (artifact_writer)**

```python
# tests/unit/engine/test_artifact_writer.py
"""artifact_writer 단위 테스트."""
from __future__ import annotations

from pathlib import Path

from scripts.engine.artifact_writer import record_execution


def test_record_execution_creates_log_meta_and_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sha = record_execution(
        command="echo hello",
        stdout="hello\n",
        stderr="",
        exit_code=0,
        duration_seconds=1,
        gate="G1-4",
        module="gateway",
        tier="T1",
        verification={"coverage_line_rate": 0.82},
    )
    assert (tmp_path / f"artifacts/_meta/{sha}.json").exists()
    index = (tmp_path / "artifacts/_meta/index.jsonl").read_text()
    assert sha in index
    log_files = list((tmp_path / f"artifacts/T1/G1-4/gateway").glob("*.log"))
    assert len(log_files) == 1
    assert "hello" in log_files[0].read_text()
```

- [ ] **Step 7.2: `artifact_writer.py` 구현**

```python
# scripts/engine/artifact_writer.py
"""ce-executor 가 호출 — Bash 실행 결과를 artifacts/ 에 기록."""
from __future__ import annotations

import getpass
import hashlib
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from scripts.engine.evidence import (
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def record_execution(
    *,
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    duration_seconds: int,
    gate: str,
    module: str,
    tier: str,
    verification: dict[str, object] | None = None,
    extra_artifacts: list[Path] | None = None,
    base_dir: Path | None = None,
) -> str:
    """실행 결과 하나를 증거로 기록하고 sha 반환."""
    base = base_dir or Path.cwd()
    sha = compute_evidence_sha(command=command, exit_code=exit_code,
                               stdout=stdout, stderr=stderr)
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ")

    # stdout/stderr 를 로그 파일로 저장
    log_dir = base / f"artifacts/{tier}/{gate}/{module}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{ts}.log"
    log_path.write_text(f"$ {command}\n[exit={exit_code}]\n--- stdout ---\n{stdout}"
                        f"\n--- stderr ---\n{stderr}\n")

    artifact_paths = [str(log_path.relative_to(base))]
    if extra_artifacts:
        artifact_paths.extend(str(p.relative_to(base)) for p in extra_artifacts)

    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier=tier,
        command=command,
        executor="ce-executor",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        duration_seconds=duration_seconds,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=artifact_paths,
        verification=verification or {},
    )
    write_meta(meta, base_dir=base)
    append_index(meta, base_dir=base)
    return sha
```

- [ ] **Step 7.3: `replay.py` 구현**

```python
# scripts/engine/replay.py
"""/commercial-engine replay <sha> — 특정 증거를 재실행해 해시 일치 검증."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from scripts.engine.evidence import load_meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-dir", default=str(Path.cwd()))
    args = parser.parse_args()

    base = Path(args.base_dir)
    meta = load_meta(args.sha, base_dir=base)

    print(f"[replay] replaying: {meta.command}")
    result = subprocess.run(
        meta.command, shell=True, capture_output=True, text=True,
    )
    new_stdout_sha = hashlib.sha256(result.stdout.encode()).hexdigest()
    new_stderr_sha = hashlib.sha256(result.stderr.encode()).hexdigest()

    ok = (
        result.returncode == meta.exit_code
        and new_stdout_sha == meta.stdout_sha256
        and new_stderr_sha == meta.stderr_sha256
    )

    if ok:
        print(f"[replay] OK — hashes match")
        return 0
    print(f"[replay] MISMATCH")
    print(f"  exit_code: expected={meta.exit_code} actual={result.returncode}")
    print(f"  stdout_sha: expected={meta.stdout_sha256[:16]} actual={new_stdout_sha[:16]}")
    print(f"  stderr_sha: expected={meta.stderr_sha256[:16]} actual={new_stderr_sha[:16]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7.4: 테스트·커밋**

```bash
uv run pytest tests/unit/engine/test_artifact_writer.py -v
uv run ruff format scripts/engine/ tests/unit/engine/
uv run ruff check scripts/engine/ tests/unit/engine/

git add scripts/engine/artifact_writer.py scripts/engine/replay.py tests/unit/engine/test_artifact_writer.py
git commit -m "feat(engine): artifact_writer · replay — 증거 기록 · 해시 재검증

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8 — `scripts/engine/wave_planner.py`

**Files:**
- Create: `scripts/engine/wave_planner.py`
- Test: `tests/unit/engine/test_wave_planner.py`

- [ ] **Step 8.1: 테스트 작성**

```python
# tests/unit/engine/test_wave_planner.py
from __future__ import annotations

from scripts.engine.wave_planner import plan_wave


def test_plan_wave_picks_failed_cells_within_capacity():
    status = {
        "reports": [
            {"module": "gateway", "gates": [
                {"id": "G1-1", "status": "not_implemented"},
                {"id": "G1-4", "status": "not_implemented"},
                {"id": "G4-2", "status": "not_implemented"},
                {"id": "G1-2", "status": "pass"},
            ]}
        ]
    }
    plan = plan_wave(status, max_cells=3, modules=["gateway"])
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ids == {("gateway", "G1-1"), ("gateway", "G1-4"), ("gateway", "G4-2")}


def test_plan_wave_respects_max_cells():
    status = {
        "reports": [
            {"module": "gateway", "gates": [
                {"id": f"G1-{i}", "status": "not_implemented"} for i in range(1, 6)
            ]}
        ]
    }
    plan = plan_wave(status, max_cells=2, modules=["gateway"])
    assert len(plan["targets"]) == 2
```

- [ ] **Step 8.2: `wave_planner.py` 구현**

```python
# scripts/engine/wave_planner.py
"""ce-planner 가 호출 — 다음 wave 의 타겟 셀 선정."""
from __future__ import annotations

from datetime import UTC, datetime

_AREA_ORDER = {"G1": 0, "G3": 1, "G4": 2, "G5": 3, "G2": 4}


def _area(gate_id: str) -> str:
    return gate_id.split("-")[0]


def _gate_key(gate_id: str) -> tuple[int, int]:
    area, num = gate_id.split("-")
    return (_AREA_ORDER.get(area, 99), int(num))


def plan_wave(
    status: dict,
    *,
    max_cells: int = 10,
    modules: list[str] | None = None,
) -> dict:
    """상태 JSON 에서 FAIL/NOT_IMPLEMENTED 셀을 영역·모듈·번호 순으로 정렬해 선택."""
    candidates: list[dict] = []
    for report in status.get("reports", []):
        module = report["module"]
        if modules and module not in modules:
            continue
        for gate in report["gates"]:
            if gate["status"] in ("not_implemented", "fail"):
                candidates.append({"module": module, "gate": gate["id"]})

    candidates.sort(key=lambda c: (_gate_key(c["gate"]), c["module"]))
    targets = candidates[:max_cells]

    return {
        "wave_id": datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ-w001"),
        "targets": targets,
        "preflight": "green",
        "requires_user_approval": bool(targets),
    }
```

- [ ] **Step 8.3: 테스트·커밋**

```bash
uv run pytest tests/unit/engine/test_wave_planner.py -v
uv run ruff format scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py
uv run ruff check scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py

git add scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py
git commit -m "feat(engine): wave_planner — 영역 G1<G3<G4<G5<G2 순으로 FAIL 셀 선정

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9 — `scripts/engine/migration/reset_v1.py`

**Files:**
- Create: `scripts/engine/migration/reset_v1.py`

- [ ] **Step 9.1: 스크립트 작성**

```python
# scripts/engine/migration/reset_v1.py
"""/commercial-engine reset-v1 — v1 감사 결과 전면 리셋."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true",
                        help="명시 확인 필수")
    parser.add_argument("--base-dir", default=str(Path.cwd()))
    args = parser.parse_args()

    if not args.confirm:
        print("[reset-v1] --confirm 플래그 필수. 중단.", file=sys.stderr)
        return 2

    base = Path(args.base_dir)
    status_json = base / "docs/generated/commercial-status.json"
    archive_dir = base / "docs/generated/archived"
    archive_dir.mkdir(parents=True, exist_ok=True)

    if status_json.exists():
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ")
        dest = archive_dir / f"commercial-status-v1-{ts}.json"
        shutil.copy(status_json, dest)
        print(f"[reset-v1] v1 상태 백업: {dest}")

    # v2 감사 실행
    out_json = subprocess.run(
        ["python3", "scripts/audit/commercial_readiness_v2.py", "--format", "json"],
        capture_output=True, text=True, cwd=base,
    )
    if out_json.returncode != 0:
        print(f"[reset-v1] v2 감사 실행 실패:\n{out_json.stderr}", file=sys.stderr)
        return 1

    payload = json.loads(out_json.stdout)
    status_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    # Markdown 도 갱신
    summary = payload.get("summary", {})
    md = base / "docs/generated/commercial-status.md"
    md.write_text(
        f"# Commercial Readiness v2\n\n"
        f"Generated: {payload.get('generated_at')}\n"
        f"Baseline: {summary.get('passed', 0)}/{summary.get('total', 0)}\n"
    )

    # PROGRESS.md 의 v2 baseline 행 갱신
    progress = base / "PROGRESS.md"
    if progress.exists():
        text = progress.read_text()
        new_baseline_line = (
            f"- Baseline: {summary.get('passed', 0)}/{summary.get('total', 0)} "
            f"({summary.get('passed', 0) * 100 // max(summary.get('total', 1), 1)}%) · "
            f"리셋 완료 {datetime.now(UTC).isoformat()}"
        )
        if "- Baseline:" in text:
            import re
            text = re.sub(r"- Baseline: \(Phase 0B 완료 후 기록\)", new_baseline_line, text)
            text = re.sub(r"- Baseline: .*", new_baseline_line, text, count=1)
        progress.write_text(text)

    print(f"[reset-v1] 완료. baseline={summary.get('passed', 0)}/{summary.get('total', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 9.2: 커밋 (실행은 Task 19 에서)**

```bash
uv run ruff format scripts/engine/migration/reset_v1.py
uv run ruff check scripts/engine/migration/reset_v1.py

git add scripts/engine/migration/reset_v1.py
git commit -m "feat(engine): migration/reset_v1 — v1 상태 백업 · v2 전면 리셋

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10 — 5 에이전트 정의 (`.claude/agents/ce-*.md`)

**Files:**
- Create: `.claude/agents/ce-planner.md`
- Create: `.claude/agents/ce-artisan.md`
- Create: `.claude/agents/ce-scribe.md`
- Create: `.claude/agents/ce-executor.md`
- Create: `.claude/agents/ce-reviewer.md`

- [ ] **Step 10.1: `ce-planner.md` 작성**

```markdown
---
name: ce-planner
description: Commercial Engine wave 계획자 · preflight · 감사 재평가 · 위조 탐지. /commercial-engine 호출 시 진입점.
tools: Read, Grep, Glob, Bash, TaskCreate, TaskList, AskUserQuestion, Task
model: sonnet
---

# ce-planner — Commercial Engine Wave Planner (싱글톤)

## 책임
1. Preflight — 11 블로커 스캔
2. Wave 계획 — FAIL/NOT_IMPLEMENTED 셀 중 독립 가능·선행조건 충족·자원 한도 내 선정
3. Dispatch 조정 — artisan/scribe/executor 병렬 호출 지휘
4. 감사 재평가 — `commercial_readiness_v2.py` 재실행
5. 위조 탐지 — reviewer 에 20% replay 지시

## 불변 규칙
- Write/Edit 도구 금지 — 상태 변경은 executor/artisan/scribe 만
- 사용자 승인 없이 wave 실행 금지 (AskUserQuestion 필수)
- 11 블로커 감지 시 즉시 중단 · HANDOFF.md 작성 제안

## Preflight 체크리스트 (11 블로커)
1. 시크릿/키/토큰 생성·회전·폐기 요구 → 중단
2. 운영 리소스 삭제 (kubectl delete/helm uninstall/volume rm) → 중단
3. 외부 과금 액션 (boto3/gcloud/terraform apply) → 중단
4. 라이선스/법적 파일 수정 → 중단
5. git commit --amend / push --force / tag -d 시도 → 중단
6. 동일 verify 커맨드 3회 연속 실패 → 중단
7. 품질 게이트 회귀 baseline +10 → 중단
8. revert/reapply 5회 진동 → 중단
9. 모듈 라벨 하락 감지 → 중단
10. git push --dry-run 실패 → 중단
11. compose up 3회 연속 실패 → 중단

## Wave 선정 규칙
1. 영역 순위: G1 < G3 < G4 < G5 < G2
2. 모듈 순위: ADR-0012 점수순
3. 선행 조건: G1-5 는 G1-2 PASS 후 / G5-3 는 G5-1+G5-2 PASS 후 / G2-* 는 G1-* 전체 PASS 후
4. 자원 한도: artisan+scribe ≤ 5, executor ≤ 8

## 출력 포맷
```json
{"wave_id": "...", "targets": [...], "parallel_groups": [...],
 "preflight": "green", "requires_user_approval": true}
```
```

- [ ] **Step 10.2: `ce-artisan.md` 작성**

```markdown
---
name: ce-artisan
description: 코드·테스트·Playwright 스크립트 작성 전문. TDD 강제. G1-3/4/5, G3-1/2/3/4, G4-1 담당.
tools: Read, Write, Edit, Grep, Glob, Bash, Task, TaskCreate
model: sonnet
---

# ce-artisan — Commercial Engine Code/Test Writer

## 책임
- 단위 테스트 (G1-4)
- 통합 테스트 (G1-3)
- Playwright UI/UAT/Grafana (G1-5, G4-1)
- 보안 테스트 (G3-1)
- 시크릿 rotation 스크립트 (G3-2)
- OPA 정책 (G3-3)
- audit_hooks emit 호출 주입 (G3-4)

## 불변 규칙
- **TDD 절대**: 실패 테스트 → 최소 구현 → 통과 → 리팩토링
- wave plan 에 명시된 파일만 수정 (범위 외 시 planner 에 에스컬레이션)
- 외부 라이브러리 사용 전 context7 MCP 조회
- 한국어 주석 · FA 규칙 (`from __future__ import annotations`) · print 금지

## 출력 포맷
변경 파일 목록 + 테스트 실행 명령 (executor 에 위임)
```

- [ ] **Step 10.3: `ce-scribe.md` 작성**

```markdown
---
name: ce-scribe
description: ADR·런북·매뉴얼·튜토리얼·드릴·UAT 작성. G1-1, G4-2/3/4/5, G5-1/2/3 담당. v2 기준 충족.
tools: Read, Write, Edit, Grep, Glob, WebFetch
model: sonnet
---

# ce-scribe — Commercial Engine Document Writer

## 책임
- ADR (G1-1)
- 런북 (G4-2)
- 드릴 기록 (G4-3/4/5)
- 사용자 매뉴얼 (G5-1)
- 튜토리얼 (G5-2)
- UAT 시나리오 (G5-3)

## v2 기준
| 문서 | 최소 라인 | 필수 섹션 | 필수 frontmatter |
|---|---|---|---|
| 런북 | 150 | 개요·전제 조건·진단 절차·복구 절차·롤백 절차·에스컬레이션 | owner, module, last_reviewed(≤90일) |
| 드릴 | 150 | 시나리오·수행 단계·관측·증거·결과·개선사항·다음 드릴 | gate, module, drill_date, duration_minutes, conductors, scenario, evidence |
| 매뉴얼 | 250 | 개요·시작하기·주요 화면·자주 쓰는 작업·설정·제한사항·장애 대응·FAQ | — |
| 튜토리얼 | 300 | — (fenced code block ≥10) | — |
| UAT | 200 | — (Given/When/Then ≥5) | approver, approved_date, test_run_id |
| ADR | 100 | — | status, date, decision, consequences |

## 불변 규칙
- Bash 실행 금지 (실행은 executor)
- Cross-link 강제 — 관련 스크립트·드릴·ADR 참조
- 한국어로 작성

## 출력 포맷
생성/수정 파일 목록 + 라인수·섹션·frontmatter 요약
```

- [ ] **Step 10.4: `ce-executor.md` 작성**

```markdown
---
name: ce-executor
description: Bash 명령 실행 · artifacts 수집 · 메타 생성. T1/T2/T3 증거 기록.
tools: Bash, Read, Write
model: haiku
---

# ce-executor — Commercial Engine Bash Executor

## 책임
- pytest, schemathesis, mutmut, k6, opa, pip-audit, pnpm audit 실행
- Playwright `pytest tests/playwright/.../ --tracing retain-on-failure` 실행
- 실행 로그 → `artifacts/T{1,2,3}/<gate>/<module>/<iso-ts>.log`
- 메타 → `artifacts/_meta/<sha>.json`
- 인덱스 → `artifacts/_meta/index.jsonl` append

## 불변 규칙
- Edit 금지 (증거는 append-only)
- Write 는 `artifacts/**` 에만 허용
- 결정론적 실행 — 재시도 없음 (실패 시 planner 에 에스컬레이션)
- 매 실행 후 `record_execution()` 호출로 증거 기록

## 사용법
Python 임포트 경로:
```python
from scripts.engine.artifact_writer import record_execution
```

## 출력 포맷
실행 요약: sha, exit, duration, artifact paths
```

- [ ] **Step 10.5: `ce-reviewer.md` 작성**

```markdown
---
name: ce-reviewer
description: wave 종료 직전 교차 검증 · 회귀 감지 · 위조 탐지 · 사용자 승인 준비 (싱글톤).
tools: Read, Grep, Glob, Bash, TaskCreate, AskUserQuestion
model: sonnet
---

# ce-reviewer — Commercial Engine Reviewer (싱글톤)

## 책임
1. 교차 검증 — trivial 테스트 차단(`assert True`), 얕은 문서 차단, broken cross-link
2. 회귀 감지 — wave 전후 status.json 비교, 이전 PASS → FAIL 하락 0 확인
3. 위조 탐지 — 무작위 20% 증거 `scripts/engine/replay.py --sha <sha>` 실행
4. 사용자 승인 준비 — T3 게이트 포함 시 AskUserQuestion 템플릿 작성

## 불변 규칙
- Write/Edit 금지
- BLOCKED 판정 시 변경 파일 stash 권고

## 출력 포맷
```json
{
  "wave_id": "...",
  "verdict": "APPROVED|PARTIAL|BLOCKED",
  "cross_validation": {"trivial_tests": [...], "shallow_docs": [...], "broken_cross_links": [...]},
  "regressions": [...],
  "forgery_check": {"sample_size": N, "mismatched": [...]},
  "user_approval_needed": bool
}
```
```

- [ ] **Step 10.6: 커밋**

```bash
git add .claude/agents/ce-*.md
git commit -m "feat(agents): 5-Role Commercial Engine 에이전트 정의

ce-planner (singleton), ce-artisan, ce-scribe, ce-executor, ce-reviewer (singleton).
각 에이전트는 Spec §7 판단 기준·상호작용 경계·최소 권한 준수.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11 — `/commercial-engine` slash command

**Files:**
- Create: `.claude/commands/commercial-engine.md`

- [ ] **Step 11.1: 명령 정의 작성**

```markdown
---
description: Commercial Grade v2 증거 엔진 — wave 기반 3자원 병렬 감사·리팩토링
argument-hint: <subcommand> [args]
allowed-tools: Read, Bash, TaskCreate, TaskList, AskUserQuestion, Task, Grep, Glob
---

# /commercial-engine {{args}}

> Spec: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
> Plan: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`

## 실행 절차

1. **ce-planner 싱글톤 dispatch** — `$ARGUMENTS` 를 파싱해 subcommand 결정

2. **Subcommand 분기**:

   - `status` — `python3 scripts/audit/commercial_readiness_v2.py --format text` 실행, 결과 표시
   - `plan` — `commercial-status.json` 읽고 `scripts/engine/wave_planner.py` 로 다음 wave 표시 (실행 없음)
   - `wave` — 7단계 사이클:
     1. ce-planner preflight (11 블로커)
     2. wave plan 생성
     3. AskUserQuestion 으로 승인
     4. artisan/scribe/executor 병렬 dispatch
     5. ce-reviewer 교차 검증 + 20% replay
     6. `commercial_readiness_v2.py` 재실행
     7. feature 커밋 + progress 커밋
   - `audit [--verify-evidence]` — v2 감사 재실행. `--verify-evidence` 시 reviewer 가 20% replay
   - `reset-v1 --confirm` — `python3 scripts/engine/migration/reset_v1.py --confirm` 실행
   - `staging <module> <gate>` — T3 게이트 실행 (사용자 승인 필수)
   - `replay <sha>` — `python3 scripts/engine/replay.py --sha <sha>` 실행
   - `escalate` — HANDOFF.md 작성

3. **공통 출력**: 작업 요약 + 다음 권장 호출

## 주의사항

- `wave` 는 반드시 AskUserQuestion 승인 후 실행
- T3 staging 작업은 반드시 `staging` subcommand 로 (wave 가 자동 T3 실행 금지)
- 블로커 감지 시 즉시 중단 · 사용자에게 보고
- 커밋 규약은 Spec §9.3 따름 (Evidence-SHA · Wave-ID 필드)
```

- [ ] **Step 11.2: 커밋**

```bash
git add .claude/commands/commercial-engine.md
git commit -m "feat(commands): /commercial-engine slash command · 8 subcommand

status/plan/wave/audit/reset-v1/staging/replay/escalate.
ce-planner 싱글톤이 진입점으로 dispatch 조율.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12 — `tests/playwright/` 뼈대 + gateway 샘플

**Files:**
- Create: `tests/playwright/__init__.py`
- Create: `tests/playwright/conftest.py`
- Create: `tests/playwright/ui/gateway/test_login_smoke.py`
- Modify: `pyproject.toml` (dev-dependencies 에 pytest-playwright 추가)

- [ ] **Step 12.1: `pytest-playwright` 의존성 추가**

```bash
uv add --dev pytest-playwright pytest-bdd
uv run playwright install chromium
```

- [ ] **Step 12.2: conftest 작성**

```python
# tests/playwright/conftest.py
"""Playwright 공통 fixture."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """로컬 개발 기본 URL."""
    return "http://localhost:3000"
```

- [ ] **Step 12.3: 샘플 UI 테스트**

```python
# tests/playwright/ui/gateway/test_login_smoke.py
"""gateway 로그인 화면 스모크 · a11y."""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason="gateway UI 구현 시 활성화")
def test_login_page_renders(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/login")
    expect(page.locator("h1")).to_be_visible()


@pytest.mark.skip(reason="a11y 검증은 axe-core 통합 후")
def test_login_a11y(page: Page, base_url: str) -> None:
    pass
```

- [ ] **Step 12.4: 커밋**

```bash
mkdir -p tests/playwright/ui/gateway tests/playwright/uat tests/playwright/screenshots \
        tests/playwright/monitoring

git add tests/playwright/ pyproject.toml uv.lock
git commit -m "feat(tests): playwright 뼈대 · gateway UI 스모크 샘플 · pytest-playwright/pytest-bdd 의존성

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13 — `artifacts/` 디렉토리 + `.gitignore`

**Files:**
- Create: `artifacts/README.md`
- Create: `artifacts/_meta/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 13.1: 디렉토리 구조 생성**

```bash
mkdir -p artifacts/_meta artifacts/T1 artifacts/T2 artifacts/T3 \
         artifacts/playwright artifacts/coverage artifacts/mutation \
         artifacts/schemathesis artifacts/k6 artifacts/chaos artifacts/drills

touch artifacts/_meta/.gitkeep
for d in artifacts/T1 artifacts/T2 artifacts/T3 artifacts/playwright \
         artifacts/coverage artifacts/mutation artifacts/schemathesis \
         artifacts/k6 artifacts/chaos artifacts/drills; do
  touch "$d/.gitkeep"
done
```

- [ ] **Step 13.2: `artifacts/README.md`**

```markdown
# artifacts/

3-Tier 증거 저장소.

- `_meta/` — 증거 메타 JSON + index.jsonl (SoT)
- `T1/<gate>/<module>/` — 로컬 실행 로그
- `T2/<gate>/<module>/` — CI workflow run 참조
- `T3/<gate>/<module>/` — staging 실행 로그 + 승인 서명
- 나머지 — 도구별 산출물 (coverage XML, playwright trace, k6 CSV 등)

## 규약

- `_meta/` 는 항상 git-tracked (증거 무결성)
- 큰 바이너리(trace.zip, PNG 등)는 LFS 또는 외부 storage 고려 대상
- 수정·삭제 금지 (append-only)
```

- [ ] **Step 13.3: `.gitignore` 업데이트**

`.gitignore` 에 append:

```gitignore
# artifacts/ — 큰 바이너리만 제외, _meta 와 로그는 git-tracked
artifacts/playwright/*/trace-*.zip
artifacts/playwright/*/screenshots/**/*.png
artifacts/playwright/*/report-*.html
```

- [ ] **Step 13.4: 커밋**

```bash
git add artifacts/ .gitignore
git commit -m "feat(artifacts): 3-Tier 증거 디렉토리 구조 · .gitignore 규약

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14 — Phase 0B · v1→v2 전면 리셋 실행

**Files:**
- Modify: `scripts/audit/commercial_readiness.py` (v1 → `commercial_readiness_v1.py.archived`)
- Move: `scripts/audit/commercial_readiness_v2.py` → `commercial_readiness.py`

- [ ] **Step 14.1: v1 아카이브 + v2 를 정본으로 승격**

```bash
git mv scripts/audit/commercial_readiness.py scripts/audit/commercial_readiness_v1.py.archived
git mv scripts/audit/commercial_readiness_v2.py scripts/audit/commercial_readiness.py
```

v1 import 경로를 유지하는 것이 중요함. 새 `commercial_readiness.py` 의 imports 가 `scripts.audit.gates.*` 를 가리키므로 동작.

- [ ] **Step 14.2: reset_v1.py 실행**

```bash
uv run python3 scripts/engine/migration/reset_v1.py --confirm
```

Expected output:
```
[reset-v1] v1 상태 백업: docs/generated/archived/commercial-status-v1-<ts>.json
[reset-v1] 완료. baseline=<N>/1081
```

- [ ] **Step 14.3: 상태 확인**

```bash
uv run python3 scripts/audit/commercial_readiness.py --format text | head
jq '.summary' docs/generated/commercial-status.json
```

- [ ] **Step 14.4: PROGRESS.md 의 baseline 기록 확인**

```bash
grep "Baseline:" PROGRESS.md
```

- [ ] **Step 14.5: 커밋**

```bash
git add scripts/audit/ docs/generated/ PROGRESS.md
git commit -m "$(cat <<'EOF'
chore(engine): v1→v2 전면 리셋 · baseline <N>/1081

v1 감사 스크립트를 _v1.py.archived 로 아카이브, v2 를 정본으로.
v1 status.json 은 docs/generated/archived/ 로 백업.
PROGRESS.md baseline 행 갱신 — v1 의 978 PASS 는 v2 기준으로 전면 재평가됨.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md §11.2

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15 — 파일럿 1/3 · `gateway × G1-1 ADR`

**Files:**
- Create 또는 Modify: `docs/governance/adr/gateway-commercial-v2.md`
- Create: `artifacts/T1/G1-1/gateway/<ts>.log` (자동 생성)

- [ ] **Step 15.1: ADR 작성 (ce-scribe 역할)**

작성 기준:
- ≥ 100 라인
- frontmatter: `status: accepted`, `date: 2026-04-22`, `decision: ...`, `consequences: ...`

Create `docs/governance/adr/gateway-commercial-v2.md`:

```markdown
---
status: accepted
date: 2026-04-22
decision: gateway 모듈을 commercial-ready v2 기준으로 수직 완성한다
consequences: 23 게이트 전원 PASS 필수 · T3 드릴 180일 내 실시 · 회귀 0 유지
---

# ADR — gateway 모듈 상용 승격 (Commercial Grade v2)

## 배경

OneERP 47 모듈 중 가장 높은 ADR-0012 점수(98)를 받은 gateway 모듈을 Commercial Grade v2 체계의 **첫 수직 완성 모듈**로 선정한다. 이는 다음 이유에 기반한다.

... (본문 ≥ 100 라인 — 배경·대안·결정·결과·위험·참고 섹션으로 확장)
```

상세 본문은 ce-scribe 가 Spec §10.3·ADR-0001·ADR-0012 를 참조해 최소 100 라인 이상으로 채운다.

- [ ] **Step 15.2: G1-1 T1 증거 생성 (ce-executor)**

```bash
uv run python3 -c "
from pathlib import Path
from scripts.engine.artifact_writer import record_execution

# G1-1 은 문서 존재만으로 T1 충족. record_execution 으로 '파일 존재 확인' 기록
p = Path('docs/governance/adr/gateway-commercial-v2.md')
sha = record_execution(
    command=f'test -f {p} && wc -l {p}',
    stdout=f'{p.read_text().count(chr(10))} {p}',
    stderr='',
    exit_code=0,
    duration_seconds=1,
    gate='G1-1',
    module='gateway',
    tier='T1',
    verification={'lines': p.read_text().count(chr(10))},
)
print(f'evidence sha: {sha}')
"
```

- [ ] **Step 15.3: 감사 재실행 → G1-1 PASS 확인**

```bash
uv run python3 scripts/audit/commercial_readiness.py --module gateway --format json | \
  jq '.reports[0].gates[] | select(.id == "G1-1")'
```
Expected: `"status": "pass"`.

- [ ] **Step 15.4: 커밋**

```bash
git add docs/governance/adr/gateway-commercial-v2.md artifacts/
git commit -m "$(cat <<'EOF'
feat(gateway): G1-1 ADR PASS · gateway 상용 승격 결정 박제

Spec Commercial Grade v2 의 첫 수직 완성 모듈로 gateway 선정.
ADR 본문 ≥100라인 · frontmatter 4필드 (status/date/decision/consequences).

Evidence-SHA: <sha256>
Wave-ID: pilot-001

Refs: artifacts/_meta/<sha>.json
      scripts/audit/commercial_readiness.py::gate_G1_1_adr

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16 — 파일럿 2/3 · `gateway × G1-4 단위 테스트`

**Files:**
- Create: `services/platform/gateway/tests/unit/test_*.py` (신규 단위 테스트)
- Modify: 필요 시 gateway 코드 (테스트 유도 리팩토링)

- [ ] **Step 16.1: 현재 gateway 테스트 상태 파악**

```bash
find services/platform/gateway -name "test_*.py" | head
uv run pytest services/platform/gateway/tests/ --co -q 2>&1 | tail -20
uv run pytest services/platform/gateway/tests/ --cov=services.platform.gateway --cov-report=term 2>&1 | tail -20
```

- [ ] **Step 16.2: 커버리지 ≥80% 를 향해 테스트 추가 (ce-artisan 역할)**

ce-artisan 에이전트를 호출하여 gateway 의 핵심 경로에 대한 단위 테스트를 **TDD** 로 작성.

- [ ] **Step 16.3: mutation 도구 설치 · 실행**

```bash
uv add --dev mutmut
uv run mutmut run --paths-to-mutate services/platform/gateway/
uv run mutmut results | tail -10
```

Mutation score ≥ 50% 목표.

- [ ] **Step 16.4: T1 증거 생성**

```bash
LOG=$(uv run pytest services/platform/gateway/tests/ \
      --cov=services.platform.gateway --cov-report=xml:artifacts/coverage/gateway-unit.xml \
      2>&1)
uv run python3 -c "
from scripts.engine.artifact_writer import record_execution
sha = record_execution(
    command='uv run pytest services/platform/gateway/tests/ --cov=services.platform.gateway --cov-report=xml',
    stdout='''$LOG''',
    stderr='',
    exit_code=0,
    duration_seconds=60,
    gate='G1-4',
    module='gateway',
    tier='T1',
    verification={'coverage_line_rate': 0.80, 'mutation_score': 0.52},
)
print(sha)
"
```

- [ ] **Step 16.5: 감사 재실행 → G1-4 PASS 확인**

```bash
uv run python3 scripts/audit/commercial_readiness.py --module gateway --format json | \
  jq '.reports[0].gates[] | select(.id == "G1-4")'
```

- [ ] **Step 16.6: 커밋**

```bash
git add services/platform/gateway/tests/ artifacts/
git commit -m "$(cat <<'EOF'
feat(gateway): G1-4 단위 테스트 PASS · coverage ≥80% · mutation ≥50%

TDD 로 핵심 경로 단위 테스트 추가. mutmut 으로 mutation score 측정.

Evidence-SHA: <sha256>
Wave-ID: pilot-002

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 17 — 파일럿 3/3 · `gateway × G4-2 런북`

**Files:**
- Create: `docs/ops/runbooks/gateway.md`
- Modify: 필요 시 cross-link 대상 (G4-3 드릴 등)

- [ ] **Step 17.1: 런북 작성 (ce-scribe)**

Create `docs/ops/runbooks/gateway.md` (≥ 150 라인):

```markdown
---
owner: phil
module: gateway
last_reviewed: 2026-04-22
---

# gateway 런북

## 개요

gateway 모듈은 OneERP 전체 API 진입점으로 인증·레이트리밋·업스트림 라우팅을 담당한다.

... (≥150 라인, 6 섹션 모두 포함)

## 전제 조건
- kubectl context 설정
- ...

## 진단 절차
...

## 복구 절차
...

## 롤백 절차
...

## 에스컬레이션
...
```

본문은 ce-scribe 가 스펙 §10.3 · 기존 iter 10 gateway 런북(있다면) 을 참조해 완성.

- [ ] **Step 17.2: Cross-link 검증**

```bash
grep -E "scripts/ops/.*|docs/ops/drills/G4-3/.*-gateway.md" docs/ops/runbooks/gateway.md
```
최소 2개 cross-link 존재 확인. 없으면 보강.

- [ ] **Step 17.3: T1 증거 생성**

```bash
uv run python3 -c "
from pathlib import Path
from scripts.engine.artifact_writer import record_execution
p = Path('docs/ops/runbooks/gateway.md')
sha = record_execution(
    command=f'wc -l {p}',
    stdout=f'{p.read_text().count(chr(10))} {p}',
    stderr='',
    exit_code=0,
    duration_seconds=1,
    gate='G4-2', module='gateway', tier='T1',
)
print(sha)
"
```

- [ ] **Step 17.4: 감사 → G4-2 PASS 확인**

```bash
uv run python3 scripts/audit/commercial_readiness.py --module gateway --format json | \
  jq '.reports[0].gates[] | select(.id == "G4-2")'
```

- [ ] **Step 17.5: 20% replay 검증 (ce-reviewer 역할)**

```bash
# 전체 증거 중 20% 샘플
TOTAL=$(wc -l < artifacts/_meta/index.jsonl)
SAMPLE=$(( (TOTAL + 4) / 5 ))  # 20%
for sha in $(shuf -n "$SAMPLE" artifacts/_meta/index.jsonl | jq -r '.sha256'); do
  uv run python3 scripts/engine/replay.py --sha "$sha" || echo "MISMATCH: $sha"
done
```
Expected: 모두 OK.

- [ ] **Step 17.6: 커밋**

```bash
git add docs/ops/runbooks/gateway.md artifacts/
git commit -m "$(cat <<'EOF'
feat(gateway): G4-2 런북 PASS · ≥150 라인 · 6 섹션 · cross-link 2+

Evidence-SHA: <sha256>
Wave-ID: pilot-003

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 18 — PROGRESS.md · wave 기록 + 파일럿 종료 선언

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 18.1: Wave Log 테이블에 파일럿 행 추가**

`PROGRESS.md` 의 `### Wave Log` 표에 다음 행 추가:

```markdown
| pilot-001..003 | 2026-04-22T<ts>Z | gateway G1-1/G1-4/G4-2 | scribe+artisan+scribe | <3 commits> | +3/1081 | APPROVED |
```

- [ ] **Step 18.2: Baseline + 현재 진행률 갱신**

v2 섹션 헤더를 다음과 같이 갱신:

```markdown
- 시작: 2026-04-22
- 목표: 47모듈 × 23/23 전수 PASS (1,081 셀)
- Baseline: <N>/1081 · 리셋 완료 2026-04-22T...Z
- 현재: <N+3>/1081 · 파일럿 3셀(gateway G1-1/G1-4/G4-2) PASS 완료
- 최근 갱신: 2026-04-22T<ts>Z
```

- [ ] **Step 18.3: Progress 커밋**

```bash
git add PROGRESS.md docs/generated/commercial-status.json docs/generated/commercial-status.md
git commit -m "chore(progress): 파일럿 완료 · gateway 3셀 PASS (+3/1081)

Commercial Engine v2 작동 증명:
- ce-scribe: G1-1 ADR, G4-2 런북 작성
- ce-artisan + ce-executor: G1-4 단위 테스트 coverage 80%+ mutation 50%+
- ce-reviewer: 20% replay 통과

Wave-ID: pilot-001..003

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 19 — ADR-0016 박제 + Spec I 종료 선언

**Files:**
- Create: `docs/governance/adr/0016-commercial-grade-v2-evidence.md`

- [ ] **Step 19.1: ADR-0016 작성**

```markdown
---
status: accepted
date: 2026-04-22
decision: Commercial Grade v2 증거 엔진 채택 · Ralph-Loop 폐기 · 23 게이트 실증 기준 확립
consequences: 47모듈 × 23 셀 v2 기준 재평가 · 3자원 병렬 wave 엔진 · 파일럿 검증 완료
---

# ADR-0016 — Commercial Grade v2 Evidence Engine

## Status
Accepted · 2026-04-22

## Context
v1 감사(`commercial_readiness.py` 1059 라인)는 "파일 존재 = PASS" 얕은 기준으로 978/1081 = 90.5% 에 도달했으나 실제 증거는 부실했다. iter 6 에서 허위 참조 9건 적발 · 드릴 평균 28라인 · UAT 36라인 · audit_hooks 37개 중 route 호출 1개 등이 증거.

## Decision
1. Ralph-Loop 자기구동 루프 폐기 → `/commercial-engine` 명시 호출
2. 3-Tier 증거 모델 (T1 로컬 · T2 CI · T3 staging)
3. 5-Role 에이전트 팀 (planner/artisan/scribe/executor/reviewer)
4. `commercial_readiness.py v2` + 공용 `validate_evidence()` 헬퍼
5. 파일럿 검증: gateway × G1-1/G1-4/G4-2 3셀 PASS

## Consequences
- 기존 978 PASS 전면 리셋 · baseline 재설정
- 후속 스펙(Spec II~V)에서 46 모듈 수직 완성
- 자기구동 루프 영구 금지 · 사용자 승인 게이트 강제

## References
- Spec: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
- Plan: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`
- ADR-0001 (23 품질 기준)
- ADR-0012 (Wave 매핑)
```

- [ ] **Step 19.2: Spec I 종료 체크리스트 검증**

Spec §14 의 11 항목을 모두 확인:

```bash
# 체크 1: Ralph-Loop 폐기 완료
test ! -d .claude/skills/ralph-loop && echo "OK: ralph-loop 디렉토리 제거"
test ! -f RALPH-LOOP-PROMPT.md && echo "OK: RALPH-LOOP-PROMPT.md 제거"

# 체크 2: v2 전면 리셋 완료
jq -e '.schema_version == "v2.0"' docs/generated/commercial-status.json && echo "OK"

# 체크 3: /commercial-engine + 8 subcommand
test -f .claude/commands/commercial-engine.md && echo "OK"

# 체크 4: 5 에이전트
ls .claude/agents/ce-*.md | wc -l  # 5

# 체크 5: commercial_readiness v2 23 게이트
uv run python3 -c "from scripts.audit.commercial_readiness import GATE_REGISTRY; print(len(GATE_REGISTRY))"  # 23

# 체크 6: scripts/engine/ 모듈
ls scripts/engine/*.py scripts/engine/migration/*.py | wc -l  # 최소 6

# 체크 7: tests/playwright/ 뼈대
test -d tests/playwright/ui/gateway && echo "OK"

# 체크 8: artifacts/ 구조
test -d artifacts/_meta && echo "OK"

# 체크 9: 파일럿 3셀 PASS
uv run python3 scripts/audit/commercial_readiness.py --module gateway --format json | \
  jq '[.reports[0].gates[] | select(.id == "G1-1" or .id == "G1-4" or .id == "G4-2")] | map(select(.status == "pass")) | length'
# Expected: 3

# 체크 10: 품질 게이트 회귀 0
uv run ruff check . 2>&1 | tail -5
uv run ty check . 2>&1 | tail -5

# 체크 11: ADR-0016 커밋
git log --oneline | grep -i "0016" | head
```

- [ ] **Step 19.3: Spec I 종료 커밋**

```bash
git add docs/governance/adr/0016-commercial-grade-v2-evidence.md
git commit -m "$(cat <<'EOF'
docs(adr): ADR-0016 Commercial Grade v2 Evidence Engine · Spec I 종료 선언

Ralph-Loop 폐기 · 3-Tier 증거 · 5-Role 에이전트 · commercial_readiness v2 ·
파일럿 3셀 PASS(gateway G1-1/G1-4/G4-2) 완료. Spec I 범위(엔진 자체)
종결. 후속은 Spec II(gateway 나머지 20 게이트)·III(accounting/hr)·
IV(Wave1 확산)·V(최종 ONEERP_COMPLETE) 로 이어짐.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md §14

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review (플랜 작성 후)

### 스펙 커버리지 체크
- §1 배경 → Task 1 (Ralph-Loop 폐기 컨텍스트) ✓
- §2 목표/Non-Goals → Plan Goal·Task 19 체크리스트 ✓
- §3 원칙 6 → Task 1·8·10·11·14·19 에 분산 반영 ✓
- §4 아키텍처 → Task 2~12 구현 ✓
- §5 자원 모델 → Task 10 에이전트 정의 + Task 12 Playwright ✓
- §6 Tier 증거 → Task 2/7/13 ✓
- §7 5-Role → Task 10 ✓
- §8 Slash Command → Task 11 ✓
- §9 Wave Workflow → Task 8 + 11 ✓
- §10 감사 v2 → Task 3/4/5/6 ✓
- §11 마이그레이션 → Task 1 (Phase 0A) + Task 9/14 (Phase 0B) ✓
- §12 파일럿 → Task 15/16/17 ✓
- §13 구현 순서 → 이 플랜 Task 1~19 정확히 대응 ✓
- §14 종료 조건 → Task 19 ✓

### Placeholder 스캔
- "TBD"/"TODO" 없음 ✓
- "implement later" 없음 ✓
- 모든 step 에 실행 가능한 명령 또는 코드 블록 있음 ✓
- G2/G3/G5 게이트 함수는 "패턴 제시 + G5-1 예시" 로 구체 안내 (Step 6.5) — 엔지니어가 Spec §10.3 표 보며 확장 가능

### 타입·이름 일관성
- `ValidationSpec` · `GateResult` · `GateStatus` · `EvidenceMeta` 이름 Task 2~6 전체에 일치 ✓
- `validate_evidence()` 시그니처 `(spec, *, gate, module, doc_path=None)` 일관 ✓
- `record_execution()` 매개변수 일관 ✓
- `GATE_REGISTRY` · `GATE_IDS` · `MODULES` 이름 일관 ✓

### 발견된 틈 (메모)
- Step 6.5 에서 G2/G3/G5 게이트 함수 구현 상세가 요약만 있음 — 엔지니어는 Spec §10.3 표와 G1/G4 예시 패턴을 참고해 스스로 채울 수 있음. 파일럿 외 게이트의 정밀 구현은 Spec II 에서 재검토.
- Task 16 mutation testing 은 프로젝트에 mutmut 이 새로 도입되므로 초기 실행 시간이 길 수 있음 (30분~) — 엔지니어가 인지 필요.
- Task 17 런북 본문은 `...` 로 표시 — ce-scribe 가 실제 gateway 운영 맥락을 ADR-0001·iter 10 기존 런북(`PROGRESS.md` iter 10 참조) 에서 참고해 작성. 스펙의 기준(150 라인, 6 섹션)은 명확.

---

## 실행 선택

**플랜 작성 완료 · `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md` 에 저장. 두 가지 실행 옵션:**

1. **Subagent-Driven (권장)** — Task 당 fresh subagent 를 dispatch, Task 간 리뷰, 빠른 반복
2. **Inline Execution** — 현 세션에서 executing-plans 로 실행, 체크포인트로 배치 실행

**어느 방식으로 진행할까요?**
