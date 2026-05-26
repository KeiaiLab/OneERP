# Finance 클러스터 병합 파일럿 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `services/finance/{accounting,expenses,finance_extra,payroll}` 4개 서브서비스를 단일 uv 패키지 `oneerp-finance`로 병합하고, 서브모듈 경계 규칙(OE005)을 도입하여 클러스터 단위 배포 구조의 템플릿을 확립한다.

**Architecture:** 파일 이동 → codemod import 재작성 → FastAPI 조립 통합 → 테스트 경로 통합. 서브모듈(`oneerp_finance_app/{accounting,expenses,...}`)은 평면 보존, 공통 영역은 `shared/`에 집약. 신규 경계 규칙은 `check_cluster_boundaries.py`로 CI에서 감시.

**Tech Stack:** Python 3.14, uv workspace 0.11, FastAPI 0.115+, pytest, ruff 0.15, ty 0.0.15

**관련 스펙:** `docs/superpowers/specs/2026-04-14-cluster-merge-granularity-design.md`

---

## Phase 0. 사전 준비 — OE005 규칙 + ADR 골격

### Task 0.1: check_cluster_boundaries.py 신설 (OE005, TDD)

**Files:**
- Create: `scripts/dev/check_cluster_boundaries.py`
- Create: `tests/unit/test_check_cluster_boundaries.py`
- Modify: `.arch-baseline.json` (OE005 키 추가)

- [ ] **Step 1: 실패 테스트 작성**

`tests/unit/test_check_cluster_boundaries.py`:

```python
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "dev" / "check_cluster_boundaries.py"


def _load() -> object:
    spec = importlib.util.spec_from_file_location("check_cluster_boundaries", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_OE005_규칙이_존재한다() -> None:
    module = _load()
    assert "OE005-submodule-cross-import" in module.RULES


def test_OE005_패턴이_cross_submodule_import를_감지한다() -> None:
    module = _load()
    pattern = module.RULES["OE005-submodule-cross-import"]["pattern"]
    # 감지: 같은 클러스터 내 다른 서브모듈로의 직접 import
    assert pattern.search("from oneerp_finance_app.accounting.models import X")
    assert pattern.search("from ..expenses.services import Y")
    # 오탐하지 않음: shared/ 또는 공통 dto 경유
    assert not pattern.search("from oneerp_finance_app.shared.repositories import Z")
    assert not pattern.search("from ..dto import FinanceDTO")
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/unit/test_check_cluster_boundaries.py -v
```
Expected: FAIL — `check_cluster_boundaries.py` 없음.

- [ ] **Step 3: check_cluster_boundaries.py 최소 구현**

```python
"""클러스터 내 서브모듈 경계 검사기 (OE005).

병합된 클러스터 서비스(oneerp_<cluster>_app/)의 서브모듈들이 서로 직접
import 하지 않음을 검증한다. 서브모듈 간 상호작용은 shared/ 또는
이벤트 체인을 경유해야 한다.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / ".arch-baseline.json"
CLUSTER_APP_GLOB = "services/*/oneerp_*_app/**/*.py"


class RuleSpec(TypedDict):
    paths: str
    pattern: re.Pattern[str]
    description: str


# 서브모듈 간 cross import 패턴
# 예: from oneerp_finance_app.accounting.X import Y
#     from ..expenses.services import Z
_CROSS_IMPORT = re.compile(
    r"from\s+(?:oneerp_\w+_app\.(?!shared\b)(?!dto\b)\w+\.|\.\.(?!shared\b)(?!dto\b)\w+\.)",
)

RULES: dict[str, RuleSpec] = {
    "OE005-submodule-cross-import": {
        "paths": CLUSTER_APP_GLOB,
        "pattern": _CROSS_IMPORT,
        "description": "클러스터 서브모듈 간 직접 import 금지 — shared/ 또는 이벤트 경유",
    },
}


def count_violations() -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule_id, rule in RULES.items():
        total = 0
        for path in ROOT.glob(rule["paths"]):
            if "/shared/" in str(path):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            total += len(rule["pattern"].findall(text))
        counts[rule_id] = total
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    counts = count_violations()
    for rule_id, n in counts.items():
        desc = RULES[rule_id]["description"]
        print(f"  [{rule_id}] {n}건 — {desc}")

    if args.check:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for rule_id, n in counts.items():
            if n > baseline.get(rule_id, 0):
                print(f"✗ {rule_id}: {n} > baseline {baseline.get(rule_id, 0)}")
                return 1
        print("✓ cluster baseline 대비 위반 증가 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_cluster_boundaries.py -v
```
Expected: 2 PASS.

- [ ] **Step 5: baseline에 OE005 키 추가**

`.arch-baseline.json` 하단에 추가:

```json
{
  "OE002-route-direct-repo-instantiate": 192,
  "OE002-route-import-repository": 117,
  "OE004-models-define-create-dto": 898,
  "OE101-plane-domain-rule-leak": 0,
  "OE201-web-contract-bypass": 0,
  "OE005-submodule-cross-import": 0
}
```

(파일럿 시작 시점에 cluster 구조가 아직 없으므로 0에서 출발)

- [ ] **Step 6: --check 모드 검증**

```bash
uv run python scripts/dev/check_cluster_boundaries.py --check
```
Expected: `✓ cluster baseline 대비 위반 증가 없음`.

- [ ] **Step 7: 커밋**

```bash
git add scripts/dev/check_cluster_boundaries.py \
        tests/unit/test_check_cluster_boundaries.py \
        .arch-baseline.json
git commit -m "feat(arch): OE005 서브모듈 cross-import 검사기 신설"
```

---

### Task 0.2: ADR-0015 초안 생성

**Files:**
- Create: `docs/governance/adr/0015-cluster-merge-granularity.md`

- [ ] **Step 1: ADR 초안 작성**

