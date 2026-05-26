---
module: stock
baseline_date: 2026-04-22
load_tool: k6
---

# stock 부하 baseline

## 시나리오

- 800 rps × 10분, movement 기록 50% + 잔고 조회 40% + reservation 10%.

## 측정

| 지표 | 값 |
|---|---:|
| movement 쓰기 p95 | 150ms |
| 잔고 조회 p95 | 85ms |
| reservation p95 | 210ms |
| 동시 reservation 경합 비율 | 2.1% |
| RSS | 290MB |

## 임계

- movement p95 > 172ms: 인덱스 재구성.
- reservation 경합 > 3%: 분산 락 튜닝.

## 특이사항

- 대형 SKU 에서 reservation 경합 집중 — shard 고려.
