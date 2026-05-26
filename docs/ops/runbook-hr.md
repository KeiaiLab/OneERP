---
gate: G4-2
module: hr
tier: T1
owner: operations@oneerp.dev
last_reviewed: 2026-04-22
last_updated: 2026-04-22
related_runbooks:
  - docs/ops/runbook-db-backup-restore.md
  - docs/ops/runbook-incident-response.md
  - docs/ops/runbook-payroll.md
escalation_channels:
  - "#hr-ops"
  - "#legal-advisory"
---

# hr 운영 런북

> 대상: HR Ops · DPO · On-call · Payroll 연계팀
> 최종 검토: 2026-04-22 (Commercial Grade v2 · Spec III Wave C-2)
> 게이트: G4-2 · 파일럿 등급 T1

## 개요

`hr` 은 OneERP 의 **인사 SSOT(Single Source of Truth)** 로 47 개 도메인
엔티티 — 직원(Employee) · 계약(Contract) · 조직 그래프(Org Graph) ·
입·퇴사(Onboarding/Offboarding) · 출결(Attendance) · 휴가(Leave) ·
급여 연계(Payroll Handoff) 를 관리한다. 다수의 PII(주민등록번호, 계좌,
가족관계) 를 포함하므로 **개인정보보호법 · GDPR · K-CCPA** 규정 준수가
최우선 요구사항이다.

본 런북은 다음 이벤트 중 하나라도 발생했을 때 **운영자가 사용자 확인
없이 수행 가능한 절차** 를 정의한다.

- 급여 연계(handoff) 이벤트 누락으로 지급 오류 가능
- 직원 입·퇴사 상태 머신 불일치 (hire 중복, offboard 후 잔존 리소스)
- PII 필드 평문 노출 의심 (응답/로그/메트릭)
- 개인정보 감사 로그 결손
- SCIM/LDAP 동기화 지연

## 전제 조건

- `kubectl -n hr get pods -l app=hr` Ready ≥ 2/3.
- `curl -s http://hr:8000/health` 200 OK, `{"db":"ok","scim":"ok"}`.
- FerretDB `hr` 데이터베이스 접근 권한 확보.
- **PII 접근** 을 위해 임시 토큰 발급 (`scripts/audit/issue_dpo_token.sh`)
  — 일반 JWT 로는 PII 응답이 마스킹된다.
- Payroll 서비스 상태가 Degraded 면 **handoff 쓰기를 일시 중단** 하고
  payroll 복구 대기 (동시 진행 금지).
- Grafana `hr-overview` 대시보드 접근 (PLACEHOLDER URL:
  `https://grafana.oneerp.dev/d/hr-overview`).

## 진단 절차

### 1. PII 유출 검사

```bash
# PII 마스킹 우회 탐지 — 응답에 RRN(주민번호 평문) 포함 시 P1
curl -s -H "Authorization: Bearer $READ_TOKEN" \
    "http://hr:8000/v1/employees?limit=20" | \
    grep -E '[0-9]{6}-[1-4][0-9]{6}' && echo "LEAK!"
```

매치 발생 시 **즉시 rate_limit=0 으로 해당 route 차단** + DPO 호출.

### 2. 이벤트 체인 누락 점검

hr 는 ADR-0020 §D3 정본에 따라 **7 종 이벤트**를 발행한다:
`employee.hired`, `employee.terminated`, `employee.transferred`,
`department.reorganized`, `designation.changed`, `payroll.run.completed`,
`leave_application.approved`.

구버전 문서에 등장하던 `employee.created` · `employee.activated` ·
`contract.signed` · `attendance.checked_in` · `leave.approved` ·
`payroll.handoff` · `employee.offboarded` · `employee.contract.signed` 은
**ADR-0020 정본에 없는 이름**이므로 구독 설정·알림 룰에서 제거한다
(미정의 · 후속 검토 필요 시 별도 ADR 로 등록).

```bash
for evt in \
    employee.hired \
    employee.terminated \
    employee.transferred \
    department.reorganized \
    designation.changed \
    payroll.run.completed \
    leave_application.approved; do
  nats consumer info hr-events $evt
done
```

`num_pending` 누적 > 200 또는 `num_ack_pending` 증가 추세면 3 단계.

### 3. 주요 지표 (Grafana 링크)

| 지표 | 임계값 | 대시보드 |
|------|--------|----------|
| payroll_handoff_lag_seconds | < 120 | `hr-overview/row-payroll` |
| pii_unmask_attempts_5m | < 5 | `hr-overview/row-pii` |
| onboard_stuck_total | < 3 | `hr-overview/row-lifecycle` |
| scim_sync_lag_minutes | < 10 | `hr-overview/row-scim` |
| audit_log_gap_seconds | 0 | `hr-overview/row-audit` |

### 4. 핵심 쿼리

```javascript
// FerretDB — 활성화 되지 않은 채 24h 경과한 신규 입사자
use hr;
db.employee.find({
  status: "pending",
  created_at: { $lt: new Date(Date.now() - 24*3600*1000) },
}).sort({ created_at: 1 }).limit(50);
```

