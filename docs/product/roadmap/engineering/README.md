---
owner: Engineering Lead
last_updated: 2026-04-16
stale_after_days: 60
audience: engineering
---

# Engineering 실행 레이어 진입점

> 이 디렉토리는 작업 흐름 1~7과 모듈 집단 1~4를 교차시켜 **"내 모듈 지금 어디 막혀있나"** 에 답한다.

## 1. 주 동선

**모듈 집단(Wave)** 을 루트로, **작업 흐름(Phase)** 은 횡단 시간축으로. 각 모듈 집단 문서에 해당 시점에 활성인 작업 흐름이 명시된다.

- 활성 모듈 집단부터 읽는다 → [waves/](./waves/)
- 시간축 횡단 뷰 → [phase-timeline.md](./phase-timeline.md)

## 2. 작업 흐름 × 모듈 집단 진입 지도

<!-- status-auto-embed:matrix -->
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
<!-- /status-auto-embed:matrix -->

각 Wave 상세: [W1](./waves/wave-1.md) · [W2](./waves/wave-2.md) · [W3](./waves/wave-3.md) · [W4](./waves/wave-4.md)

## 3. 이 레이어의 규약

- **수치·상태는 [../status.md](../status.md) 한 곳에만 있다.** 각 문서는 섹션 주석으로 임베드한다.
- **품질 기준 정의는 [../gates/README.md](../gates/README.md) 와 [ADR-0001](../../../governance/adr/0001-commercial-grade-definition.md) 에만 있다.**
- **작업 흐름 상세 계획은 `.planning/phases/0N-*/PLAN.md` 에만 있다.** 여기는 링크만.
- 각 모듈 집단 문서의 **"What done looks like"** 섹션에는 로컬에서 재현 가능한 명령만 넣는다.

## 4. 주요 링크

- [모듈 집단 1 재무·운영 핵심](./waves/wave-1.md)
- [모듈 집단 2 운영 확산](./waves/wave-2.md)
- [모듈 집단 3 지원·전문](./waves/wave-3.md)
- [모듈 집단 4 차별화](./waves/wave-4.md)
- [작업 흐름 1~7 횡단 시간축](./phase-timeline.md)
- [품질 기준 5 영역 23 기준](../gates/README.md)
- [4축 좌표계 정의](../matrix.md)

## 5. 어휘 주의

이 레이어는 Engineering 어휘를 쓴다. Executive 쪽 언어는 [../overview.md](../overview.md) 로 분리된다. CI (`scripts/roadmap/forbidden_terms.py`) 가 두 레이어의 어휘 번짐을 차단하며, 허용된 번역 매핑은 [../translation.md](../translation.md) 에 있다.
