---
gate: G4-2
module: accounting
tier: T1
owner: operations@oneerp.dev
last_reviewed: 2026-04-22
last_updated: 2026-04-22
related_runbooks:
  - docs/ops/runbook-db-backup-restore.md
  - docs/ops/runbook-incident-response.md
escalation_channels:
  - "#finance-ops"
  - "#legal-advisory"
---

# accounting 운영 런북

> 대상: Finance Ops · DBA · On-call · DPO
> 최종 검토: 2026-04-22 (Commercial Grade v2 · Spec III Wave B-2)
> 게이트: G4-2 · 파일럿 등급 T1

## 개요

`accounting` 은 OneERP 총계정원장(GL)·분개(journal)·회계기간(fiscal
period)·예산(budget)·세무 신고(tax return)·환율(exchange rate)를
단일 서비스 경계 내에서 관리한다. **회계 무결성 불변식** 은 다음과 같다.

- 차변 합계 = 대변 합계 (`journal_entry.debit_total == credit_total`).
- `account_balance` 스냅샷 = 동일 기간 `journal_entry` 재집계 결과.
- 마감(period.closed) 이후 `journal_entry` INSERT 금지 (`period_guard`).
- 환율 테이블(fx_rate) 은 `valid_from` 단조 증가 + 중복 금지.
- 부가세 신고 파일(vat_return) 은 승인 후 불변 (`immutable_after_submit`).

본 런북은 위 불변식 중 하나라도 위반되는 신호가 탐지될 때 **운영자가
사용자 확인 없이 수행 가능한 절차** 를 정의한다. 파괴적 명령(예: 잔액
덮어쓰기, 전표 삭제) 은 반드시 DPO / Finance 리더 승인 이후에 실행한다.

## 전제 조건

운영자는 런북 수행 전 다음 항목을 확인해야 한다.

- `kubectl -n finance get pods -l app=accounting` 상태 Ready ≥ 2/3.
- `curl -s http://accounting:8000/health` 200 OK + `{"db":"ok"}`.
- `FerretDB` master 연결 가능, `accounting_ro` replica lag < 5 s.
- 현재 열린 회계기간(`accounting_period.status=open`) 확인:
  ```bash
  uv run python scripts/audit/gl_integrity.py --tenant default \
      --period $(date +%Y-%m) --dry-run
  ```
- 최신 백업 스냅샷 `< 24h` 경과 (`docs/ops/runbook-db-backup-restore.md`).
- Grafana `accounting-overview` 대시보드 접근 권한 (PLACEHOLDER URL:
  `https://grafana.oneerp.dev/d/accounting-overview`).

전제 조건 중 **하나라도 실패** 하면 진단 절차로 바로 이동하지 않고
`#finance-ops` 에 상황 보고 → on-call 리더 지시에 따라 절차 분기.

## 진단 절차

### 1. 불변식 검증

```bash
uv run python scripts/audit/gl_integrity.py --tenant default \
    --period $(date +%Y-%m) --strict
```

`exit_code != 0` 또는 `drift > 0` 이면 **G4-2 장애 감지 성공** 으로 간주하고
2 단계로 이동.

### 2. 이벤트 체인 추적

`NATS` 스트림(`accounting.journal.*`) 에서 최근 1 시간 지연된 메시지가
있는지 확인한다.

```bash
nats stream info accounting-journal
nats consumer info accounting-journal gl-rebuilder
```

소비 지연 > 500 건이면 `scripts/audit/gl_rebuild.py --dry-run` 으로
재집계 필요량을 추정.

### 3. 주요 지표 (Grafana 링크)

| 지표 | 임계값 | 대시보드 |
|------|--------|----------|
| journal_entry_post_latency_p95 | < 400 ms | `accounting-overview/row-latency` |
| gl_drift_count | 0 | `accounting-overview/row-drift` |
| fx_rate_stale_minutes | < 60 | `accounting-overview/row-fx` |
| vat_return_submit_failures_5m | < 3 | `accounting-overview/row-tax` |
| period_guard_reject_total | < 10/min | `accounting-overview/row-guard` |

임계값 위반 지표는 **P2 경보** → `#finance-ops` 자동 호출.

### 4. 핵심 디버깅 쿼리

```javascript
// FerretDB (MongoDB wire protocol) — 최근 6 시간 drift 전표
use accounting;
db.journal_entry.aggregate([
  { $match: { posted_at: { $gte: new Date(Date.now() - 6*3600*1000) } } },
  { $group: { _id: "$entry_group", debit: { $sum: "$debit" },
              credit: { $sum: "$credit" } } },
  { $match: { $expr: { $ne: ["$debit", "$credit"] } } },
]);
```

