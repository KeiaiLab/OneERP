---
chaos_id: chaos-assets-2026-04-22
module: assets
severity: P2-simulated
conducted_at: 2026-04-22T06:30:00Z
duration_minutes: 10
---

# chaos-assets-2026-04-22 — 감가상각 배치 실패

## 가설
월말 depreciation cron pod crash 시 수동 재실행으로 SLA 유지.

## 주입
cron pod kill 20분.

## 관측
- accounting 재공품 journal 지연 20분.
- 수동 재실행 후 정상.

## 결론
cron high-availability 고려 필요 (현재 단일).
