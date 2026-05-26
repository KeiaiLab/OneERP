---
module: advanced-planning
baseline_date: 2026-04-22
load_tool: k6
---

# advanced-planning 부하 baseline

## 시나리오
일반 CRUD 부하 100 rps × 10분. 모듈 특화는 후속.

## 측정
| 지표 | 값 |
|---|---:|
| p95 | 180ms |
| p99 | 380ms |
| throughput | 98 rps |
| RSS | 280MB |

## 임계
- p95 > 207ms 회귀.
- RSS > 336MB (+20%) 회귀.

## 참조
- 회귀: scripts/perf/regression.py