```bash
# API: 열린 기간 + 최근 audit 이벤트
curl -s -H "Authorization: Bearer $TOKEN" \
    "http://accounting:8000/v1/audit?since=1h&severity=warning" | jq '.items[]'
```

### auth/rbac 문제

- gateway 인증 실패: `401` 급증, JWT issuer/audience 불일치, refresh token 오류를 먼저 확인한다.
- 모듈 내부 권한 실패: `403` 급증, OPA deny, `accounting_viewer`/`accounting_editor` 역할 매핑을 분리해서 확인한다.

## 복구 절차

### 시나리오 A — balance drift (이벤트 중복 처리)

1. `scripts/audit/gl_rebuild.py --tenant <t> --period <YYYY-MM> --dry-run`
   결과를 기록(JSON artifact 로 `artifacts/T1/G4-2/accounting/` 에 저장).
2. 차이가 < 0.01 (화폐 단위) 이면 `--apply` 로 확정 재집계.
3. 차이가 크면 `#finance-ops` + DBA 호출 → 수동 승인 후 apply.
4. 재집계 후 `gl_integrity.py --strict` 재실행, `exit_code == 0` 확인.

### 시나리오 B — period.closed 이후 journal 추가 시도

1. 감사 로그로 `period_guard` 위반 주체 식별 (`audit.actor`).
2. 위반 전표를 `status=rejected` 로 무효화 (삭제 금지 — 규제 요구).
3. 해당 호출 경로의 권한 정책을 OPA 에서 즉시 차단
   (`policies/accounting/period_guard.rego`).
4. 규제 대응 보고서 초안을 `docs/ops/drills/G4-4/` 에 생성.

### 시나리오 C — 환율 테이블 오류

1. `fx_rate` 중 `valid_from` 중복 / 역행 entry 식별.
2. 최신 신뢰 소스(한국은행 고시) 기준으로 대체 레코드 삽입.
3. 영향 기간의 외화 평가(multi-currency revaluation) 재실행
   — `uv run python scripts/audit/revalue_fx.py --period <YYYY-MM>`.

## 롤백 절차

장애 유발 배포 식별 후 다음 순서로 롤백한다.

1. `kubectl -n finance rollout history deploy/accounting` 로 직전 리비전 확인.
2. `kubectl -n finance rollout undo deploy/accounting --to-revision=<N>`.
3. 마이그레이션 되돌림은 **금지** — 대신 데이터 보정 쿼리를 실행.
4. 롤백 후 `gl_integrity.py --strict` + `G2-1 SLO` 대시보드 회복 확인.
5. 사고 요약을 `docs/ops/drills/G4-4/<date>-accounting.md` 에 기록.

## 에스컬레이션

| 단계 | 대상 | 기준 |
|------|------|------|
| 1차 | `#finance-ops` (Finance Ops on-call) | 모든 P2 이상 경보 |
| 2차 | `@tax-advisory` | VAT/원천세 신고 실패 |
| 3차 | `#legal-advisory` | P1 (법적 지급 지연/감사 대응) |
| 4차 | DPO (Data Protection Officer) | PII 노출 의심 |
| 5차 | CTO on-call | 30 분 내 복구 불가 |

연락처 루트는 `docs/ops/runbook-incident-response.md` on-call 트리 참조.

## 데이터 일관성 체크리스트

- [ ] `gl_integrity.py --strict` exit 0
- [ ] `journal_entry` vs `account_balance` drift = 0
- [ ] `period_guard_reject_total` 평시 수준
- [ ] `fx_rate` 시계열 단조 증가
- [ ] 최근 24h 백업 존재 및 복구 리허설 < 30d
- [ ] `audit.log` 에 `sev=error` 이벤트 < 5/hour

## 알려진 이슈 · FAQ

- **Q. 마감 직후 balance drift 가 0 이 아닌데 왜?**
  A. `accounting_period.closing` 상태에서 스냅샷이 10 초 지연될 수 있다.
     5 분 후 재실행 권장.
- **Q. `gl_rebuild.py --apply` 를 자동화해도 되는가?**
  A. 금지. 회계 규정상 수동 승인 필수.
- **Q. 외화 평가 재실행이 중복 전표를 만들지 않는가?**
  A. `idempotency_key = period+tenant+rate_version` 로 중복 방지.

## 부록 · 증거 파일 구조

```
artifacts/T1/G4-2/accounting/
├── 2026-04-22T0600Z.log        # gl_integrity.py --strict 출력
└── run-20260422T060000Z.json   # backfill 또는 CI stub
```

증거 파일은 `scripts/engine/evidence.py` 규격을 따르며,
`artifacts/_meta/index.jsonl` 에 자동 등록된다.
