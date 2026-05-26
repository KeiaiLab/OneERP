---
chaos_id: chaos-portal-2026-04-22
module: portal
severity: P2-simulated
conducted_at: 2026-04-22T05:00:00Z
duration_minutes: 9
type: chaos-engineering
---

# chaos-portal-2026-04-22 — CDN 엣지 일시 장애

## 가설

CDN 504 에 대해 CDN 우회 쿠키 활성화 → origin 직통 경로가 30초 내 작동.

## 주입

Cloudflare worker 로 특정 리전 (seoul) 의 edge 에 504 주입.

## 관측

- 흰 화면 감지까지 7초.
- X-Portal-Bypass 쿠키 활성화 12초.
- origin 부하 +40% 급증, rate limit 은 유지.
- 5분 내 CDN 복구.

## 결론

- 우회 경로 정상 ✓
- origin 처리 한계 미도달.

## 개선

- origin 부하 급증 시 rate limit 자동 완화 (현재 수동).
