---
chaos_id: chaos-subscriptions-2026-04-22
module: subscriptions
severity: P2-simulated
conducted_at: 2026-04-22T07:30:00Z
duration_minutes: 11
---

# chaos-subscriptions-2026-04-22 — dunning 파이프라인 지연

## 가설
결제 실패 구독에 대한 dunning 이메일이 3일간 지연 발송돼도 강제 해지 전.

## 주입
dunning cron 72h 중단.

## 관측
- 강제 해지 0건 (SLA 유효).
- 복구 후 일괄 발송 정상.

## 결론
여유 시간(72h) 충분. SLA 위반 경계 강화 필요.
