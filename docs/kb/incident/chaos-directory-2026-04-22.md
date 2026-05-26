---
chaos_id: chaos-directory-2026-04-22
module: directory
severity: P1-simulated
conducted_at: 2026-04-22T03:15:00Z
duration_minutes: 10
type: chaos-engineering
---

# chaos-directory-2026-04-22 — SSO provider 응답 지연

## 가설

SSO provider 외부 응답이 느릴 때 dual-read fallback 이 사용자 영향 없이 작동.

## 주입

metadata URL 요청에 인위적 3s delay 추가 (toxiproxy).

## 관측

- 로그인 p95: 280ms → 320ms (fallback 동작).
- JWT 재발행 실패 0건 (기존 세션 유지).
- dual-read 로 inline XML 경로 성공.

## 결론

- fallback 메커니즘 정상 ✓
- 사용자 영향 거의 없음 (p95 +40ms).
