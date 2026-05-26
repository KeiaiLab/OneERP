---
module: survey
baseline_date: 2026-04-22
---

# survey 부하 baseline

## 시나리오
NPS 발송 직후 burst 2000 rps 10분.

## 측정
| 지표 | 값 |
|---|---:|
| 응답 쓰기 p95 | 180ms |
| dedup p95 | 45ms |
| NPS 집계 | 12s |

## 임계
- 응답 쓰기 > 207ms: DB 쓰기 큐 tune.
