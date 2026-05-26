---
chaos_id: chaos-compliance-2026-04-22
module: compliance
severity: P2-simulated
conducted_at: 2026-04-22T08:15:00Z
duration_minutes: 10
---

# chaos-compliance-2026-04-22 — 정책 업데이트 롤백

## 가설
새 규제 정책 배포 후 위반 경보 급증 시 staging 으로 회수 가능.

## 주입
staging 에 의도적으로 잘못된 정책 룰 배포.

## 관측
- 위반 경보 400건 급증 감지 5분.
- 정책 롤백 3분.
- 의도된 오보 400건 정리 15분.

## 결론
정책 staging 흐름 검증. 프로덕션 배포 전 dry-run 필수.
