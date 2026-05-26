---
chaos_id: chaos-buying-2026-04-22
module: buying
severity: P2-simulated
conducted_at: 2026-04-22T04:30:00Z
duration_minutes: 14
type: chaos-engineering
---

# chaos-buying-2026-04-22 — 승인 체인 가짜 부결 주입

## 가설

L2 승인자가 부결 후 draft 재작성 시 체인 역진 없이 새 approval_chain 생성.

## 주입

PO 3건에 대해 L2 부결 이벤트 주입.

## 관측

- PO 3건 모두 draft 로 복귀.
- approval_chain 이력 보존 (이전 L1 승인 기록 유지).
- 재작성 후 신규 approval_chain id 할당 확인.

## 결론

- 체인 역진 없음 ✓ (ADR-0013 buying 드릴 G4-3 원칙과 일치).
- 감사 로그 완전성 ✓.
