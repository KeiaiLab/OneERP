---
module: selling
baseline_date: 2026-04-22
load_tool: k6
---

# selling 부하 baseline

## 시나리오

- 600 rps × 10분, SO 생성 30% + 조회 60% + 업데이트 10%.
- stock reservation 동시 연동.

## 측정

| 지표 | 값 |
|---|---:|
| SO 생성 p95 | 240ms (stock reserve 포함) |
| SO 조회 p95 | 130ms |
| PG 결제 호출 p95 | 680ms (외부) |
| RSS | 360MB |

## 임계

- SO 생성 p95 > 276ms: stock API 점검.
- PG p95 > 1.2s: A/B 스위치 검토.

## 특이사항

- stock reservation 동시 쓰기가 SO 생성 지연의 주요 원인.
