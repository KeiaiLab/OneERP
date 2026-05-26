---
chaos_id: chaos-payroll-2026-04-22
module: payroll
severity: P1-simulated
conducted_at: 2026-04-22T04:00:00Z
duration_minutes: 20
type: chaos-engineering
---

# chaos-payroll-2026-04-22 — 은행 API 부분 장애

## 가설

A-bank API 의 30% 응답 실패 시 B-bank fallback 전환으로 0 지급 실패 달성.

## 주입

staging 에서 A-bank mock 의 30% 5xx 응답 (60분 시뮬).

## 관측

- 집행 1차 성공률: 70%.
- B-bank fallback 전환 후 재시도: 성공률 100%.
- 실패 재시도 17건 포함 전체 지급 완료.
- MTTR 37분 (드릴 G4-5 payroll 과 일치).

## 결론

- 법적 지급 시한 0 위반 ✓
- B-bank 전환 수동 승인이 병목 (+8분).

## 개선

- B-bank 전환 임계치 자동 트리거 (30% 실패 3분 지속 시 자동) 설계.
