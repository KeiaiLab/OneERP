---
module: portal
baseline_date: 2026-04-22
load_tool: lighthouse
---

# portal 부하 baseline (Core Web Vitals 포함)

## 시나리오

- 로그인 → 대시보드 렌더 → 알림 센터 조회.
- 접속자 500 동시, 5분.

## 측정

| 지표 | 값 |
|---|---:|
| First Contentful Paint | 1.2s |
| Largest Contentful Paint | 2.1s |
| Time to Interactive | 2.6s |
| Cumulative Layout Shift | 0.02 |
| Total Blocking Time | 180ms |

## 임계

- LCP > 2.5s: 회귀.
- TBT > 250ms: 번들 분석.

## 특이사항

- CDN edge 경로 평균 45ms, origin 직통은 160ms.