```markdown
# ADR-0015: 클러스터 단위 서비스 병합 (파일럿: finance)

- Status: Proposed (파일럿 완료 시 Accepted)
- Date: 2026-04-14
- Related: ADR-0011(runtime cluster), ADR-0014(runtime plane)

## 컨텍스트

30+ 서브서비스가 각자 독립된 uv 패키지·디렉터리 구조를 보유. 배포 단위가
클러스터 경계와 일치하지 않아 스캐폴딩 중복과 공통 추상화 부재가 누적.

## 결정

코드 클러스터(`services/<cluster>/`)를 1차 배포 단위로 승격한다.
클러스터 내 기존 서브서비스는 서브모듈로 보존(하이브리드 D)하되,
서브모듈 간 직접 import는 OE005로 차단하고 공통 영역은 `shared/`에 집약.

데이터 결합이 클러스터를 가로지르는 경우(예: sales↔accounting 자동분개)는
기존 이벤트 체인으로 유지하고 코드 병합하지 않는다.

## 파일럿

- 대상: `finance` 클러스터 (accounting/expenses/finance_extra/payroll)
- 산출물: 단일 uv 패키지 `oneerp-finance`, OE005 baseline=0
- 수용 기준: 기존 unit 테스트 회귀 0, OTC E2E 3회 연속 통과

## 결과

파일럿 완료 후 본 섹션을 채운다.
```

- [ ] **Step 2: 커밋**

```bash
git add docs/governance/adr/0015-cluster-merge-granularity.md
git commit -m "docs(adr): 0015 클러스터 단위 서비스 병합 (Proposed)"
```

---

## Phase 1. finance 구조 이동

### Task 1.1: 목적지 디렉터리 골격 생성

**Files:**
- Create: `services/finance/pyproject.toml`
- Create: `services/finance/oneerp_finance_app/__init__.py`
- Create: `services/finance/oneerp_finance_app/main.py`
- Create: `services/finance/oneerp_finance_app/dto.py`
- Create: `services/finance/oneerp_finance_app/shared/__init__.py`
- Create: `services/finance/oneerp_finance_app/shared/repositories.py`
- Create: `services/finance/tests/__init__.py`
- Create: `services/finance/tests/conftest.py`

- [ ] **Step 1: 실패 테스트 (구조 존재 확인)**

`tests/unit/test_finance_cluster_shell.py` 루트 tests에 추가:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINANCE = ROOT / "services" / "finance"


def test_finance_단일_uv_패키지_골격이_존재한다() -> None:
    assert (FINANCE / "pyproject.toml").exists()
    assert (FINANCE / "oneerp_finance_app" / "__init__.py").exists()
    assert (FINANCE / "oneerp_finance_app" / "main.py").exists()
    assert (FINANCE / "oneerp_finance_app" / "shared").is_dir()
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/unit/test_finance_cluster_shell.py -v
```
Expected: FAIL.

- [ ] **Step 3: pyproject.toml 작성**

`services/finance/pyproject.toml`:

```toml
[project]
name = "oneerp-finance"
version = "0.1.0"
description = "OneERP finance 클러스터 서비스 (accounting/expenses/finance_extra/payroll)"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.11.0",
    "oneerp-core",
]

