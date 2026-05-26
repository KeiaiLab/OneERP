---
chaos_id: chaos-selling-2026-04-22
module: selling
severity: P2-simulated
conducted_at: 2026-04-22T04:15:00Z
duration_minutes: 18
type: chaos-engineering
---

# chaos-selling-2026-04-22 — PG 타임아웃 연쇄

## 가설

외부 PG-A 응답 p95 8s 지연 시 A/B 스위치로 주문 완료 성공률 유지.

## 주입

toxiproxy 로 PG-A 에 가중치 latency 추가 (p95 target 8s).

## 관측

- PG-A 에서 주문 완료 시도: 65% (타임아웃 35%).
- PG-B 전환 후: 성공률 99.1%.
- backorder 큐 사용: 0건 (A/B 전환이 먼저).

## 결론

- A/B 스위치 정상 ✓
- 전환 조건(3회 연속 timeout)이 12초 → 개선 여지.

## 개선

- 전환 조건 임계치를 3회 → 5회로 (false-positive 감소) vs 12초 → 6초 (속도 우선) 선택 필요.
