---
incident_id: INC-2026-04-21-accounting-v18-validation
severity: P3 (post-deploy validation)
status: resolved
detected_at: 2026-04-21T02:15:00Z
resolved_at: 2026-04-21T03:42:00Z
module: accounting
type: deploy-validation
drill_gate: G4-4
related: docs/ops/drills/G4-4/2026-04-21-accounting.md
---

# INC-2026-04-21 — accounting v18 chart-of-accounts 검증

## 요약

v18 배포에서 chart-of-accounts 를 **level 5 → level 6** 으로 확장했으나,
staging 검증 중 일부 테넌트 원장에서 level 6 세그먼트 매핑이 중복 계정
(동일 상위 코드) 를 생성함을 확인. 마이그레이션을 취소하고 level 5 로 환원한다.

## 타임라인 (UTC)

| 시각 | 이벤트 |
|------|--------|
| 02:00:00 | v18 ArgoCD Sync 완료 (accounting Deployment) |
| 02:15:00 | staging QA: `account.5.1.2.3.4.5` 와 `account.5.1.2.3.4.6` 잔액 합 ≠ `account.5.1.2.3.4` 잔액 |
| 02:30:00 | 임원 회계팀 확인, backward-compat 위반 판정 |
| 02:45:00 | 롤백 결정 — ArgoCD targetRevision v18 → v17.9 |
| 03:10:00 | `scripts/migrations/accounting/001_backfill_level6.py --apply` 실행 (level 6 → 5 병합) |
| 03:25:00 | `scripts/audit/gl_integrity.py --period 2026-04 --strict` 전 테넌트 통과 |
| 03:42:00 | resolve |

## 증거

- 롤백 대상: accounting Deployment v18 → v17.9 (ArgoCD UI)
- 백필 스크립트: [`scripts/migrations/accounting/001_backfill_level6.py`](../../../scripts/migrations/accounting/001_backfill_level6.py)
- 무결성 검증: [`scripts/audit/gl_integrity.py`](../../../scripts/audit/gl_integrity.py)
- 데이터 손실 0, 모든 잔액 재계산 결과 차대 일치.

## 근본 원인

v18 마이그레이션이 level 6 세그먼트 생성 시 상위 계정을 "deprecated" 로만
표시하고 journal_entries 의 account_code 를 고수해, 상위/하위에서 이중 집계
발생. 마이그레이션 스크립트가 journal 레코드를 level 6 으로 이주시켰어야 함.

## 개선 항목

1. v19 재시도 전 proxy pattern (`account_balance_view`) 도입 — 물리 재구조화 없이
   level-6 조회만 논리적으로 제공.
2. 마이그레이션 게이트: level 변경 시 `gl_integrity.py --strict` 를 pre-apply check
   에 강제하도록 `k8s/migrations/*.yaml` 템플릿 수정.
3. backward-compat 테스트 추가: 상위 코드 잔액 = Σ 하위 코드 잔액 고정 불변식.