[tool.uv.sources]
oneerp-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["oneerp_finance_app"]
```

- [ ] **Step 4: 골격 파일 작성**

`services/finance/oneerp_finance_app/__init__.py`:

```python
"""finance 클러스터 서비스 — accounting/expenses/finance_extra/payroll 서브모듈 통합."""
```

`services/finance/oneerp_finance_app/main.py`:

```python
"""finance 클러스터 FastAPI 엔트리."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="OneERP finance cluster")


# Task 3.1에서 서브모듈 router 마운트 추가 예정
```

`services/finance/oneerp_finance_app/dto.py`:

```python
"""finance 클러스터 공통 DTO (cross-submodule 공유)."""

from __future__ import annotations
```

`services/finance/oneerp_finance_app/shared/__init__.py`: 빈 파일

`services/finance/oneerp_finance_app/shared/repositories.py`:

```python
"""finance 클러스터 공통 Repository 팩토리 — 서브모듈 간 공유."""

from __future__ import annotations

from oneerp_core.repository import Repository


def get_shared_repo(collection: str, tenant_id: str) -> Repository:
    """공용 컬렉션 Repository 팩토리."""
    return Repository(collection, tenant_id=tenant_id)
```

`services/finance/tests/__init__.py`: 빈 파일

`services/finance/tests/conftest.py`:

```python
"""finance 클러스터 테스트 공통 fixture."""

from __future__ import annotations
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_finance_cluster_shell.py -v
```
Expected: PASS.

- [ ] **Step 6: 커밋**

```bash
git add services/finance/pyproject.toml services/finance/oneerp_finance_app/ \
        services/finance/tests/__init__.py services/finance/tests/conftest.py \
        tests/unit/test_finance_cluster_shell.py
git commit -m "feat(finance): 클러스터 병합 골격 생성 (oneerp-finance 패키지)"
```

---

### Task 1.2: accounting 서브모듈 이동

**Files:**
- Move: `services/finance/accounting/oneerp_accounting_app/*` → `services/finance/oneerp_finance_app/accounting/*`
- Move: `services/finance/accounting/tests/unit/*` → `services/finance/tests/unit/accounting/*`

- [ ] **Step 1: 사전 회귀 baseline 측정**

```bash
uv run --package oneerp-accounting --directory services/finance/accounting pytest -q --collect-only 2>&1 | tail -3
```

수집된 테스트 개수 기록 (예: `N tests collected`).

- [ ] **Step 2: git mv로 이동**

```bash
mkdir -p services/finance/oneerp_finance_app/accounting
git mv services/finance/accounting/oneerp_accounting_app/* \
       services/finance/oneerp_finance_app/accounting/

mkdir -p services/finance/tests/unit/accounting
git mv services/finance/accounting/tests/unit/* \
       services/finance/tests/unit/accounting/
```

- [ ] **Step 3: 빈 래퍼 디렉터리 제거**

```bash
rm -rf services/finance/accounting/oneerp_accounting_app
rm -rf services/finance/accounting/tests
rm services/finance/accounting/pyproject.toml
rmdir services/finance/accounting 2>/dev/null || true
```

- [ ] **Step 4: 커밋 (import은 다음 Task에서 수정)**

```bash
git add -A services/finance/
git commit -m "refactor(finance): accounting 서브모듈 위치 이동 (import 재작성 전)"
```

---

### Task 1.3: expenses 서브모듈 이동

**Files:**
- Move: `services/finance/expenses/oneerp_expenses_app/*` → `services/finance/oneerp_finance_app/expenses/*`
- Move: `services/finance/expenses/tests/unit/*` → `services/finance/tests/unit/expenses/*`

- [ ] **Step 1: 수집 테스트 개수 기록**

```bash
uv run --package oneerp-expenses --directory services/finance/expenses pytest -q --collect-only 2>&1 | tail -3
```

- [ ] **Step 2: git mv로 이동**

```bash
mkdir -p services/finance/oneerp_finance_app/expenses
git mv services/finance/expenses/oneerp_expenses_app/* \
       services/finance/oneerp_finance_app/expenses/

mkdir -p services/finance/tests/unit/expenses
git mv services/finance/expenses/tests/unit/* \
       services/finance/tests/unit/expenses/
```

- [ ] **Step 3: 빈 래퍼 제거**

```bash
rm -rf services/finance/expenses/oneerp_expenses_app
rm -rf services/finance/expenses/tests
rm services/finance/expenses/pyproject.toml
rmdir services/finance/expenses 2>/dev/null || true
```

- [ ] **Step 4: 커밋**

```bash
git add -A services/finance/
git commit -m "refactor(finance): expenses 서브모듈 위치 이동"
```

---

### Task 1.4: finance_extra 서브모듈 이동

**Files:**
- Move: `services/finance/finance_extra/oneerp_finance_extra_app/*` → `services/finance/oneerp_finance_app/finance_extra/*`

- [ ] **Step 1: 수집 테스트 개수 기록**

```bash
uv run --package oneerp-finance-extra --directory services/finance/finance_extra pytest -q --collect-only 2>&1 | tail -3
```

- [ ] **Step 2: git mv로 이동**

```bash
mkdir -p services/finance/oneerp_finance_app/finance_extra
git mv services/finance/finance_extra/oneerp_finance_extra_app/* \
       services/finance/oneerp_finance_app/finance_extra/

mkdir -p services/finance/tests/unit/finance_extra
git mv services/finance/finance_extra/tests/unit/* \
       services/finance/tests/unit/finance_extra/ 2>/dev/null || true
```

- [ ] **Step 3: 빈 래퍼 제거**

```bash
rm -rf services/finance/finance_extra/oneerp_finance_extra_app
rm -rf services/finance/finance_extra/tests
rm services/finance/finance_extra/pyproject.toml
rmdir services/finance/finance_extra 2>/dev/null || true
```

- [ ] **Step 4: 커밋**

```bash
git add -A services/finance/
git commit -m "refactor(finance): finance_extra 서브모듈 위치 이동"
```

---

### Task 1.5: payroll 서브모듈 이동

**Files:**
- Move: `services/finance/payroll/oneerp_payroll_app/*` → `services/finance/oneerp_finance_app/payroll/*`

- [ ] **Step 1: 수집 테스트 개수 기록**

```bash
uv run --package oneerp-payroll --directory services/finance/payroll pytest -q --collect-only 2>&1 | tail -3
```

- [ ] **Step 2: git mv로 이동**

```bash
mkdir -p services/finance/oneerp_finance_app/payroll
git mv services/finance/payroll/oneerp_payroll_app/* \
       services/finance/oneerp_finance_app/payroll/

mkdir -p services/finance/tests/unit/payroll
git mv services/finance/payroll/tests/unit/* \
       services/finance/tests/unit/payroll/ 2>/dev/null || true
```

- [ ] **Step 3: 빈 래퍼 제거**

```bash
rm -rf services/finance/payroll/oneerp_payroll_app
rm -rf services/finance/payroll/tests
rm services/finance/payroll/pyproject.toml
rmdir services/finance/payroll 2>/dev/null || true
```

- [ ] **Step 4: 커밋**

```bash
git add -A services/finance/
git commit -m "refactor(finance): payroll 서브모듈 위치 이동"
```

---

### Task 1.6: uv workspace 재구성

**Files:**
- Modify: `services/pyproject.toml` (workspace members)
- Modify: `services/uv.lock` (uv sync로 재생성)

- [ ] **Step 1: services/pyproject.toml workspace members 갱신**

`services/pyproject.toml`의 `[tool.uv.workspace]` 섹션에서 제거:
- `finance/accounting`
- `finance/expenses`
- `finance/finance_extra`
- `finance/payroll`

추가:
- `finance`

현재 파일 확인:

```bash
grep -A 30 "\[tool.uv.workspace\]" services/pyproject.toml
```

수정은 수동 또는 sed:

```bash
# finance 하위 4개 라인 제거 + "finance" 추가
```

- [ ] **Step 2: uv sync로 lockfile 재생성**

```bash
cd services && uv sync 2>&1 | tail -5 && cd ..
```
Expected: `oneerp-finance` 패키지 인식, 4개 제거된 멤버 경고 없음.

- [ ] **Step 3: 커밋**

```bash
git add services/pyproject.toml services/uv.lock
git commit -m "chore(uv): finance 클러스터 병합에 맞춘 workspace 재구성"
```

---

## Phase 2. Import 재작성

### Task 2.1: import codemod 스크립트 작성 (TDD)

**Files:**
- Create: `scripts/dev/cluster_import_codemod.py`
- Create: `tests/unit/test_cluster_import_codemod.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/unit/test_cluster_import_codemod.py`:

```python
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODEMOD_PATH = ROOT / "scripts" / "dev" / "cluster_import_codemod.py"


def _load() -> object:
    spec = importlib.util.spec_from_file_location("cluster_import_codemod", CODEMOD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_절대_import를_재작성한다() -> None:
    mod = _load()
    rewritten = mod.rewrite_text(
        "from oneerp_accounting_app.models.journal_entry import X",
        submodule="accounting",
        old_pkg="oneerp_accounting_app",
        new_pkg="oneerp_finance_app",
    )
    assert rewritten == "from oneerp_finance_app.accounting.models.journal_entry import X"


def test_여러_old_import를_일괄_처리한다() -> None:
    mod = _load()
    src = (
        "from oneerp_accounting_app import Y\n"
        "import oneerp_accounting_app.routes.journal_entries as je\n"
    )
    rewritten = mod.rewrite_text(
        src,
        submodule="accounting",
        old_pkg="oneerp_accounting_app",
        new_pkg="oneerp_finance_app",
    )
    assert "from oneerp_finance_app.accounting import Y" in rewritten
    assert "import oneerp_finance_app.accounting.routes.journal_entries as je" in rewritten


def test_무관한_import는_유지한다() -> None:
    mod = _load()
    src = "from oneerp_core.repository import Repository"
    assert (
        mod.rewrite_text(
            src,
            submodule="accounting",
            old_pkg="oneerp_accounting_app",
            new_pkg="oneerp_finance_app",
        )
        == src
    )
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/unit/test_cluster_import_codemod.py -v
```
Expected: FAIL.

- [ ] **Step 3: codemod 구현**

`scripts/dev/cluster_import_codemod.py`:

```python
"""클러스터 병합 시 서브모듈 import 재작성 codemod.

