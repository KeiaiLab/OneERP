---
owner: Architecture Lead
last_updated: 2026-04-16
stale_after_days: 180
audience: shared
---

# 4축 좌표계 · 작업 흐름 × 모듈 집단 매트릭스

> 이 문서는 **구조와 정의**를 소유한다. 수치는 [status.md](./status.md) 에서만 살고, 여기에서는 `<!-- matrix-cell:... -->` 형태로 임베드된다.

## 1. 네 개의 축

| 축 | 단위 | 대표 질문 | 정본 |
|---|---|---|---|
| Phase (작업 흐름축) | 시간 · 시나리오 | 언제 어떤 벽을 깨는가 | [.planning/ROADMAP.md](../../../.planning/ROADMAP.md) |
| Wave (모듈 집단축) | 47 모듈의 분류 | 누가 먼저 출시 자격을 얻는가 | [docs/governance/adr/0012-commercialization-wave-mapping.md](../../governance/adr/0012-commercialization-wave-mapping.md) |
| Stream (가치축) | ERP / Groupware / AI | 누구에게 가치인가 (다중 라벨) | [.planning/strategy/](../../../.planning/strategy/) |
| Plane (런타임축) | API · Realtime · Worker · Scheduler · Edge · Extension | 어느 런타임으로 제공되는가 (다중 라벨) | [docs/governance/adr/0014-runtime-plane-decomposition.md](../../governance/adr/0014-runtime-plane-decomposition.md) |

## 2. 기본 조회 경로

`Phase → Wave → (Stream | Plane) 필터 → 모듈 → 품질 기준 상태`.

Phase 가 외부 커뮤니케이션과 1:1 대응되므로 첫 번째 조회 키. Stream·Plane 은 다중 라벨 필터.

## 3. 마일스톤 명명 체계

| 용도 | 표기 | 예시 | 의미 |
|---|---|---|---|
| 내부 · 자동화 친화 | `G<P>.W<W>.K<K>` | `G2.W1.K07` | 작업 흐름 2 × 모듈 집단 1 × 23 기준 중 7번 |
| 외부 · 이사회 친화 | `M1..Mn` | `M7` | 평탄 태그. 치환표는 [milestones.md](./milestones.md) |

## 4. 작업 흐름 × 모듈 집단 매트릭스 (7 × 4)

셀 형식: `(해당 Wave 모듈 중 이 Phase의 E2E·기준에 닿는 모듈 수 / Wave 총 모듈 수, 23 기준 평균 통과 수, 상태)`

범례: 🟢 완료 · 🟡 진행중 · ⚪ 준비됨 · ⚫ 미개시

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

## 5. 진행률 공식 (단일)

```
전체 상용화 진행률 = Σ (모듈 m 의 통과 23 기준 수) / (47 × 23) = Σ g(m) / 1,081
```

- Wave 별 진행률: 같은 식을 해당 Wave 모듈로 제한
- Phase 별 진행률: 같은 식을 해당 Phase 대상 기준으로 제한
- Stream 별 진행률: 같은 식을 Stream 라벨 모듈로 제한
- Plane 별 진행률은 별도 파생하지 않음. 필요 시 [engineering/waves/](./engineering/waves/) 의 Plane 태그로 조회.

## 6. 모듈 집단 경계 규칙

- 활성 Wave 는 항상 **1개**. (ADR-0002 단일 활성 모듈 집단 원칙)
- Wave N 의 **80% 이상 모듈이 23/23 기준 통과** 전에 Wave N+1 실행 자원 전환 금지.
- Wave 4의 전체 상용 완성은 **8 모듈 전부 23/23 기준 통과**로 판정한다.
- 선행 설계·기준 ADR 작성은 허용.
- Carry-over 허용 SLA = 2 분기. 초과 시 [ADR-0012](../../governance/adr/0012-commercialization-wave-mapping.md) 개정으로 재분류.

## 7. 로드맵 개정이 ADR 개정을 요구하는 경우

| 변경 | 요구 ADR 개정 |
|---|---|
| 모듈의 Wave 이동 | [ADR-0012](../../governance/adr/0012-commercialization-wave-mapping.md) 개정 |
| 모듈의 Plane 재지정 | [ADR-0014](../../governance/adr/0014-runtime-plane-decomposition.md) 개정 |
| 23 기준 정의 변경 | [ADR-0001](../../governance/adr/0001-commercial-grade-definition.md) 개정 |
| 단일 활성 Wave 해제 | [ADR-0002](../../governance/adr/0002-commercialization-waves.md) 개정 |
| 작업 흐름 순서·목표 변경 | `.planning/ROADMAP.md` + `v1.0-program.md` 동시 수정 |
| Stream 신설 | 신규 ADR 발의 |

## 8. 면책

**시간은 근사, 기준 통과가 진실이다.** 분기 대역은 외부 커뮤니케이션용 예상 구간이며, 모듈의 출시 자격은 23 품질 기준 통과로만 판정한다.
