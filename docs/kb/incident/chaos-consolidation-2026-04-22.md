---
chaos_id: chaos-consolidation-2026-04-22
module: consolidation
severity: P2-simulated
conducted_at: 2026-04-22T07:00:00Z
duration_minutes: 15
---

# chaos-consolidation-2026-04-22

## 가설
consolidation 모듈이 주요 실패 모드에서 degraded 모드로 안전 전환된다.

## 주입
scripts/chaos/fault-inject.sh consolidation --kind latency --duration 5m --namespace services-staging

## 관측
- p95 허용 범위 내 상승.
- consumer backpressure 정상.
- 복구 후 원상 복귀.

## 결론
기본 내성 정상. 특화 시나리오는 후속 iter.

## 참조
- 런북: docs/ops/runbook-incident-response.md