예: from oneerp_accounting_app.X import Y
  → from oneerp_finance_app.accounting.X import Y
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def rewrite_text(
    text: str,
    *,
    submodule: str,
    old_pkg: str,
    new_pkg: str,
) -> str:
    """단일 파일 텍스트 내의 import를 재작성한다."""
    # from <old_pkg>.X import Y → from <new_pkg>.<submodule>.X import Y
    text = re.sub(
        rf"\bfrom\s+{re.escape(old_pkg)}\.",
        f"from {new_pkg}.{submodule}.",
        text,
    )
    # from <old_pkg> import Y → from <new_pkg>.<submodule> import Y
    text = re.sub(
        rf"\bfrom\s+{re.escape(old_pkg)}\s+import\b",
        f"from {new_pkg}.{submodule} import",
        text,
    )
    # import <old_pkg>.X → import <new_pkg>.<submodule>.X
    text = re.sub(
        rf"\bimport\s+{re.escape(old_pkg)}\.",
        f"import {new_pkg}.{submodule}.",
        text,
    )
    # import <old_pkg> → import <new_pkg>.<submodule>
    text = re.sub(
        rf"\bimport\s+{re.escape(old_pkg)}\b(?!\.)",
        f"import {new_pkg}.{submodule}",
        text,
    )
    return text


def rewrite_tree(root: Path, *, submodule: str, old_pkg: str, new_pkg: str) -> list[Path]:
    """디렉터리 트리 전체에 rewrite_text를 적용하고, 수정된 경로 목록을 반환."""
    changed: list[Path] = []
    for path in root.rglob("*.py"):
        original = path.read_text(encoding="utf-8")
        rewritten = rewrite_text(
            original, submodule=submodule, old_pkg=old_pkg, new_pkg=new_pkg
        )
        if rewritten != original:
            path.write_text(rewritten, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="재작성 대상 루트 디렉터리")
    parser.add_argument("--submodule", required=True)
    parser.add_argument("--old-pkg", required=True)
    parser.add_argument("--new-pkg", required=True)
    args = parser.parse_args()

    changed = rewrite_tree(
        Path(args.root),
        submodule=args.submodule,
        old_pkg=args.old_pkg,
        new_pkg=args.new_pkg,
    )
    print(f"수정된 파일 수: {len(changed)}")
    for p in changed:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_cluster_import_codemod.py -v
```
Expected: 3 PASS.

- [ ] **Step 5: 커밋**

```bash
git add scripts/dev/cluster_import_codemod.py tests/unit/test_cluster_import_codemod.py
git commit -m "feat(tools): 클러스터 import 재작성 codemod"
```

---

### Task 2.2: codemod 적용 (accounting)

**Files:**
- Modify: `services/finance/oneerp_finance_app/accounting/**/*.py`
- Modify: `services/finance/tests/unit/accounting/**/*.py`
- Modify: 크로스 서비스 참조자 (grep으로 탐지)

- [ ] **Step 1: 크로스 서비스 참조자 사전 탐지**

```bash
grep -rn "oneerp_accounting_app" services/ packages/ tests/ | \
  grep -v "services/finance/oneerp_finance_app/accounting/" | \
  cut -d: -f1 | sort -u > /tmp/accounting_refs.txt
wc -l /tmp/accounting_refs.txt
```

목록을 기록한다 (빈 경우 참조자 없음, 있는 경우 모두 함께 재작성해야 함).

- [ ] **Step 2: accounting 서브모듈 내부 재작성**

```bash
uv run python scripts/dev/cluster_import_codemod.py \
  --root services/finance/oneerp_finance_app/accounting \
  --submodule accounting \
  --old-pkg oneerp_accounting_app \
  --new-pkg oneerp_finance_app
```

- [ ] **Step 3: accounting 테스트 디렉터리 재작성**

```bash
uv run python scripts/dev/cluster_import_codemod.py \
  --root services/finance/tests/unit/accounting \
  --submodule accounting \
  --old-pkg oneerp_accounting_app \
  --new-pkg oneerp_finance_app
```

- [ ] **Step 4: 크로스 서비스 참조자 재작성**

Step 1의 `/tmp/accounting_refs.txt`에 나열된 각 파일에 동일 codemod 적용:

```bash
while read -r f; do
  dir=$(dirname "$f")
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$dir" \
    --submodule accounting \
    --old-pkg oneerp_accounting_app \
    --new-pkg oneerp_finance_app
