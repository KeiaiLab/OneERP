---
incident_id: INC-2026-04-21-gateway-drill
severity: P1 (simulated)
status: resolved
detected_at: 2026-04-21T09:00:00Z
resolved_at: 2026-04-21T09:38:00Z
module: gateway
type: drill
drill_gate: G4-5
related: docs/ops/drills/G4-5/2026-04-21-gateway.md
---

# INC-2026-04-21 — gateway drill (G4-5 On-call 응답 훈련)

## 요약

`gateway` 모듈의 `/health` 가 30초 이상 5xx 를 반환하는 P1 인시던트를 모의 주입하고
On-call 응답 체인 (Alertmanager → PagerDuty → primary on-call @phil) 을 검증했다.

## 타임라인 (UTC)

| 시각 | 이벤트 |
|------|--------|
| 09:00:00 | `scripts/chaos/fault-inject.sh gateway --kind 5xx --duration 5m` 시작 |
| 09:00:42 | Prometheus `oneerp_gateway_http_5xx_total` 임계 초과 |
| 09:01:12 | Alertmanager → PagerDuty `oneerp-gateway-oncall` 페이지 발송 |
| 09:03:12 | @phil 응답(MTTA 3m12s) — `#inc-gateway-2026-04-21` 자동 생성 |
| 09:05:00 | 플레이북 §2.3 "격리" 수행: `gateway-canary` 로 트래픽 50% 우회 |
| 09:09:00 | chaos 주입 자동 해제, 주요 API 5xx 0건 확인 |
| 09:11:00 | 트래픽 원복, p95 180ms 회귀 |
| 09:35:00 | incident 공식 resolve 선언 |
| 09:38:00 | blameless 회고 작성 완료 |

## 증거

- **MTTA 3m12s** — PagerDuty audit log 발췌 (SLO ≤ 5분 충족).
- **MTTR 26m**  — chaos 중단~resolve 선언 구간, SLO P1 ≤ 30분 충족.
- chaos 도구: [`scripts/chaos/fault-inject.sh`](../../../scripts/chaos/fault-inject.sh)
- 플레이북: [`docs/ops/runbook-incident-response.md`](../../ops/runbook-incident-response.md)

## 개선 항목

1. incident 채널의 첫 상태 업데이트가 8분 지연 (권장 ≤ 5분).
   → 플레이북에 "5분 자동 리마인더 봇" 추가 예정.
2. Escalation 2차(@backup-oncall) 가 트리거되지 않은 것은 정상 — 이번 드릴은 primary 응답 검증.
3. PagerDuty 수신 지연이 관측되지 않아 네트워크 경로는 양호.

## 다음 드릴

- 2026-07-21 (분기 순환)
- 2차 on-call 응답 경로 주입 시나리오 추가 예정 (primary 무응답 시뮬레이션)
