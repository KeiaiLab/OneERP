# 경계 규칙 주도 대규모 리팩토링 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `check_layer_boundaries.py`의 경계 규칙 4개를 추가하고, 전체 위반을 0으로 수렴시킨 뒤 `baseline.json`을 0으로 잠가 이후 PR이 위반을 추가할 수 없게 만든다.

**Architecture:** 경계 검사 스크립트(`scripts/dev/check_layer_boundaries.py`)에 신규 규칙을 추가한 뒤, 현재 위반 코드를 올바른 레이어로 이동하고, CI가 `--enforce-zero` 플래그로 영구 게이트를 건다. 코드 이동은 최소 단위로만 수행하며, 공용 추상 인터페이스(Protocol)는 core에 유지한다.

**Tech Stack:** Python 3.14, pytest, `scripts/dev/check_layer_boundaries.py`, `.arch-baseline.json`, `core/.gitea/workflows/ci.yml`

---

## 파일 맵

| 파일 | 변경 유형 | 책임 |
|------|-----------|------|
| `scripts/dev/check_layer_boundaries.py` | 수정 | OE102/OE301/OE401 규칙 추가, OE101 패턴 재정의, `--enforce-zero` 옵션 추가, `_scan_oe301()` 신규 함수 |
| `.arch-baseline.json` | 수정 | 신규 규칙 키 추가 → Task 7에서 전 항목 0으로 갱신 |
| `tests/unit/test_check_layer_boundaries.py` | 수정 | 신규 규칙 + `--enforce-zero` 테스트 추가 |
| `core/oneerp_core/valuation/strategy.py` | 수정 | `MovingAverageStrategy` 제거 (Protocol + dataclass만 유지) |
| `services/scm/stock/oneerp_stock_app/services/valuation.py` | 신규 생성 | `MovingAverageStrategy` 이관 |
| `services/scm/stock/oneerp_stock_app/services/valuation_helpers.py` | 수정 | import 경로 교정 |
| `core/.gitea/workflows/ci.yml` | 수정 | `--enforce-zero` 스텝 추가 |

---

### Task 1: OE101 패턴 재정의 — 오탐 3건 해소

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py:61-67`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** 현재 OE101 패턴이 `planes/_shared/plane_shared/assembler.py`의 조립 유효성 검사 메시지를 도메인 규칙 누수로 오탐하고 있다. 패턴을 실제 도메인 규칙 누수(plane 내 도메인 enum/상수 직접 정의)로 교체한다.

- [ ] **Step 1: 실패 테스트 작성**

`tests/unit/test_check_layer_boundaries.py`에 다음 테스트를 추가한다:

```python
def test_oe101_패턴이_plane_조립_코드를_오탐하지_않는다() -> None:
    """assembler.py 의 조립 유효성 검사는 도메인 규칙 누수가 아니다."""
    module = _load_module()
    report = module.build_report()
    # assembler.py 는 OE101 위반이 아니어야 한다
    oe101_findings = [f for f in report.findings if f.rule == "OE101-plane-domain-rule-leak"]
    assembler_violations = [f for f in oe101_findings if "assembler.py" in f.path]
    assert len(assembler_violations) == 0, (
        f"assembler.py 가 OE101 오탐: {assembler_violations}"
    )
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe101_패턴이_plane_조립_코드를_오탐하지_않는다 -v
```

Expected: FAIL — 현재 assembler.py 3건이 감지됨.

- [ ] **Step 3: OE101 패턴 교체**

`scripts/dev/check_layer_boundaries.py`에서 OE101 항목을 다음으로 교체한다:

```python
"OE101-plane-domain-rule-leak": {
    "paths": PLANE_GLOB,
    "pattern": re.compile(
        # plane 내 도메인 enum 직접 정의 금지
        r"class\s+\w+(?:Status|Type|Category|State)\s*\(\s*(?:str\s*,\s*)?(?:int\s*,\s*)?Enum\b"
        # plane 내 도메인 비즈니스 상수 직접 정의 금지
        r"|(?:^|\s)(?:TAX_RATE|DISCOUNT_RATE|MARKUP_RATE|MARGIN_RATE|MAX_QTY|MIN_QTY)\s*[=:]",
        re.MULTILINE,
    ),
    "desc": "plane 에서 도메인 enum/비즈니스 상수 직접 정의 금지 — 해당 서비스로 이동 (OE101)",
},
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe101_패턴이_plane_조립_코드를_오탐하지_않는다 -v
```

Expected: PASS

- [ ] **Step 5: 경계 검사 실행하여 OE101=0 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py
```