done < /tmp/accounting_refs.txt
```

- [ ] **Step 5: import 잔재 확인 (0건이어야 함)**

```bash
grep -rn "oneerp_accounting_app" services/ packages/ tests/
```
Expected: 출력 없음.

- [ ] **Step 6: accounting 서브모듈 단위 테스트 수집 가능 확인**

```bash
uv run --package oneerp-finance --directory services/finance pytest tests/unit/accounting -q --collect-only 2>&1 | tail -3
```
Expected: 수집 성공 (Task 1.2 Step 1 기록값과 동일).

- [ ] **Step 7: 커밋**

```bash
git add -A
git commit -m "refactor(finance): accounting 서브모듈 import 재작성"
```

---

### Task 2.3: codemod 적용 (expenses)

**Files:**
- Modify: `services/finance/oneerp_finance_app/expenses/**/*.py`
- Modify: `services/finance/tests/unit/expenses/**/*.py`
- Modify: 크로스 서비스 참조자

- [ ] **Step 1: 사전 탐지**

```bash
grep -rn "oneerp_expenses_app" services/ packages/ tests/ | \
  grep -v "services/finance/oneerp_finance_app/expenses/" | \
  cut -d: -f1 | sort -u > /tmp/expenses_refs.txt
```

- [ ] **Step 2: expenses 내부 + 테스트 재작성**

```bash
for target in services/finance/oneerp_finance_app/expenses services/finance/tests/unit/expenses; do
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$target" \
    --submodule expenses \
    --old-pkg oneerp_expenses_app \
    --new-pkg oneerp_finance_app
done
```

- [ ] **Step 3: 크로스 참조자 재작성**

```bash
while read -r f; do
  dir=$(dirname "$f")
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$dir" \
    --submodule expenses \
    --old-pkg oneerp_expenses_app \
    --new-pkg oneerp_finance_app
done < /tmp/expenses_refs.txt
```

- [ ] **Step 4: 잔재 확인**

```bash
grep -rn "oneerp_expenses_app" services/ packages/ tests/
```
Expected: 출력 없음.

- [ ] **Step 5: 테스트 수집**

```bash
uv run --package oneerp-finance --directory services/finance pytest tests/unit/expenses -q --collect-only 2>&1 | tail -3
```

- [ ] **Step 6: 커밋**

```bash
git add -A
git commit -m "refactor(finance): expenses 서브모듈 import 재작성"
```

---

### Task 2.4: codemod 적용 (finance_extra + payroll)

**Files:**
- Modify: `services/finance/oneerp_finance_app/{finance_extra,payroll}/**/*.py`
- Modify: `services/finance/tests/unit/{finance_extra,payroll}/**/*.py`
- Modify: 크로스 서비스 참조자

- [ ] **Step 1: finance_extra 처리**

```bash
grep -rn "oneerp_finance_extra_app" services/ packages/ tests/ | \
  grep -v "services/finance/oneerp_finance_app/finance_extra/" | \
  cut -d: -f1 | sort -u > /tmp/finance_extra_refs.txt

for target in services/finance/oneerp_finance_app/finance_extra services/finance/tests/unit/finance_extra; do
  [ -d "$target" ] || continue
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$target" \
    --submodule finance_extra \
    --old-pkg oneerp_finance_extra_app \
    --new-pkg oneerp_finance_app
done

while read -r f; do
  [ -z "$f" ] && continue
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$(dirname "$f")" \
    --submodule finance_extra \
    --old-pkg oneerp_finance_extra_app \
    --new-pkg oneerp_finance_app
done < /tmp/finance_extra_refs.txt
```

- [ ] **Step 2: payroll 처리**

```bash
grep -rn "oneerp_payroll_app" services/ packages/ tests/ | \
  grep -v "services/finance/oneerp_finance_app/payroll/" | \
  cut -d: -f1 | sort -u > /tmp/payroll_refs.txt

for target in services/finance/oneerp_finance_app/payroll services/finance/tests/unit/payroll; do
  [ -d "$target" ] || continue
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$target" \
    --submodule payroll \
    --old-pkg oneerp_payroll_app \
    --new-pkg oneerp_finance_app
done

while read -r f; do
  [ -z "$f" ] && continue
  uv run python scripts/dev/cluster_import_codemod.py \
    --root "$(dirname "$f")" \
    --submodule payroll \
    --old-pkg oneerp_payroll_app \
    --new-pkg oneerp_finance_app
