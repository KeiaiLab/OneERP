# 경계 규칙 주도 대규모 리팩토링 설계서

> 작성일: 2026-04-14
> 방안: A (Boundary-First — 경계 규칙 주도)

---

## 배경

OneERP는 2축 아키텍처(코드 클러스터 × 런타임 plane)를 채택하고 있다.
이전 리팩토링 사이클(2026-04-13)에서 OE002(route→repo), OE004(models→DTO) 위반이 이미 0건으로 해소되었다.
그러나 현재 경계 검사 규칙이 커버하지 못하는 사각지대가 존재하며, baseline.json이 낡아서 실제보다 훨씬 높은 허용량을 설정 중이다.

---

## 목표

| 기준 | 현재 | 목표 |
|------|------|------|
| OE002 route→repo | 0 ✅ | 0 유지 |
| OE004 models→DTO | 0 ✅ | 0 유지 |
| OE101 plane→domain | 3 ❌ | **0** |
| OE201 web→any | 0 ✅ | 0 유지 |
| OE102 plane→비즈니스로직 | 미측정 ⚠️ | **0** |
| OE301 services→크로스import | 미측정 ⚠️ | **0** |
| OE401 core→도메인오염 | 미측정 ⚠️ | **0** |

**완료 조건:** 모든 규칙 위반 0건, `baseline.json` 전 항목 0으로 잠금.

---

## 의존 방향 원칙

```
core (kernel + infra 어댑터만)
  ↓ 의존만 허용
services (도메인 유스케이스 — 타 도메인 직접 import 금지)
  ↓ mount만 허용
planes (조립자 — 도메인 규칙 구현 금지)
  ↓ 계약 타입만 소비
web (렌더링 — any 계약 우회 금지)
```

역방향 import 및 계층 건너뛰기 전면 금지.

---

## 신규 경계 규칙 (4개)

### OE102 — plane 비즈니스 로직 직접 구현 금지

- **대상:** `planes/**/*.py`
- **패턴:** `def (calculate|validate|apply_rule|compute)_\w+`
- **허용 예외:** plane 내부 mount/health/라우팅 관련 함수
- **근거:** plane은 조립자. 계산·검증은 services 도메인 책임

### OE301 — services 간 크로스 도메인 직접 import 금지

- **대상:** `services/**/*.py`
- **패턴:** `from oneerp_(selling|buying|stock|accounting|payroll|hr|crm|pos|commerce|reservation|manufacturing|qm|expenses)\b`
- **자기 도메인 제외 구현:** 파일 경로에서 서비스명을 추출해 import 대상과 동일하면 위반에서 제외 (예: `services/finance/accounting/` 파일이 `oneerp_accounting`을 import하는 것은 허용)
- **허용 예외:** `oneerp-core` 공용 타입 import는 허용
- **근거:** 도메인 간 통신은 EventBus 또는 core 공용 계약 타입 경유

### OE401 — core 패키지 내 도메인 로직 오염 금지

- **대상:** `core/oneerp_core/*.py`, `core/oneerp_core/**/*.py`
- **패턴:** 파일명 `pricing_rule`, `valuation` 또는 파일 내 `tax_calc`, `inventory_count`, `unit_price` 등 도메인 키워드
- **허용 예외:** 공용 추상 인터페이스 (`PricingStrategy` 프로토콜 등)
- **근거:** core는 커널·인프라 어댑터 전용. 도메인 로직은 해당 서비스로 이관

### OE101 (패턴 확대) — plane 도메인 규칙 누수 강화

- 기존 패턴(특정 문자열 3건) → 도메인 enum 직접 정의, 비즈니스 상수 패턴으로 확대
- `class \w+(Status|Type|Category)\(.*Enum\)`, 매직넘버 비즈니스 상수 패턴 추가

---

## 구현 Phase

### Phase 1 — 규칙 확장 (T1-1, T1-2)

**T1-1.** `scripts/dev/check_layer_boundaries.py`에 4개 규칙 추가 + OE101 패턴 확대

```python
# 테스트 먼저
def test_all_new_rules_exist():
    from scripts.dev.check_layer_boundaries import RULES
    for rule_id in ["OE102-plane-business-logic",
                    "OE301-service-cross-import",
                    "OE401-core-domain-logic"]:
        assert rule_id in RULES
```