Expected: `[OE101-plane-domain-rule-leak] 0건`

- [ ] **Step 6: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py
git commit -m "fix(arch): OE101 패턴 재정의 — plane 조립 오탐 3건 해소"
```

---

### Task 2: OE102 규칙 추가 — plane 비즈니스 로직 직접 구현 금지

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** plane이 도메인 계산/검증 함수를 직접 구현하는 것을 감지한다. 함수명 패턴(`calculate_`, `compute_`, `apply_rule_`, `apply_discount_`)으로 감지한다.

- [ ] **Step 1: 실패 테스트 작성**

`tests/unit/test_check_layer_boundaries.py`에 추가:

```python
def test_oe102_규칙이_RULES에_존재한다() -> None:
    module = _load_module()
    assert "OE102-plane-business-logic" in module.RULES

def test_oe102_plane_내_비즈니스_함수를_감지한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OE102 패턴이 plane 내 비즈니스 로직 함수명을 잡는다."""
    module = _load_module()
    pattern = module.RULES["OE102-plane-business-logic"]["pattern"]
    # 위반 예: plane 에서 calculate_ 함수 정의
    assert pattern.search("    def calculate_tax(self, amount: Decimal) -> Decimal:")
    # 허용: mount_, health_, router_ 등은 plane 조립 함수
    assert not pattern.search("    def mount_domain(self, app: FastAPI) -> None:")
    assert not pattern.search("    def health_check(self) -> dict:")
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe102_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe102_plane_내_비즈니스_함수를_감지한다 -v
```

Expected: FAIL — `OE102-plane-business-logic` 키가 없음.

- [ ] **Step 3: OE102 규칙 추가**

`scripts/dev/check_layer_boundaries.py`의 `RULES` 딕셔너리에 다음을 추가한다 (OE101 항목 다음):

```python
"OE102-plane-business-logic": {
    "paths": PLANE_GLOB,
    "pattern": re.compile(
        r"^\s*def\s+(?:calculate|compute|apply_rule|apply_discount|calc_tax|calc_price|validate_business)\w*\s*\(",
        re.MULTILINE,
    ),
    "desc": "plane 에서 비즈니스 로직 함수 직접 구현 금지 — services 도메인으로 이동 (OE102)",
},
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe102_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe102_plane_내_비즈니스_함수를_감지한다 -v
```

Expected: PASS

- [ ] **Step 5: 현재 위반 수 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py
```

Expected: OE102 위반 수를 기록해 둔다 (다음 Task에서 baseline에 반영).

- [ ] **Step 6: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py
git commit -m "feat(arch): OE102 규칙 추가 — plane 비즈니스 로직 직접 구현 감지"
```

---

### Task 3: OE301 규칙 추가 — services 크로스 도메인 직접 import 금지

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** 도메인 서비스가 타 도메인 패키지를 직접 import하는 것을 감지한다. 자기 도메인 import는 허용해야 하므로 `_scan_oe301()` 함수를 따로 작성한다.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_oe301_규칙이_RULES에_존재한다() -> None:
    module = _load_module()
    assert "OE301-service-cross-import" in module.RULES

def test_oe301_자기_도메인_import는_허용한다() -> None:
    """selling 서비스 내 oneerp_selling_app import 는 위반이 아니다."""
    module = _load_module()
    # _scan_oe301 내부적으로 자기 도메인 제외를 구현해야 한다
    # 간접 검증: 현재 selling 파일들이 OE301 위반으로 잡히지 않는다
    report = module.build_report()
    oe301 = [f for f in report.findings if f.rule == "OE301-service-cross-import"]
    # selling 내부 oneerp_selling_app import 는 허용 — 포함되면 안 됨
    self_imports = [
        f for f in oe301
        if "services/sales/selling" in f.path and "oneerp_selling" in f.path
    ]
    assert len(self_imports) == 0
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe301_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe301_자기_도메인_import는_허용한다 -v
```

Expected: FAIL — `OE301-service-cross-import` 키가 없음.

- [ ] **Step 3: `_scan_oe301()` 함수 및 규칙 추가**

`scripts/dev/check_layer_boundaries.py`에 다음을 추가한다:

glob 상수 추가 (파일 상단 기존 glob 상수 다음):
```python
SERVICES_GLOB = "services/**/*.py"

# OE301 감지 대상 도메인 패키지명 (oneerp_{name}_app 형식)
_OE301_DOMAINS = (
    "selling", "buying", "stock", "accounting", "payroll",
    "hr", "crm", "pos", "commerce", "reservation",
    "manufacturing", "qm", "expenses",
)
_OE301_IMPORT_RE = re.compile(
    r"from\s+(oneerp_(?:"
    + "|".join(_OE301_DOMAINS)
    + r")_app)\b"
)
_OE301_OWN_DOMAIN_RE = re.compile(r"oneerp_(\w+?)_app")
```

`_scan` 함수 다음에 신규 함수 추가:
```python
def _scan_oe301() -> list[Finding]:
    """services 내 크로스 도메인 import 감지 — 자기 도메인 import 는 제외."""
    findings: list[Finding] = []
    for path in ROOT.glob(SERVICES_GLOB):
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT))
        # 현재 파일의 도메인명 추출
        own_match = _OE301_OWN_DOMAIN_RE.search(rel)
        own_domain = own_match.group(1) if own_match else ""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in _OE301_IMPORT_RE.finditer(text):
            imported_match = _OE301_OWN_DOMAIN_RE.search(m.group(1))
            imported_domain = imported_match.group(1) if imported_match else ""
            if imported_domain == own_domain:
                continue  # 자기 도메인 import 허용
            line = text[: m.start()].count("\n") + 1
            findings.append(Finding(rule="OE301-service-cross-import", path=rel, line=line))
    return findings
```

`RULES` 딕셔너리에 추가:
```python
"OE301-service-cross-import": {
    "paths": SERVICES_GLOB,  # build_report 에서는 _scan_oe301() 로 처리
    "pattern": re.compile(r"__OE301_HANDLED_BY_scan_oe301__"),  # 더미 — 아래 참조
    "desc": "services 간 크로스 도메인 직접 import 금지 — EventBus 또는 core 공용 타입 경유 (OE301)",
},
```

`build_report()` 함수를 다음으로 교체한다:
```python
def build_report() -> Report:
    r = Report()
    for rule, spec in RULES.items():
        if rule == "OE301-service-cross-import":
            r.findings.extend(_scan_oe301())
            continue
        paths: str | list[str] = spec["paths"]
        if isinstance(paths, str):
            paths = [paths]
        for glob in paths:
            r.findings.extend(_scan(rule, glob, spec["pattern"]))
    return r
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe301_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe301_자기_도메인_import는_허용한다 -v
```

Expected: PASS

- [ ] **Step 5: 현재 OE301 위반 수 기록**

```bash
uv run python scripts/dev/check_layer_boundaries.py --verbose 2>&1 | grep OE301
```

Expected: 위반 수를 메모해 둔다 (다음 Task baseline에 반영).

- [ ] **Step 6: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py
git commit -m "feat(arch): OE301 규칙 추가 — services 크로스 도메인 import 감지"
```

---

### Task 4: OE401 규칙 추가 — core 내 단일 도메인 구현체 금지

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** `core/oneerp_core/valuation/strategy.py`의 `MovingAverageStrategy`는 stock 서비스에서만 사용하는 구현체로 core에 있어서는 안 된다. Protocol 클래스(`ValuationStrategy(Protocol)`)는 허용한다.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_oe401_규칙이_RULES에_존재한다() -> None:
    module = _load_module()
    assert "OE401-core-domain-impl" in module.RULES

def test_oe401_Protocol_클래스는_허용한다() -> None:
    module = _load_module()
    pattern = module.RULES["OE401-core-domain-impl"]["pattern"]
    # Protocol 상속 클래스는 허용
    assert not pattern.search("class ValuationStrategy(Protocol):")
    assert not pattern.search("class PricingStrategy(Protocol, runtime_checkable):")
    # 구현 클래스는 감지
    assert pattern.search("class MovingAverageStrategy:")
    assert pattern.search("class FIFOStrategy:")
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe401_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe401_Protocol_클래스는_허용한다 -v
```

Expected: FAIL — `OE401-core-domain-impl` 키가 없음.

- [ ] **Step 3: OE401 규칙 추가**

`scripts/dev/check_layer_boundaries.py` 상단에 glob 추가:
```python
CORE_GLOB = "core/oneerp_core/**/*.py"
```

`RULES`에 추가:
```python
"OE401-core-domain-impl": {
    "paths": CORE_GLOB,
    "pattern": re.compile(
        # Protocol/Abstract 를 상속하지 않는 Strategy 구현체
        r"^class\s+\w+Strategy\b(?!\s*\([^)]*Protocol)",
        re.MULTILINE,
    ),
    "desc": "core 에서 단일 도메인 전략 구현체 정의 금지 — Protocol 선언은 허용, 구현체는 해당 서비스로 이관 (OE401)",
},
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe401_규칙이_RULES에_존재한다 tests/unit/test_check_layer_boundaries.py::test_oe401_Protocol_클래스는_허용한다 -v
```

Expected: PASS

- [ ] **Step 5: OE401 현재 위반 수 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py --verbose 2>&1 | grep -A5 "OE401"
```

Expected: `MovingAverageStrategy` 1건 감지.

- [ ] **Step 6: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py tests/unit/test_check_layer_boundaries.py
git commit -m "feat(arch): OE401 규칙 추가 — core 내 단일 도메인 구현체 감지"
```

---

### Task 5: baseline 재설정 + check 모드 회귀 테스트

**Files:**
- Modify: `.arch-baseline.json`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** 신규 규칙 4개를 포함한 현재 위반 수를 baseline에 기록한다. 이후 `--check` 모드가 baseline 초과를 정확히 감지하는지 검증한다.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_baseline에_신규_규칙_키가_포함된다() -> None:
    import json
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    for key in [
        "OE102-plane-business-logic",
        "OE301-service-cross-import",
        "OE401-core-domain-impl",
    ]:
        assert key in baseline, f"baseline 에 {key} 키 없음"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_baseline에_신규_규칙_키가_포함된다 -v
```

Expected: FAIL — 신규 키가 baseline.json에 없음.

- [ ] **Step 3: baseline 갱신**

```bash
uv run python scripts/dev/check_layer_boundaries.py --update-baseline
```

Expected: `.arch-baseline.json` 파일이 신규 규칙 키를 포함해 갱신됨.

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_baseline에_신규_규칙_키가_포함된다 -v
```

Expected: PASS

- [ ] **Step 5: check 모드 회귀 테스트 작성 및 실행**

```python
def test_check_모드가_baseline_초과_시_nonzero를_반환한다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """위반이 baseline 보다 증가하면 exit code 1 이어야 한다."""
    import json
    import subprocess

    module = _load_module()
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    # 현재 OE002-route-direct-repo-instantiate 은 0건 — baseline 을 -1 로 조작
    fake_baseline = {**baseline, "OE002-route-direct-repo-instantiate": -1}
    fake_path = tmp_path / "fake_baseline.json"
    fake_path.write_text(json.dumps(fake_baseline), encoding="utf-8")

    result = subprocess.run(
        ["uv", "run", "python", "scripts/dev/check_layer_boundaries.py", "--check"],
        capture_output=True,
        env={
            **__import__("os").environ,
            # BASELINE_PATH 를 가짜 파일로 교체하기 위해 monkeypatch 대신
            # 스크립트 내부 상수를 직접 패치한다
        },
        cwd=str(ROOT),
    )
    # 실제로는 baseline=-1 이면 current(0) > -1 이므로 exit 1
    # 단, subprocess 환경에서는 실제 baseline 파일을 읽으므로
    # 현재 OE401 위반이 1건이면 baseline 을 0으로 설정 후 --check 실행
    ...
```

> **참고:** check 모드 회귀 테스트는 실제 baseline을 임시 수정하는 대신, 스크립트를 직접 로드해 `load_baseline()` 을 monkeypatch하는 방식이 더 안정적이다. 아래가 최종 구현:

```python
def test_check_모드가_baseline_초과_시_nonzero를_반환한다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()

    # OE401 위반이 1건인 상태에서 baseline 을 0으로 설정
    monkeypatch.setattr(
        module,
        "load_baseline",
        lambda: {rule: 0 for rule in module.RULES},
    )
    import sys

    monkeypatch.setattr(sys, "argv", ["check_layer_boundaries.py", "--check"])
    exit_code = module.main()
    assert exit_code == 1, "baseline 초과 시 exit 1 이어야 한다"
```

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_check_모드가_baseline_초과_시_nonzero를_반환한다 -v
```

Expected: PASS (OE401 위반 1건이 baseline 0 초과 → exit 1)

- [ ] **Step 6: 커밋**

```bash
git add .arch-baseline.json tests/unit/test_check_layer_boundaries.py
git commit -m "chore(arch): baseline 재설정 — 신규 규칙 4개 포함"
```

---

### Task 6: OE401 위반 소거 — `MovingAverageStrategy` stock 서비스로 이관

**Files:**
- Modify: `core/oneerp_core/valuation/strategy.py`
- Create: `services/scm/stock/oneerp_stock_app/services/valuation.py`
- Modify: `services/scm/stock/oneerp_stock_app/services/valuation_helpers.py`

**배경:** `MovingAverageStrategy`는 `services/scm/stock/`에서만 사용된다. core에서 제거하고 stock 서비스로 이동한다. `ValuationStrategy(Protocol)`, `StockBin`, `ValuationResult`는 공용 추상이므로 core에 유지한다.

- [ ] **Step 1: 실패 테스트 작성**

`tests/unit/test_check_layer_boundaries.py`에 추가:

```python
def test_oe401_위반이_0건이다() -> None:
    module = _load_module()
    report = module.build_report()
    oe401 = [f for f in report.findings if f.rule == "OE401-core-domain-impl"]
    assert len(oe401) == 0, f"OE401 위반 잔존: {oe401}"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe401_위반이_0건이다 -v
```

Expected: FAIL — `MovingAverageStrategy` 1건 감지.

- [ ] **Step 3: stock 서비스에 `valuation.py` 신규 생성**

`services/scm/stock/oneerp_stock_app/services/valuation.py`를 새로 만든다:

```python
"""재고 이동평균 평가 전략 — stock 서비스 전용 구현체.