done < /tmp/payroll_refs.txt
```

- [ ] **Step 3: 잔재 확인**

```bash
grep -rn "oneerp_finance_extra_app\|oneerp_payroll_app" services/ packages/ tests/
```
Expected: 출력 없음.

- [ ] **Step 4: 커밋**

```bash
git add -A
git commit -m "refactor(finance): finance_extra + payroll 서브모듈 import 재작성"
```

---

### Task 2.5: cross-submodule import 탐지 및 shared/ 승격

**Files:**
- Create/Modify: `services/finance/oneerp_finance_app/shared/*.py` (발견 시)
- Modify: 서브모듈 파일들

- [ ] **Step 1: cross-submodule import 탐지**

```bash
uv run python scripts/dev/check_cluster_boundaries.py 2>&1 | tail -5
```

OE005 위반 수를 기록한다.

- [ ] **Step 2: 위반 목록 획득**

위반이 있는 경우, 파일별 import 구문을 나열:

```bash
grep -rnE "from oneerp_finance_app\.(accounting|expenses|finance_extra|payroll)\." \
     services/finance/oneerp_finance_app/ | \
  grep -vE "/(accounting|expenses|finance_extra|payroll)/"
# 서브모듈 내부에서 다른 서브모듈로 향하는 import만 남음
grep -rnE "^from oneerp_finance_app\.(accounting|expenses|finance_extra|payroll)\." \
     services/finance/oneerp_finance_app/accounting \
     services/finance/oneerp_finance_app/expenses \
     services/finance/oneerp_finance_app/finance_extra \
     services/finance/oneerp_finance_app/payroll
```

- [ ] **Step 3: 각 위반을 shared/로 승격 또는 이벤트 체인 전환**

각 위반에 대해 판단:
- **shared로 승격**: 공통 타입/Repository 팩토리 → `services/finance/oneerp_finance_app/shared/<name>.py`로 이동 후 양쪽 서브모듈이 shared에서 import
- **이벤트 체인 전환**: 비즈니스 로직 호출 → 이벤트 publish로 대체, consumer 서브모듈이 subscribe

판단 예시:
- `from oneerp_finance_app.accounting.models import JournalEntry`를 payroll에서 사용 중 → 이벤트 `journal_entry.requested` 발행으로 전환
- `from oneerp_finance_app.accounting.shared_types import CurrencyCode` → `shared/types.py`로 승격

각 승격마다 개별 커밋:

```bash
git add -A
git commit -m "refactor(finance): <심볼명> shared/ 승격 (OE005)"
```

- [ ] **Step 4: OE005 baseline=0 확인**

```bash
uv run python scripts/dev/check_cluster_boundaries.py --check
```
Expected: `✓ cluster baseline 대비 위반 증가 없음`.

- [ ] **Step 5: 통합 커밋 (남은 변경 있으면)**

```bash
git add -A
git status --short
git commit -m "refactor(finance): cross-submodule import 해소 완료 (OE005 baseline=0)" --allow-empty
```

---

## Phase 3. FastAPI 조립 통합

### Task 3.1: 서브모듈 router 마운트

**Files:**
- Modify: `services/finance/oneerp_finance_app/main.py`
- Modify: `services/finance/oneerp_finance_app/__init__.py`

- [ ] **Step 1: 실패 테스트 (통합 앱 기동 확인)**

`services/finance/tests/unit/test_app_assembly.py`:

```python
from __future__ import annotations


def test_finance_app이_4개_서브모듈_router를_마운트한다() -> None:
    from oneerp_finance_app.main import app

    prefixes = {route.path for route in app.routes}
    # 각 서브모듈의 대표 엔드포인트 prefix가 마운트되었는지
    assert any("/api/v1/journal-entries" in p for p in prefixes), "accounting router 누락"
    # expenses / finance_extra / payroll 중 최소 하나씩 대표 prefix 확인
    assert any("/api/v1/expense" in p.lower() for p in prefixes), "expenses router 누락"
    assert any("/api/v1/payroll" in p.lower() or "/api/v1/salary" in p.lower()
               for p in prefixes), "payroll router 누락"
```

- [ ] **Step 2: 실패 확인**

```bash
uv run --package oneerp-finance --directory services/finance pytest tests/unit/test_app_assembly.py -v
```
Expected: FAIL.

- [ ] **Step 3: 각 서브모듈의 대표 router 확인**

```bash
grep -rn "APIRouter(" services/finance/oneerp_finance_app/accounting/routes/ | head -3
grep -rn "APIRouter(" services/finance/oneerp_finance_app/expenses/routes/ | head -3
grep -rn "APIRouter(" services/finance/oneerp_finance_app/finance_extra/routes/ 2>/dev/null | head -3
grep -rn "APIRouter(" services/finance/oneerp_finance_app/payroll/routes/ | head -3
```

발견한 router를 main.py에 마운트할 목록으로 정리한다.

- [ ] **Step 4: main.py에 router 마운트**

`services/finance/oneerp_finance_app/main.py` 재작성:

```python
"""finance 클러스터 FastAPI 엔트리 — 서브모듈 router 통합."""

from __future__ import annotations

from fastapi import FastAPI

from .accounting.routes.journal_entries import router as accounting_journal_entries_router
from .accounting.routes.accounts_receivable import router as accounting_ar_router
# (Step 3에서 발견한 모든 서브모듈 router를 import)

app = FastAPI(title="OneERP finance cluster")

# accounting 서브모듈
app.include_router(accounting_journal_entries_router)
app.include_router(accounting_ar_router)

# expenses / finance_extra / payroll 서브모듈
# (Step 3의 목록에 따라 include_router 호출)
```

(실제 import와 include_router는 Step 3에서 발견한 목록으로 채운다.)

- [ ] **Step 5: 테스트 통과**

```bash
uv run --package oneerp-finance --directory services/finance pytest tests/unit/test_app_assembly.py -v
```
Expected: PASS.

- [ ] **Step 6: 커밋**

```bash
git add services/finance/oneerp_finance_app/main.py \
        services/finance/tests/unit/test_app_assembly.py
git commit -m "feat(finance): 4개 서브모듈 router 통합 마운트"
```

---

### Task 3.2: uvicorn 기동 sanity

**Files:**
- Test: 런타임 기동만 검증 (파일 수정 없음)

- [ ] **Step 1: uvicorn 기동**

```bash
uv run --package oneerp-finance --directory services/finance \
  uvicorn oneerp_finance_app.main:app --port 8099 &
SERVER_PID=$!
sleep 3
```

- [ ] **Step 2: OpenAPI 스펙 조회**

```bash
curl -sf http://localhost:8099/openapi.json | \
  python -c "import json, sys; d=json.load(sys.stdin); print(len(d['paths']), 'paths')"
```
Expected: path 수 > 0.

- [ ] **Step 3: 종료**

```bash
kill $SERVER_PID
```

- [ ] **Step 4: 기동 통과 커밋 (변경 없으면 스킵)**

(Step 1~3은 검증이므로 파일 변경 없음. 이 task는 커밋 없이 PASS로 종료.)

---

## Phase 4. 테스트 경로 통합

### Task 4.1: pytest marker 부여

**Files:**
- Modify: `services/finance/pyproject.toml`
- Modify: `services/finance/tests/unit/{accounting,expenses,finance_extra,payroll}/conftest.py` (없으면 생성)

- [ ] **Step 1: pyproject.toml에 marker 선언**

`services/finance/pyproject.toml`에 추가:

```toml
[tool.pytest.ini_options]
markers = [
    "accounting: accounting 서브모듈 테스트",
    "expenses: expenses 서브모듈 테스트",
    "finance_extra: finance_extra 서브모듈 테스트",
    "payroll: payroll 서브모듈 테스트",
]
testpaths = ["tests"]
```

- [ ] **Step 2: 서브모듈별 conftest.py로 자동 marker 부여**

`services/finance/tests/unit/accounting/conftest.py`:

```python
"""accounting 서브모듈 테스트 — 자동 marker 부여."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        item.add_marker(pytest.mark.accounting)
```

expenses / finance_extra / payroll 동일 패턴 (marker 이름만 변경).

- [ ] **Step 3: marker별 선택 실행 검증**

```bash
uv run --package oneerp-finance --directory services/finance pytest -m accounting --collect-only -q 2>&1 | tail -3
uv run --package oneerp-finance --directory services/finance pytest -m expenses --collect-only -q 2>&1 | tail -3
```
Expected: 각 marker별로 수집 결과가 해당 서브모듈 테스트 수와 일치.

- [ ] **Step 4: 커밋**

```bash
git add services/finance/pyproject.toml services/finance/tests/unit/*/conftest.py
git commit -m "test(finance): 서브모듈별 pytest marker 자동 부여"
```

---

### Task 4.2: 전체 회귀 확인

**Files:**
- Test: (실행만)

- [ ] **Step 1: 전수 실행**

```bash
uv run --package oneerp-finance --directory services/finance pytest -q 2>&1 | tail -10
```

- [ ] **Step 2: 이동 전 baseline 비교**

Task 1.2/1.3/1.4/1.5 Step 1에서 기록한 수집 수 합계와 비교.
Expected: **수집 수 동일** (마이그레이션 과정에서 테스트 손실 0).

- [ ] **Step 3: 신규 실패가 있으면 조사**

기존 통과 테스트 중 신규 실패가 있다면 중단하고 원인 분석:
- 가장 흔한 원인: 서브모듈 간 mock 경로 변경 필요 (`@patch("oneerp_accounting_app.X")` → `@patch("oneerp_finance_app.accounting.X")`)
- codemod가 `@patch` 문자열 인자는 재작성하지 않음 → 수동 grep + 수정

```bash
grep -rn '"oneerp_accounting_app\|"oneerp_expenses_app\|"oneerp_finance_extra_app\|"oneerp_payroll_app' \
     services/finance/
