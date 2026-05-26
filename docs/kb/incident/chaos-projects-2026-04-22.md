---
chaos_id: chaos-projects-2026-04-22
module: projects
severity: P2-simulated
conducted_at: 2026-04-22T05:15:00Z
duration_minutes: 11
type: chaos-engineering
---

# chaos-projects-2026-04-22 — SLA breach 대량 오보

## 가설

SLA 경보 자동 이메일 발송 가드 (auto-email guard) 가 데이터 오류로 인한
대량 오보를 차단한다.

## 주입

staging 에서 20개 프로젝트 deadline 을 -11 영업일로 조정 (데이터 오류 시뮬).

## 관측

- `project-sla-breach` 경보 20건 동시 발생.
- auto-email guard 자동 활성 → 고객 이메일 0 발송.
- PM 리뷰 후 실제 breach 3건만 수동 승인 → 이메일 3건 발송.

## 결론

- 가드 동작 ✓
- 오보 방지 효과 확인.

## 개선

- 가드 활성 임계 (현재 "5건 이상 breach in 10m") 조정 근거 정량화 필요.
