---
module: directory
baseline_date: 2026-04-22
load_tool: k6
---

# directory 부하 baseline

## 시나리오

- target: 500 rps (인증 중심) × 10분.
- 90% SSO flow, 10% org tree 쿼리.

## 측정

| 지표 | 값 |
|---|---:|
| p95 | 140ms |
| p99 | 280ms |
| SSO p95 | 260ms (metadata URL 포함) |
| RSS | 280MB |
| CPU | 25% |

## 임계

- p95 > 161ms: 회귀.
- SSO p95 > 300ms: dual-read 점검.

## 특이사항

- organization_unit 깊이 6+ 에서 DFS 2.5ms → 8ms 선형 증가 관찰.
- Wave2 전 인덱스 최적화 필요.