```

발견 시 수동 수정 후 재실행.

- [ ] **Step 4: 통과 확인 커밋 (수정 있었던 경우)**

```bash
git add -A
git commit -m "fix(finance): mock 문자열 경로를 병합 후 구조로 갱신"
```

---

## Phase 5. 수용 기준 · 마무리

### Task 5.1: boundary checker 전수 통과

**Files:**
- Modify: `.arch-baseline.json` (OE002/OE004 재측정)

- [ ] **Step 1: 기존 boundary checker 재측정**

```bash
uv run python scripts/dev/check_layer_boundaries.py 2>&1 | tail -8
```

OE002/OE004 위반 수가 파일 이동으로 숫자가 동일한지 확인 (glob이 `services/*/*/oneerp_*_app/`이므로 `services/finance/oneerp_finance_app/accounting/routes/*.py`는 매칭 안 됨).

glob을 병합 후 구조도 커버하도록 확장 필요:

- [ ] **Step 2: check_layer_boundaries.py glob 확장 (병합 대응)**

`scripts/dev/check_layer_boundaries.py`의 27-28행:

```python
ROUTES_GLOB = "services/*/*/oneerp_*_app/routes/*.py"
MODELS_GLOB = "services/*/*/oneerp_*_app/models/*.py"
```

를 다음으로 교체 (2축 매칭):

```python
ROUTES_GLOB = [
    "services/*/*/oneerp_*_app/routes/*.py",          # 병합 전 구조
    "services/*/oneerp_*_app/*/routes/*.py",          # 병합 후 서브모듈 구조
]
MODELS_GLOB = [
    "services/*/*/oneerp_*_app/models/*.py",
    "services/*/oneerp_*_app/*/models/*.py",
]
```

(주의: 리스트로 변경되었으므로 `RULES`에서 `paths` 처리가 list를 받도록 확인하거나, 단일 glob이면 `{,*/}` brace expansion 지원 여부 확인. 단순화: Path.glob이 brace를 지원하지 않으므로 list 처리 로직 추가.)

관련 테스트 `tests/unit/test_check_layer_boundaries.py`에 병합 구조 인식 테스트 추가:

```python
def test_glob이_병합_서브모듈_구조도_인식한다() -> None:
    cblm = _load_module()
    routes_globs = cblm.ROUTES_GLOB if isinstance(cblm.ROUTES_GLOB, list) else [cblm.ROUTES_GLOB]
    assert any("oneerp_*_app/*/routes" in g for g in routes_globs), (
        "병합된 서브모듈 구조(oneerp_*_app/<submodule>/routes)를 인식해야 함"
    )
```

TDD: Step 1 테스트 작성 → 실패 확인 → 구현 → 통과 확인.

- [ ] **Step 3: 재측정 + baseline 갱신**

```bash
uv run python scripts/dev/check_layer_boundaries.py 2>&1 | tail -8
```

출력값으로 `.arch-baseline.json` 업데이트 (OE002/OE004가 파일 이동으로 숫자가 바뀔 수 있으므로 실측값 그대로 기록).

- [ ] **Step 4: --check 통과 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py --check
uv run python scripts/dev/check_cluster_boundaries.py --check
```
Expected: 둘 다 통과.

- [ ] **Step 5: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py .arch-baseline.json
git commit -m "chore(arch): 병합 구조 대응 glob 확장 + baseline 재측정"
```

---

### Task 5.2: OTC E2E 3회 연속 회귀

**Files:**
- Test: (실행만)

- [ ] **Step 1: Docker Compose로 의존 서비스 기동**

```bash
docker compose -f docker-compose.dev.yml up -d ferretdb nats 2>&1 | tail -3
```

(프로젝트의 E2E 기동 전제 파일을 확인하여 필요한 서비스 기동.)

- [ ] **Step 2: OTC E2E 3회 연속 실행**

```bash
for i in 1 2 3; do
  echo "=== Run $i ==="
  PYTHONPATH=$(pwd) ONEERP_JWT_SECRET="dev-secret-32bytes-for-test-env-only" \
    uv run pytest tests/e2e/test_order_to_cash_flow.py -v 2>&1 | tail -5