core.valuation.strategy 의 ValuationStrategy Protocol 을 구현한다.
이관 배경: MovingAverageStrategy 는 stock 서비스에서만 사용하므로
core 에 두는 것이 OE401 규칙 위반이다.
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.valuation.strategy import StockBin, ValuationResult


class MovingAverageStrategy:
    """이동평균 단가 전략 (ERPNext 기본과 동일).

    입고: 가중평균으로 단가 재계산.
    출고: 현재 이동평균 단가로 차감.
    """

    def on_inflow(self, stock_bin: StockBin, qty: Decimal, rate: Decimal) -> ValuationResult:
        new_qty = stock_bin.qty + qty
        if new_qty == Decimal(0):
            return ValuationResult(new_bin=stock_bin, out_rate=Decimal(0))
        new_value = stock_bin.stock_value + (qty * rate)
        new_rate = new_value / new_qty
        return ValuationResult(
            new_bin=StockBin(
                qty=new_qty,
                valuation_rate=new_rate,
                stock_value=new_value,
            ),
            out_rate=Decimal(0),
        )

    def on_outflow(self, stock_bin: StockBin, qty: Decimal) -> ValuationResult:
        out_rate = stock_bin.valuation_rate
        new_qty = stock_bin.qty - qty
        new_value = stock_bin.stock_value - (qty * out_rate)
        return ValuationResult(
            new_bin=StockBin(
                qty=new_qty,
                valuation_rate=stock_bin.valuation_rate,
                stock_value=new_value,
            ),
            out_rate=out_rate,
        )
