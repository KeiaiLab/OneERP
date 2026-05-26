---
module: payroll
baseline_date: 2026-04-22
load_tool: k6
---

# payroll 부하 baseline

## 시나리오

- 월말 집행 시뮬: 5000 pay_slip 생성 + 은행 API 호출.
- 평상시 API: 50 rps (조회 위주).

## 측정

| 지표 | 값 |
|---|---:|
| pay_run 생성 (5000건) | 42s |
| 은행 API 호출 p95 | 820ms (외부 의존) |
| 조회 API p95 | 85ms |
| RSS | 310MB |
| CPU peak | 62% (생성 시) |

## 임계

- pay_run 생성 > 50s: 배치 크기 재검토.
- 은행 API p95 > 1.5s: A→B 전환 고려.

## 특이사항

- 월말 peak 과 평상시 load 차이 큼 — 오토스케일링 필수.
