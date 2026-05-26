---
chaos_id: chaos-gateway-2026-04-22
module: gateway
severity: P1-simulated
conducted_at: 2026-04-22T03:00:00Z
duration_minutes: 12
type: chaos-engineering
---

# chaos-gateway-2026-04-22 — upstream cascade 시뮬레이션

## 가설

gateway 에서 단일 upstream 모듈 (selling) 응답 지연 시, 부하가 다른 upstream
으로 전파되지 않고 격리되는가.

## 주입

`scripts/chaos/fault-inject.sh selling --kind latency --duration 5m --namespace services-staging`

## 관측

- gateway p95: 180ms → 480ms (selling 호출 포함 요청만).
- 타 모듈 (accounting·buying·stock) p95: 190ms → 195ms (거의 무영향).
- 격리 성공. circuit breaker 가 5분 내 half-open 진입.

## 결론

- selling 전용 호출이 격리됨 ✓
- retry 폭주 없음 ✓

## 개선

- circuit breaker half-open 진입이 5분으로 느림 → 2분으로 단축 검토.