```

- [ ] **Step 4: `core/oneerp_core/valuation/strategy.py`에서 `MovingAverageStrategy` 제거**

`core/oneerp_core/valuation/strategy.py`에서 `MovingAverageStrategy` 클래스 전체를 삭제한다. `ValuationStrategy(Protocol)`, `StockBin`, `ValuationResult`는 그대로 유지한다.

파일 최종 상태 (클래스 3개 중 구현체 1개만 제거):
```python
"""재고 평가 전략 인터페이스 — Protocol 선언과 공용 데이터클래스만 제공.

구현체(MovingAverageStrategy 등)는 각 도메인 서비스에서 정의한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable


@dataclass
class StockBin:
    """단일 창고·품목 단위의 재고 잔액 스냅샷."""
    qty: Decimal = Decimal(0)
    valuation_rate: Decimal = Decimal(0)
    stock_value: Decimal = Decimal(0)


@dataclass
class ValuationResult:
    """전략이 반환하는 새 잔액."""
    new_bin: StockBin
    out_rate: Decimal = Decimal(0)


@runtime_checkable
class ValuationStrategy(Protocol):
    """재고 평가 전략 공통 인터페이스."""
    def on_inflow(self, stock_bin: StockBin, qty: Decimal, rate: Decimal) -> ValuationResult: ...
    def on_outflow(self, stock_bin: StockBin, qty: Decimal) -> ValuationResult: ...
```

- [ ] **Step 5: `valuation_helpers.py` import 경로 교정**

`services/scm/stock/oneerp_stock_app/services/valuation_helpers.py`의 import를 수정한다:

기존:
```python
from oneerp_core.valuation import MovingAverageStrategy, StockBin
```

교체:
```python
from oneerp_core.valuation.strategy import StockBin
from oneerp_stock_app.services.valuation import MovingAverageStrategy
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_oe401_위반이_0건이다-v
```

Expected: PASS

기존 stock 서비스 테스트도 확인:
```bash
uv run pytest services/scm/stock/ -m "not integration and not e2e" -q
```

Expected: PASS

- [ ] **Step 7: 커밋**

```bash
git add core/oneerp_core/valuation/strategy.py \
        services/scm/stock/oneerp_stock_app/services/valuation.py \
        services/scm/stock/oneerp_stock_app/services/valuation_helpers.py \
        tests/unit/test_check_layer_boundaries.py
git commit -m "refactor(stock): MovingAverageStrategy 를 stock 서비스로 이관 — OE401 소거"
```

---

### Task 7: `--enforce-zero` 옵션 추가 + baseline 전 항목 0으로 잠금

**Files:**
- Modify: `scripts/dev/check_layer_boundaries.py`
- Modify: `.arch-baseline.json`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** `--enforce-zero` 플래그를 추가해 baseline 여부와 무관하게 위반 수 > 0 이면 즉시 실패하게 만든다. 이후 baseline을 0으로 갱신해 잠근다.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_enforce_zero_위반_존재_시_nonzero_반환(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--enforce-zero 모드에서 위반이 1건이라도 있으면 exit 1."""
    module = _load_module()
    import sys

    # 현재 코드베이스가 완전 0이라면 임시로 RULES 에 오항상 1건 나오는 패턴 추가
    original_rules = dict(module.RULES)
    module.RULES["TEST-always-fail"] = {
        "paths": "scripts/dev/check_layer_boundaries.py",
        "pattern": re.compile(r"def main"),  # 이 파일에는 반드시 존재
        "desc": "테스트 전용 더미 규칙",
    }
    monkeypatch.setattr(sys, "argv", ["check_layer_boundaries.py", "--enforce-zero"])
    exit_code = module.main()
    module.RULES.clear()
    module.RULES.update(original_rules)
    assert exit_code == 1

