# ADR-0013: 상용 게이트 드릴 증거 규약

- 상태: Proposed
- 날짜: 2026-04-21
- 작성자: @phil
- 관련: ADR-0001(상용 게이트 정의), ADR-0009(백업·복구 RPO/RTO),
  ADR-0010(배포 파이프라인 표준), ADR-0015(경계 가드레일)

## 1. 맥락(Context)

ADR-0001 §6.4 는 G4-3(백업·복구), G4-4(롤백), G4-5(On-call) 에 대해
각각 "실제 복구 시뮬레이션", "스테이징 롤백 시뮬레이션 통과",
"사고 분류·심각도 매핑" 을 요구한다. 그러나 `scripts/audit/commercial_readiness.py`
의 기존 구현은 런북 파일 크기(>500B) 존재 여부만 검사해 47 모듈 전수
100% PASS(3×47=141 셀)를 자가 신고해 왔다.

이 자가 신고는 `docs/product/roadmap/status.md` 의 전체 진행률(441/1,081 =
40.8%) 을 실제보다 약 13% 포인트 과대 집계해, "자가 신고 게이트"와 "실증
게이트" 를 같은 통계로 합산하는 근본 모순을 만든다. Ralph-Loop 이 후속
640 셀을 진전시키더라도 이 141 셀이 자가 신고인 한 최종 "commercial-ready"
선언이 허위가 될 수 있다.

## 2. 결정(Decision)

G4-3/4/5 의 PASS 판정은 **런북 존재 AND 해당 모듈의 최근 드릴 기록**
두 조건을 모두 만족할 때만 내린다. 드릴 기록은 다음 규약을 따른다:

- 경로: `docs/ops/drills/<gate-id>/<YYYY-MM-DD>-<module>.md`
- 프론트매터 필수 필드: `gate`, `module`, `drill_date`
- 유효 기간: 오늘 기준 **90일** 이내 (상수
  `commercial_readiness.DRILL_MAX_AGE_DAYS`)

판정 전이:

| 런북 | 최근 드릴 | 판정 |
|---|---|---|
| 없음 | - | FAIL |
| 존재 | 없음 | **NOT_IMPLEMENTED** |
| 존재 | 90일 이내 | PASS |
| 존재 | 90일 초과 | NOT_IMPLEMENTED |

NOT_IMPLEMENTED 는 라벨 승급을 막지 않지만(ADR-0001 §7) PASS 수에도
들어가지 않아 통계 왜곡을 차단한다.

## 3. 대안(Alternatives Considered)

### 대안 A — 드릴 증거 없을 때 FAIL 처리
- 장점: 가장 엄격.
- 단점: 현재 "drill 인프라 자체가 미정의" 인 상태에서 FAIL 을 47×3=141건
  쏟아내면 모듈 오너 피로가 높고, 실제 결함(코드 미구현)과 "드릴 미실시"
  를 구분할 수 없다.
- 불채택: 상태 레이어(FAIL vs NOT_IMPLEMENTED)를 분리해 진단하는 것이
  운영 관점에서 낫다.

### 대안 B — 감사 스크립트는 그대로 두고 외부 체크리스트만 추가
- 장점: 코드 변경 없음.
- 단점: `scripts/audit/commercial_readiness.py` 가 SoT(Single Source of Truth)인
  체계에서, SoT 밖 규약은 곧바로 사문화된다.
- 불채택.

### 대안 C — 본 결정(상태 레이어 + 파일 규약)
- 채택. 코드 한 곳(`_has_recent_drill`)과 문서 디렉토리(`docs/ops/drills/`)
  두 개만 SoT 로 둔다.

## 4. 근거(Rationale)

- 라벨 승급 정책(ADR-0001 §7)은 "passed count" 로만 판정하므로, PASS→
  NOT_IMPLEMENTED 전이는 과대 집계분을 정직하게 깎는다.
- 90일 기준은 ADR-0009(백업 RPO/RTO)와 분기 회고 주기(ADR-0001 §9)에
  부합한다. 분기마다 최소 1회 드릴이 돌면 항상 유효.
- 상용 게이트는 "얻는 것"이 아니라 "유지되는 것"이어야 한다. 시간 기반
  만료는 라벨의 신뢰성을 유지하는 유일한 메커니즘.

## 5. 영향(Consequences)

### 5.1 긍정적
- `docs/product/roadmap/status.md` 의 진행률이 자가 신고분을 제거한 실수치가
  된다(예상: 441 → ≈300, 약 -13pp).
- 드릴 기록이 운영 지식 베이스(`docs/ops/drills/`)로 축적되어 신입 오너
  온보딩 재료로 쓰인다.

### 5.2 부정적 / 리스크
- 기존 "commercial-ready" 에 근접한 모듈이 있었다면 일시적으로 라벨
  하락. 단, 현재 시점 commercial-ready=0 이므로 실제 하락 위험은 라벨이
  아닌 "pass count 감소" 뿐.
- 드릴 자동화(PagerDuty, 복구 자동화)가 정비되지 않은 영역은 수동 드릴
  기록 부담이 생김.

### 5.3 마이그레이션
- 본 ADR 머지 즉시 감사 스크립트가 NOT_IMPLEMENTED 로 전환. 별도 데이터
  마이그레이션 없음.
- 선제 드릴 기록이 필요하면 `docs/ops/drills/README.md` 의 템플릿으로
  개별 모듈이 추가.

### 5.4 측정 지표
| 지표 | 적용 전 | 적용 직후 기대치 | 측정 |
|---|---|---|---|
| G4-3/4/5 PASS 합 | 141 | 0 | `commercial_readiness.py --format json` |
| 전체 진행률 | 441/1081 (40.8%) | ≈300/1081 (≈27.8%) | 동일 |
| 드릴 등록 모듈 수 | 0/47 | 분기당 +N | `ls docs/ops/drills/G4-*/` |

## 6. 구현 상태

- [x] 스크립트 헬퍼 `_has_recent_drill(gate_id, module)` — `scripts/audit/commercial_readiness.py`
- [x] 상수 `DRILL_ROOT`, `DRILL_MAX_AGE_DAYS`
- [x] 게이트 판정 전이 — G4-3/4/5 세 함수
- [x] 단위 테스트 — `tests/unit/test_commercial_readiness_drill_evidence.py` (10 케이스)
- [x] 드릴 템플릿 · 규약 문서 — `docs/ops/drills/README.md`
- [ ] 최초 드릴 기록 수립 (웨이브 1 12모듈 우선) — 후속 운영 작업

## 7. 검증(Verification)

```bash
uv run --package oneerp-core pytest tests/unit/test_commercial_readiness_drill_evidence.py
uv run --package oneerp-core python3 scripts/audit/commercial_readiness.py --format summary
# 기대: pass count 가 이전 대비 141 감소, 47 모듈 전부 impl=20/23
```
