---
module: manufacturing
baseline_date: 2026-04-22
---

# manufacturing 부하 baseline

## 시나리오
200 rps × 10분. MRP 일괄 계산 + 작업 지시 상태 업데이트.

## 측정
| 지표 | 값 |
|---|---:|
| API p95 | 180ms |
| MRP 일괄 (1000 BOM) | 72s |
| 작업지시 업데이트 p95 | 140ms |
| RSS | 310MB |

## 임계
- MRP p95 > 207ms 회귀.
- MRP 일괄 > 90s: 재귀 캐시 점검.