def test_baseline_전_항목이_0이다() -> None:
    import json
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    non_zero = {k: v for k, v in baseline.items() if v != 0}
    assert not non_zero, f"baseline 에 비제로 항목 존재: {non_zero}"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_enforce_zero_위반_존재_시_nonzero_반환 tests/unit/test_check_layer_boundaries.py::test_baseline_전_항목이_0이다 -v
```

Expected: 두 테스트 모두 FAIL — `--enforce-zero` 옵션 없음, baseline에 비제로 항목 있음.

- [ ] **Step 3: `--enforce-zero` 옵션 추가**

`scripts/dev/check_layer_boundaries.py`의 `main()` 함수에 다음을 추가한다:

argparse 선언에 추가:
```python
parser.add_argument(
    "--enforce-zero",
    action="store_true",
    help="위반 수 > 0 이면 즉시 exit 1 (baseline 무관)",
)
```

`args.update_baseline` 처리 블록 다음에 추가:
```python
if args.enforce_zero:
    violations = [rule for rule, count in counts.items() if count > 0]
    if violations:
        print("\n❌ --enforce-zero: 위반 규칙 존재:")
        for v in violations:
            print(f"  {v}: {counts[v]}건")
        return 1
    print("\n✓ --enforce-zero: 모든 규칙 위반 0건")
    return 0
