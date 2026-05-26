---
module: buying
baseline_date: 2026-04-22
load_tool: k6
---

# buying 부하 baseline

## 시나리오

- 150 rps × 10분, PO 조회 + 승인 체인 진행 + 입고 등록.

## 측정

| 지표 | 값 |
|---|---:|
| PO 조회 p95 | 110ms |
| 승인 체인 진행 p95 | 180ms |
| 입고 등록 p95 (stock 연동 포함) | 290ms |
| RSS | 220MB |

## 임계

- 입고 등록 p95 > 333ms: stock API 또는 3-way match 지연.
