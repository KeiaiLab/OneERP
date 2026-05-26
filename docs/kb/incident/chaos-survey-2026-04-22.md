---
chaos_id: chaos-survey-2026-04-22
module: survey
severity: P3-simulated
conducted_at: 2026-04-22T09:00:00Z
duration_minutes: 7
---

# chaos-survey-2026-04-22 — 대규모 응답 러시 대응

## 가설
NPS 조사 발송 직후 10분간 응답 2000 건 버스트에서 API 유지.

## 주입
k6 로 burst 2000 rps 10분.

## 관측
- API p95 580ms (허용 < 1s).
- DB 쓰기 queue 최대 depth 320.
- drop 0건.

## 결론
burst 수용 정상.
