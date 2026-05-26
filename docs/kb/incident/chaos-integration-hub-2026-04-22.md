---
chaos_id: chaos-integration-hub-2026-04-22
module: integration-hub
severity: P2-simulated
conducted_at: 2026-04-22T07:45:00Z
duration_minutes: 15
---

# chaos-integration-hub-2026-04-22 — 외부 커넥터 응답 5xx

## 가설
특정 커넥터 5xx 폭주 시 circuit breaker 가 30초 내 열려 큐 오버플로 방지.

## 주입
mock 외부 API 에 100% 500.

## 관측
- circuit breaker 28초 후 open.
- 재시도 큐 성장률 대폭 감소.
- 복구 후 half-open 적용.

## 결론
circuit breaker 설계 정상.