```

- [ ] **Step 4: enforce-zero 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_enforce_zero_위반_존재_시_nonzero_반환 -v
```

Expected: PASS

- [ ] **Step 5: 전체 위반 0건 확인 후 baseline 갱신**

```bash
uv run python scripts/dev/check_layer_boundaries.py
```

Expected: 전 규칙 0건. 만약 0건이 아닌 규칙이 있으면 해당 위반을 먼저 소거한다 (OE102, OE301 위반이 있을 경우 — 각 위반 파일을 `--verbose`로 확인 후 코드를 올바른 레이어로 이동).

0건 확인 후:
```bash
uv run python scripts/dev/check_layer_boundaries.py --update-baseline
```

Expected: `.arch-baseline.json` 전 항목이 0으로 기록됨.

- [ ] **Step 6: baseline=0 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_baseline_전_항목이_0이다 -v
```

Expected: PASS

- [ ] **Step 7: enforce-zero 실행 최종 확인**

```bash
uv run python scripts/dev/check_layer_boundaries.py --enforce-zero
```

Expected: `✓ --enforce-zero: 모든 규칙 위반 0건` 출력, exit 0.

- [ ] **Step 8: 커밋**

```bash
git add scripts/dev/check_layer_boundaries.py .arch-baseline.json tests/unit/test_check_layer_boundaries.py
git commit -m "feat(arch): --enforce-zero 옵션 추가 + baseline 전 항목 0으로 잠금"
```

---

### Task 8: CI 워크플로 강화 — `--enforce-zero` 게이트 추가

**Files:**
- Modify: `core/.gitea/workflows/ci.yml`
- Modify: `tests/unit/test_check_layer_boundaries.py`

**배경:** CI가 모든 PR에서 경계 위반 0건을 자동으로 강제하도록 `--enforce-zero` 스텝을 추가한다.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_ci_workflow에_enforce_zero_스텝이_있다() -> None:
    ci_path = ROOT / "core" / ".gitea" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    assert "--enforce-zero" in text, "CI workflow 에 --enforce-zero 스텝 없음"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_ci_workflow에_enforce_zero_스텝이_있다 -v
```