done
```
Expected: 3회 모두 PASS.

- [ ] **Step 3: 실패 시 중단 + 원인 분석**

accounting 경로 변경으로 인한 journal_entry 연동 실패가 가장 가능성 높음. 로그에서 import/404/5xx 중 어디서 깨지는지 확인.

- [ ] **Step 4: 통과 시 커밋 없음 (읽기 전용 검증)**

---

### Task 5.3: 컨테이너 빌드 sanity

**Files:**
- Create (필요 시): `services/finance/Dockerfile`

- [ ] **Step 1: 기존 Dockerfile 참조 확인**

```bash
find services/finance -name Dockerfile -maxdepth 3 2>/dev/null
find services -name Dockerfile -maxdepth 4 | head -5
```

기존 서비스의 Dockerfile 패턴을 확인한다.

- [ ] **Step 2: services/finance/Dockerfile 작성**

기존 패턴을 참고하여 `services/finance/Dockerfile` 신규 작성:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# uv 설치
RUN pip install --no-cache-dir uv==0.11.1

# workspace 복사
COPY services/ /app/services/
COPY packages/ /app/packages/

WORKDIR /app/services

# oneerp-finance 패키지 동기화
RUN uv sync --package oneerp-finance --frozen

EXPOSE 8000

CMD ["uv", "run", "--package", "oneerp-finance", "--directory", "finance", \
     "uvicorn", "oneerp_finance_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

(프로젝트의 기존 Dockerfile 패턴에 맞춰 세부 조정.)

- [ ] **Step 3: buildx로 linux/amd64 빌드**

```bash
docker buildx build \
  --builder masblue-builder \
  --platform linux/amd64 \
  -t oneerp-finance:pilot \
  -f services/finance/Dockerfile \
  . 2>&1 | tail -10
```
Expected: `Successfully built` 또는 buildx 성공 로그.

- [ ] **Step 4: 컨테이너 기동 sanity**

```bash
docker run --rm -d --name finance-pilot -p 8100:8000 oneerp-finance:pilot
sleep 5
curl -sf http://localhost:8100/openapi.json | python -c "import json,sys; print(len(json.load(sys.stdin)['paths']),'paths')"
docker stop finance-pilot
```

- [ ] **Step 5: 커밋**

```bash
git add services/finance/Dockerfile
git commit -m "chore(finance): 병합 클러스터 Dockerfile 추가"
```

---

### Task 5.4: ADR-0015 Accepted 승격

**Files:**
- Modify: `docs/governance/adr/0015-cluster-merge-granularity.md`

- [ ] **Step 1: ADR 본문 갱신**

`docs/governance/adr/0015-cluster-merge-granularity.md`의 `Status: Proposed` → `Status: Accepted` 변경.

"결과" 섹션 채우기:

```markdown
## 결과

파일럿 `finance` 클러스터 완료 (2026-04-NN):
- 4개 서브서비스 → 단일 uv 패키지 `oneerp-finance` 병합
- OE005 baseline=0
- OTC E2E 3회 연속 통과
- 컨테이너 빌드 성공

후속: 나머지 12개 클러스터를 클러스터당 1 PR로 롤아웃 (별도 plan).
참고: `docs/superpowers/plans/2026-04-14-finance-cluster-merge-pilot.md`
```

- [ ] **Step 2: 커밋**

```bash
git add docs/governance/adr/0015-cluster-merge-granularity.md
git commit -m "docs(adr): 0015 Accepted — finance 파일럿 완료"
```

---

### Task 5.5: 파일럿 완료 요약 커밋

**Files:**
- Modify: `docs/superpowers/specs/2026-04-14-cluster-merge-granularity-design.md` (footer에 완료 링크)

- [ ] **Step 1: 스펙 문서 footer 갱신**

스펙 파일 끝에 추가:

```markdown

## 파일럿 완료 기록

- 완료일: 2026-04-NN
- 커밋 범위: `<Phase 0 시작 SHA>..<Task 5.4 SHA>`
- ADR: `docs/governance/adr/0015-cluster-merge-granularity.md` (Accepted)
- 후속 롤아웃 plan: (작성 예정)
```

- [ ] **Step 2: 커밋**

```bash
git add docs/superpowers/specs/2026-04-14-cluster-merge-granularity-design.md
git commit -m "docs(spec): finance 파일럿 완료 기록 추가"
```

---

## 완료 정의 (Definition of Done)

다음을 모두 만족하면 파일럿 완료:

- [ ] Task 0.1~5.5 모든 체크박스 ✓
- [ ] `uv run python scripts/dev/check_cluster_boundaries.py --check` 통과 (OE005 = 0)
- [ ] `uv run python scripts/dev/check_layer_boundaries.py --check` 통과 (OE002/OE004 비증가)
- [ ] `uv run --package oneerp-finance --directory services/finance pytest -q` — 신규 실패 0
- [ ] OTC E2E 3회 연속 통과
- [ ] `docker buildx build` linux/amd64 성공
- [ ] ADR-0015 Status: Accepted
- [ ] `services/finance/{accounting,expenses,finance_extra,payroll}` 서브디렉터리 및 그 하위의 `oneerp_*_app/`, `pyproject.toml` 잔존 0건

---

## 참고 · 제약

- 모든 커밋 메시지·코멘트·주석은 한국어
- `docker buildx` + `masblue-builder` 기본 빌더 사용, `--platform` 생략 가능 (자동 linux/amd64)
- 프로덕션 배포·Helm rollout은 본 파일럿 범위 밖 (별도 배포 이니셔티브)
- 도메인 재분해·보일러플레이트 공통화는 별도 스펙에서 다룬다
