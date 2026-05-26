---
owner: Engineering Lead
last_updated: 2026-04-16
stale_after_days: 2
generated_at: 2026-04-16T09:55:37Z
audience: shared
---

# 로드맵 상태 보드

> 자동 섹션은 `scripts/roadmap/status_render.py` 가 생성한다. 수동 편집 금지.
> 수동 섹션은 주 1회 (엔지니어링) / 월 1회 (Executive) 갱신한다.

---

<!-- status-auto:active -->
- 활성 작업 흐름: **1 — 이벤트 체인 안정화**
- 활성 모듈 집단: **Wave 1**
<!-- /status-auto:active -->

## [자동] 활성 작업 흐름 · 모듈 집단

_`scripts/roadmap/status_render.py` 실행 전. 최초 렌더 대기._


<!-- status-auto:gate-distribution -->
| 라벨 | 모듈 수 |
|------|---------|
| alpha | 46 |
| beta | 1 |
| pre-commercial | 0 |
| commercial-ready | 0 |
<!-- /status-auto:gate-distribution -->

## [자동] 23 품질 기준 진행률 분포

_`docs/generated/commercial-status.md` 요약 대기._


<!-- status-auto:wave-entry -->
| 집단 | 총 | pre-commercial+ | commercial-ready | 진입 | 완료 |
|------|-----|-----------------|-------------------|------|------|
| Wave 1 | 12 | 0/12 | 0/12 | ✅ | ❌ |
| Wave 2 | 13 | 0/13 | 0/13 | ⏳ | ❌ |
| Wave 3 | 14 | 0/14 | 0/14 | ⏳ | ❌ |
| Wave 4 | 8 | 0/8 | 0/8 | ⏳ | ❌ |
<!-- /status-auto:wave-entry -->

## [자동] 모듈 집단 진입·완료 상태

_`docs/generated/wave-status.md` 요약 대기._


<!-- status-auto:matrix -->
| 작업 흐름 \ 집단 | W1 (12) | W2 (13) | W3 (14) | W4 (8) |
|---|---|---|---|---|
| P1 | 54/72 | 59/78 | 57/84 | 32/48 |
| P2 | 10/24 | 7/26 | 8/28 | 5/16 |
| P3 | 5/12 | 9/13 | 4/14 | 3/8 |
| P4 | 0/12 | 0/13 | 0/14 | 0/8 |
| P5 | 48/72 | 52/78 | 56/84 | 32/48 |
| P6 | 0/48 | 0/52 | 0/56 | 0/32 |
| P7 | 0/36 | 0/39 | 0/42 | 0/24 |

_셀 = 해당 Phase 게이트 × 해당 Wave 모듈의 통과/대상. 출처: scripts/audit/commercial_readiness.py GATE_PHASE × WAVES_BY_MODULE._
<!-- /status-auto:matrix -->

## [자동] 작업 흐름 × 모듈 집단 매트릭스

_matrix.md 의 수치 셀 자동 채움 대기._


<!-- status-auto:progress -->
**441 / 1081** = **40.8%**  (Σ g(m) / 1081)
<!-- /status-auto:progress -->

## [자동] 전체 상용화 진행률

_Σ g(m) / (47 × 23) = Σ g(m) / 1,081 계산 대기._


<!-- status-auto:next-gate -->
- 내부 태그: `G1.W1.K03`
- 조건: 활성 집단 전 모듈의 이벤트 체인 일관성 확보
- 증거: `scripts/audit/commercial_readiness.py --module <mod>` 통과
<!-- /status-auto:next-gate -->

## [자동] 다음 게이트 바스켓

_가장 가까운 게이트 바스켓 자동 주입 대기._


<!-- status-auto:executive-one-line -->
**활성 Wave 1 · 1 — 이벤트 체인 안정화 · 전체 진행률 40.8% (441/1081)**
<!-- /status-auto:executive-one-line -->

## [자동] Executive 한 줄

_overview.md · README.md 가 임베드하는 한 줄. 자동 작성 대기._

<!-- status-auto:release-rehearsal -->
- 최근 출시급 실측: 미실행
- 근거: `artifacts/rehearsal/latest/` (미생성)
<!-- /status-auto:release-rehearsal -->

## [자동] 출시 리허설 상태

_`artifacts/rehearsal/latest/` 요약 대기._

<!-- status-auto:blockers -->
- 상태 원문: Pre-Loop Cleanup 완료 · 다음 단계는 전체 상용 기준 루프 기동
- 판정: 블로커 0건
- 마지막 갱신: 2026-04-16T09:47:16Z
- 근거: `HANDOFF.md`
<!-- /status-auto:blockers -->

## [자동] 정지 조건 상태

_`HANDOFF.md` 기반 활성 블로커 요약 대기._


---

<!-- status-manual:weekly-eng -->
## [수동 · 주 1회] 이번 주 엔지니어링 하이라이트

_(월요일 3줄 갱신. 작성자: Engineering Lead)_

- 초기 렌더 전. 스크립트 구현 완료 후 최초 기입.
<!-- /status-manual:weekly-eng -->

<!-- status-manual:monthly-exec -->
## [수동 · 월 1회] 이번 월 Executive 요약

_(월초 3줄 갱신. 작성자: PM. overview.md 가 이 섹션을 자동 임베드)_

- 초기 렌더 전. 스크립트 구현 완료 후 최초 기입.
<!-- /status-manual:monthly-exec -->

<!-- status-manual:risks-top3 -->
## [수동 · 월 1회] 상위 리스크 Top 3

_(상위 3건 + 대응 1줄. `.planning/program/risks/RISK-REGISTER.md` 발췌)_

- 초기 렌더 전.
<!-- /status-manual:risks-top3 -->

---

## 운영 규칙

- 자동 섹션이 7일 이상 갱신되지 않으면 상단 **STALE 배너**가 자동 주입된다.
- 수동 엔지 섹션 10일, Executive 섹션 35일도 동일 규칙.
- 자동 섹션을 손으로 수정하지 말 것 — 다음 렌더에서 덮어씌워진다.
- 수동 섹션의 섹션 주석(`status-manual:*`)은 지우지 말 것 — 렌더러가 보존 경계로 사용한다.
