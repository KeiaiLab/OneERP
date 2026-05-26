---
module: projects
baseline_date: 2026-04-22
load_tool: k6
---

# projects 부하 baseline

## 시나리오

- 100 rps × 10분, WBS 조회 + 타임시트 쓰기 + SLA 집계.

## 측정

| 지표 | 값 |
|---|---:|
| WBS 트리 조회 p95 | 320ms (깊이 5) |
| WBS 트리 조회 p95 (깊이 7) | 1.1s |
| 타임시트 쓰기 p95 | 160ms |
| SLA 집계 배치 | 18s (전 프로젝트) |

## 임계

- WBS 깊이 7 p95 > 1.3s: 인덱스 점검.
- SLA 집계 > 25s: 증분 계산 도입.