**T1-2.** `--update-baseline` 실행 → 신규 규칙 포함 현재 위반 수 기록

```python
def test_baseline_includes_new_rules():
    import json
    baseline = json.loads(Path(".arch-baseline.json").read_text())
    for key in ["OE102-plane-business-logic", "OE301-service-cross-import", "OE401-core-domain-logic"]:
        assert key in baseline
```

---

### Phase 2 — baseline 재설정 (T2-1)

**T2-1.** `--check` 모드가 baseline 초과 시 즉시 실패함을 검증

```python
def test_check_mode_exits_nonzero_on_regression(tmp_path, monkeypatch):
    # 인위적으로 위반 1건 추가 후 --check 실행 시 exit code != 0 확인
    ...
```

---

### Phase 3 — 위반 소거 (T3-1, T3-2, T3-3)

**T3-1. OE101/OE102 — plane 위반 소거**

- 위반 파일 특정 후 로직을 해당 도메인 `services/` 로 이동
- plane에 남는 것: mount 호출, health 엔드포인트, 라우터 등록만
- 커밋 후 `uv run python scripts/dev/check_layer_boundaries.py --update-baseline`

**T3-2. OE301 — services 크로스 import 소거**

- 직접 import → `EventBus.publish()` 또는 `oneerp-core` 공용 DTO로 교체
- 도메인 간 공유 데이터가 필요한 경우 `core/oneerp_core/` 공용 계약 타입으로 승격

**T3-3. OE401 — core 도메인 로직 이관**

- `core/oneerp_core/pricing_rule.py` → `services/finance/accounting/` 또는 `services/sales/selling/`
- `core/oneerp_core/valuation/` → `services/scm/stock/` 등 해당 도메인
- 이관 후 core import 경로 교정 (기존 참조는 re-export 없이 직접 수정)

---

### Phase 4 — 제로 고정 (T4-1, T4-2)

**T4-1.** `--enforce-zero` 옵션 추가: baseline 항목 중 0 초과 시 즉시 실패

```python
def test_baseline_all_zero():
    import json
    baseline = json.loads(Path(".arch-baseline.json").read_text())
    assert all(v == 0 for v in baseline.values()), f"비제로 항목: {baseline}"
```

**T4-2.** `core/.gitea/workflows/ci.yml`에 enforce-zero 스텝 추가

```yaml
- name: 경계 규칙 제로 게이트
  run: uv run python scripts/dev/check_layer_boundaries.py --enforce-zero
```

---

## 전체 태스크 순서

```
T1-1 규칙 추가
  → T1-2 baseline 기록
    → T2-1 check 모드 검증
      → T3-1 plane 위반 소거
      → T3-2 cross-import 소거   (T3-1과 병렬 가능)
      → T3-3 core 이관           (T3-1과 병렬 가능)
        → T4-1 baseline=0 잠금
          → T4-2 CI 게이트 강화
```

**총 8 태스크.** 각 태스크는 "테스트 실패 확인 → 최소 구현 → 테스트 통과 → 커밋" 사이클을 따른다.

---

## 성공 기준 요약

1. **경계 위반 제로:** `check_layer_boundaries.py --enforce-zero` 전체 통과
2. **단방향 의존성:** OE301 = 0, 역방향 import 없음
3. **테스트 독립성:** 각 레이어가 다른 레이어 없이 단독 pytest 통과
4. **CI 게이트 잠금:** 이후 PR에서 위반 추가 불가능

---

## 영향받는 파일

| 파일 | 변경 유형 |
|------|-----------|
| `scripts/dev/check_layer_boundaries.py` | 규칙 4개 추가, `--enforce-zero` 옵션 |
| `.arch-baseline.json` | 신규 규칙 키 추가 → Phase 4에서 전부 0 |
| `core/oneerp_core/pricing_rule.py` | 도메인 서비스로 이관 |
| `core/oneerp_core/valuation/` | 도메인 서비스로 이관 |
| `planes/*/` (위반 파일) | 비즈니스 로직 → services 이동 |
| `services/` (크로스 import) | EventBus/공용 DTO로 교체 |
| `core/.gitea/workflows/ci.yml` | enforce-zero 스텝 추가 |
| `tests/unit/test_check_layer_boundaries.py` | 신규 규칙 + enforce-zero 테스트 |