```bash
# 급여 handoff 누락 재발행 (payroll 복구 이후 사용)
uv run python scripts/hr/replay_payroll_handoff.py \
    --period $(date +%Y-%m) --dry-run
```

### auth/rbac 문제

- gateway 인증 실패: `401` 급증, JWT issuer/audience 불일치, refresh token 오류를 먼저 확인한다.
- 모듈 내부 권한 실패: `403` 급증, OPA deny, `hr_viewer`/`hr_editor` 역할 매핑을 분리해서 확인한다.

## 복구 절차

### 시나리오 A — 급여 계산 오류 (handoff 누락)

1. `handoff_lag_seconds > 300` 경보 확인.
2. `replay_payroll_handoff.py --dry-run` 으로 누락 건수/영향 직원 추출.
3. HR 리더 + Payroll 리더 승인 → `--apply` 실행.
4. Payroll 서비스 `reconcile` 엔드포인트 호출로 중복 방지 확인.
5. 결과를 `artifacts/T1/G4-2/hr/<timestamp>.log` 로 저장.

### 시나리오 B — 입사/퇴사 상태 머신 불일치

1. `status=pending` 이 24h 초과한 employee 목록 확보 (위 쿼리).
2. 정상 경로로 재시도 (`POST /v1/employees/{id}:activate`).
3. 실패 시 OPA 정책(`policies/hr/lifecycle.rego`) 로그 확인.
4. 후처리 — orphan contract / attendance 레코드는 **소프트 삭제** 만.
5. 퇴사(offboard) 후 잔여 리소스는 `scripts/hr/cleanup_offboarded.py`
   사용, 삭제 아닌 **보존(retention_until=+5y)** 원칙.

### 시나리오 C — 개인정보 감사 실패

1. `audit_log_gap_seconds > 0` 은 GDPR 상 보고 가능 사건.
2. 감사 로그 파이프라인(`hr.audit → nats → audit-store`) 끊김 지점 식별.
3. 정상 복구 후 **gap 기간** 에 대한 재구성 보고서 작성.
4. 24 시간 내 DPO 가 규제 당국 통지 여부 판단.

## 롤백 절차

1. `kubectl -n hr rollout history deploy/hr` 로 직전 리비전 확인.
2. `kubectl -n hr rollout undo deploy/hr --to-revision=<N>`.
3. SCIM 동기화 재실행 (`uv run python scripts/hr/scim_resync.py`).
4. PII 감사 로그가 롤백 후에도 연속되는지 `audit.log` 에서 확인.
5. 사고 요약을 `docs/ops/drills/G4-4/<date>-hr.md` 에 기록.

## 에스컬레이션

| 단계 | 대상 | 기준 |
|------|------|------|
| 1차 | `#hr-ops` | 모든 P2 이상 경보 |
| 2차 | DPO (Data Protection Officer) | PII 노출/감사 결손 |
| 3차 | `#legal-advisory` | GDPR 72h 통지 후보 |
| 4차 | Payroll On-call | handoff_lag > 600s |
| 5차 | CTO on-call | 30 분 내 복구 불가 |

## 데이터 일관성 체크리스트

- [ ] `payroll_handoff_lag_seconds` 평시 수준 복귀
- [ ] `employee.status` 일관성 (pending → active 전이 < 24h)
- [ ] `contract.signed_at` 가 `employee.hired_at` 이후인지
- [ ] PII 필드 응답에서 평문 미출현 (자동 스캐너 통과)
- [ ] SCIM/LDAP 사용자 수 동기화 오차 < 0.1 %
- [ ] 감사 로그 시퀀스 연속 (gap = 0)

## 알려진 이슈 · FAQ

- **Q. 퇴사 후 7 년이 지난 직원 레코드를 삭제해도 되는가?**
  A. 세법상 7 년 보존이 지나도 **노동청 기록보존 의무** 10 년을 추가 확인.
     `scripts/hr/retention_check.py --employee <id>` 로 확정.
- **Q. SCIM 동기화 지연이 10 분을 넘는데 장애인가?**
  A. 60 분 이내면 backoff 구간 — 정상. 60 분 초과 시 IdP 측 점검 요청.
- **Q. payroll 다운 시 hr 가 handoff 이벤트를 발행해도 되는가?**
  A. 발행 가능(idempotent). 단, handoff replay 에 의존하여 payroll 복구
     직후 reconcile 호출 필수.

## 부록 · 증거 파일 구조

```
artifacts/T1/G4-2/hr/
├── 2026-04-22T0700Z.log        # lifecycle 검증 출력
└── run-20260422T070000Z.json   # backfill 또는 CI stub
```

연락처 루트는 `docs/ops/runbook-incident-response.md` on-call 트리 참조.

<!-- DOC-AUDIT C3 해소: 2026-04-22 — 이벤트 7종을 ADR-0020 §D3 정본(employee.hired/terminated/transferred · department.reorganized · designation.changed · payroll.run.completed · leave_application.approved)으로 전면 교체 · NATS 구독 예시 동기화 · employee.created/activated/contract.signed/attendance.checked_in/leave.approved/payroll.handoff/employee.offboarded 제거 -->
