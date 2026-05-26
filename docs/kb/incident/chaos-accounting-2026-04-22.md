---
chaos_id: chaos-accounting-2026-04-22
module: accounting
severity: P2-simulated
conducted_at: 2026-04-22T03:30:00Z
duration_minutes: 15
type: chaos-engineering
---

# chaos-accounting-2026-04-22 — NATS replay 부하

## 가설

이벤트 재적용 (replay) 중 GL 무결성 검증이 기능 중단 없이 수행.

## 주입

`scripts/ops/replay-events.sh --stream accounting-events --from T-30m --dry-run`
을 2회 중첩 실행 (peak load 시뮬).

## 관측

- journal_entries 쓰기 지연 p95: 85ms → 140ms.
- gl_integrity.py 는 정합 유지 (차대 일치 100%).
- period_close 작업은 일시 중단 권장 (replay 종료까지 대기).

## 결론

- 무결성 유지 ✓
- 중첩 replay 는 성능 저하 수반 — 직렬 권장.
