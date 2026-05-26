---
module: integration-hub
baseline_date: 2026-04-22
---

# integration-hub 부하 baseline

## 시나리오
100 커넥터 × 평균 50 메시지/s, circuit breaker 반복 테스트.

## 측정
| 지표 | 값 |
|---|---:|
| 메시지 변환 p95 | 42ms |
| 재시도 큐 drain time | 12s |
| circuit breaker open → half-open | 28s |

## 임계
- 변환 p95 > 48ms: 스키마 복잡도 검토.
