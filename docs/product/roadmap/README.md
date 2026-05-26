---
owner: Product Lead
last_updated: 2026-04-16
stale_after_days: 30
audience: executive
---

# OneERP 상용화 로드맵

> **Executive 30초 랜딩** — 지금 어디, 다음은 무엇, 최종은 무엇.

## 1. 지금 어디 있는가 (Now)

<!-- status-auto-embed:active -->
- 활성 작업 흐름: **1 — 이벤트 체인 안정화**
- 활성 모듈 집단: **Wave 1**
<!-- /status-auto-embed:active -->

## 2. 다음 중요한 한 걸음 (Next)

<!-- status-auto-embed:next-gate -->
- 내부 태그: `G1.W1.K03`
- 조건: 활성 집단 전 모듈의 이벤트 체인 일관성 확보
- 증거: `scripts/audit/commercial_readiness.py --module <mod>` 통과
<!-- /status-auto-embed:next-gate -->

## 3. 출시 리허설 상태

<!-- status-auto-embed:release-rehearsal -->
- 최근 출시급 실측: 미실행
- 근거: `artifacts/rehearsal/latest/` (미생성)
<!-- /status-auto-embed:release-rehearsal -->

## 4. 정지 조건 상태

<!-- status-auto-embed:blockers -->
- 상태 원문: Pre-Loop Cleanup 완료 · 다음 단계는 전체 상용 기준 루프 기동
- 판정: 블로커 0건
- 마지막 갱신: 2026-04-16T09:47:16Z
- 근거: `HANDOFF.md`
<!-- /status-auto-embed:blockers -->

## 5. 최종 상태 (Destination)

v1.0 파일럿 출시 = **v1.0 프로그램 7개 작업 흐름 완결** + **재무·운영 핵심 12 모듈 commercial-ready**
전체 상용 = **47 모듈 × 23 품질 기준 전수 통과** (상세는 `gates/` 참조)

## 6. 축별 진입점

| 축 | 진입점 | 질문 |
|---|---|---|
| 시간 / 작업 흐름 | [engineering/phase-timeline.md](./engineering/phase-timeline.md) | 이번에 어떤 벽을 깨고 있는가 |
| 모듈 우선순위 | [engineering/waves/](./engineering/waves/) | 누가 먼저 출시 자격을 얻는가 |
| 4축 좌표계 | [matrix.md](./matrix.md) | 지금 어디에 서 있는가 |
| 품질 기준 | [gates/README.md](./gates/README.md) | 출시 완료의 정의는 무엇인가 |
| 어휘 번역 | [translation.md](./translation.md) | Executive와 실행 팀의 용어 지도 |

## 7. 참조 규약

이 디렉토리는 **지도**다. 원본은 `.planning/`, `docs/governance/adr/`, `.planning/strategy/` 에 있고, 수치는 `status.md` 한 곳에만 있다.
