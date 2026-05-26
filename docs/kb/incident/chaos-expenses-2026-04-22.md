---
chaos_id: chaos-expenses-2026-04-22
module: expenses
severity: P2-simulated
conducted_at: 2026-04-22T05:30:00Z
duration_minutes: 13
type: chaos-engineering
---

# chaos-expenses-2026-04-22 — fraud pipeline 지연

## 가설

fraud-detection 배치 지연 시 auto_approval_threshold 임시 강화가
의심 건의 자동 승인 유입을 차단한다.

## 주입

fraud-detection cron pod crash 시뮬 (3시간 지연).

## 관측

- threshold 자동 강화: $500 → $100.
- 자동 승인 감소: 142 → 38 건/시간.
- 수동 재심사 큐 평균 대기: 2.1시간.

## 결론

- 보호 메커니즘 정상 ✓
- 수동 재심사 부하 허용 범위.

## 개선

- threshold 자동 강화는 CRD 관리로 전환 (현재 수동 kubectl patch).
