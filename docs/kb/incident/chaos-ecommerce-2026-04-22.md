---
chaos_id: chaos-ecommerce-2026-04-22
module: ecommerce
severity: P1-simulated
conducted_at: 2026-04-22T07:00:00Z
duration_minutes: 16
---

# chaos-ecommerce-2026-04-22 — 장바구니 세션 소실

## 가설
Redis 세션 스토어 부분 장애 시 장바구니가 cookie fallback 으로 유지.

## 주입
Redis 50% 응답 실패.

## 관측
- cookie fallback 활성화.
- 체크아웃 성공률 유지 97%.
- 세션 복구 후 자동 정상.

## 결론
cookie fallback 정상 작동. 이탈율 영향 0.5%p.
