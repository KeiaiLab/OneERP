---
module: quality
baseline_date: 2026-04-22
---

# quality 부하 baseline

## 시나리오
100 rps × 10분. 검사 결과 쓰기 60% + 조회 40%.

## 측정
| 지표 | 값 |
|---|---:|
| 결과 쓰기 p95 | 120ms |
| 조회 p95 | 85ms |
| CAPA 생성 p95 | 210ms |

## 임계
- 결과 쓰기 > 138ms 회귀.
