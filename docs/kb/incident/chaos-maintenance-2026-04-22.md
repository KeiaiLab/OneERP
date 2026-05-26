---
chaos_id: chaos-maintenance-2026-04-22
module: maintenance
severity: P2-simulated
conducted_at: 2026-04-22T06:45:00Z
duration_minutes: 14
---

# chaos-maintenance-2026-04-22 — iot 센서 연결 끊김

## 가설
iot 게이트웨이 30분 단절 시 maintenance 가 예측 PM 파이프라인 stale 상태로 감지.

## 주입
iot 연결 toxiproxy 로 100% 차단 30분.

## 관측
- PM 예측 stale flag 자동 활성화.
- 설비 다운 경보 수동 보정으로 전환.
- 연결 복구 후 자동 resume.

## 결론
iot 의존성 자동 fallback 정상.