Expected: FAIL

- [ ] **Step 3: CI workflow에 스텝 추가**

`core/.gitea/workflows/ci.yml`의 `test` job 내 "테스트 실행" 스텝 다음에 추가한다:

```yaml
      - name: 경계 규칙 제로 게이트
        run: |
          if [ -f scripts/dev/check_layer_boundaries.py ]; then
            uv run python scripts/dev/check_layer_boundaries.py --enforce-zero
          else
            echo "SKIP: check_layer_boundaries.py 없음 (core-only checkout)"
          fi
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/test_check_layer_boundaries.py::test_ci_workflow에_enforce_zero_스텝이_있다 -v
```

Expected: PASS

- [ ] **Step 5: 전체 단위 테스트 회귀 확인**

```bash
uv run pytest tests/unit/ -m "not integration and not e2e" -q
```

Expected: 기존 실패 6건은 별도 작업 대상 — 이번 작업 관련 테스트만 모두 PASS.

- [ ] **Step 6: 커밋**

```bash
git add core/.gitea/workflows/ci.yml tests/unit/test_check_layer_boundaries.py
git commit -m "ci: 경계 규칙 제로 게이트(--enforce-zero) CI 스텝 추가"
```

---

## 성공 기준 체크리스트

- [ ] `uv run python scripts/dev/check_layer_boundaries.py --enforce-zero` → exit 0
- [ ] `.arch-baseline.json` 전 항목 값 == 0
- [ ] `uv run pytest tests/unit/test_check_layer_boundaries.py -v` → 전부 PASS
- [ ] `uv run pytest services/scm/stock/ -m "not integration and not e2e" -q` → PASS
- [ ] `core/.gitea/workflows/ci.yml`에 `--enforce-zero` 스텝 존재
