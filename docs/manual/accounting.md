---
module: accounting
gate: G5-1
tier: "T1+T2"
audience: finance-admin tenant-admin operator auditor
last_updated: 2026-04-22
spec_version: Commercial Grade v2
evidence_line_target: 400
---

# accounting 운영 매뉴얼

> 대상: 재무 관리자 · 테넌트 관리자 · 운영자 · 감사인
> 최종 갱신: 2026-04-22 (Commercial Grade v2 · Spec III Wave B-2)
> 게이트: G5-1 운영자 매뉴얼 증거

## 개요

`accounting` 은 OneERP 재무 클러스터의 리더 서비스로, **56 개 모델 · 70 개
라우트 · 23 개 도메인 서비스** 를 단일 프로세스 경계 내에서 제공한다.
ADR-0019 에서 동결된 6 서브도메인 그룹(회계기간 · 전표 · 예산 · 세무 ·
환율 · 자금)을 본 매뉴얼이 순서대로 안내한다.

본 문서는 **운영자 관점**에서 정상 동작 확인 · 장애 진단 · 규제 대응까지
한 번에 따라갈 수 있도록 구성된다. 엔드유저 UI 사용법은 `docs/user-manual/
accounting.md` 와 `docs/tutorials/accounting.md` 를 참조한다.

### 주요 책임 영역

| 영역 | 설명 |
|------|------|
| 전표 관리 | 복식부기 전표 draft→submit→approve→post→reverse 전이 |
| 기간 관리 | 회계연도·회계기간 생성·마감·잠금 |
| 예산 관리 | 수립·확정·실행·결산, 원가 센터/프로핏 센터 |
| 세무 | 부가세(VAT)·원천세·전자세금계산서·K-IFRS 매핑 |
| 환율 | 외화환산·헤지 포지션·연결결산·제거분개 |
| 자금 | 은행 매칭·현금흐름 예측·자금수지·대출·리스 |

## 도메인 — 56 모델 · 6 그룹

ADR-0019 Appendix B 와 동일한 그룹화. 운영자가 문제 원인을 좁히는 첫
필터로 사용한다.

### 그룹 1 · 회계기간(period)

- `fiscal_year` — 회계연도. 시작일/종료일/상태(open/closing/closed).
- `accounting_period` — 월 단위 기간. 12 회계연도 × 12 기간 구조.
- `period_closing_voucher` — 기간 마감 전표(이월 손익).
- **운영 포인트**: 기간을 `closed` 로 전이하면 해당 기간에 속한 전표
  `post` 가 영구 차단된다. 복구는 관리자 권한으로만 가능(ADR-0019 §3).

### 그룹 2 · 전표(journal)

- `journal_entry` — 복식부기 전표. 상태 전이가 가장 복잡한 엔티티.
- `general_ledger_entry` — 총계정원장(포스팅 후 생성).
- `accounts_receivable` / `accounts_payable` — 매출·매입 채권/채무.
- `payment_entry` / `payment_reconciliation` — 결제·매칭.
- **운영 포인트**: `post` 이후 정정은 반드시 `reversed` 후 재발행. 직접
  수정 시 감사 로그 불일치가 발생한다.

### 그룹 3 · 예산(budget)

- `budget` / `budget_version` — 예산 및 버전 관리.
- `budget_transfer` — 예산 이체.
- `cost_center` / `profit_center` — 원가·수익 센터.
- `activity_based_costing_rule` — ABC 원가 배부.
- **운영 포인트**: 확정 예산의 이체는 승인 워크플로우(submit → approve)
  를 거쳐야 한다.

### 그룹 4 · 세무(tax)

- `vat_return` — 부가세 신고. 국세청 Open API 연계.
- `tax_rule` / `tax_calendar` — 세율·신고 일정.
- `etax_invoice` — 전자세금계산서. 바로빌 연동.
- `withholding_tax_*` — 원천세 계산·신고.
- `kifrs_mapping` / `revenue_recognition_*` — K-IFRS 수익인식.
- **운영 포인트**: 국세청·바로빌 장애 시 `status=failed` 재시도 큐 가동
  여부를 먼저 확인(장애 대응 §참조).

### 그룹 5 · 환율·국제거래

- `currency_exchange` / `multi_currency_revaluation` — 외화 평가.
- `exchange_rate_revaluation` — 평가차손익.
- `letter_of_credit` — 신용장.
- `hedging_instrument` / `hedging_relationship` — 파생·헤지 관계.
- `intercompany_*` / `consolidation_*` — 내부거래·연결결산.
- **운영 포인트**: 월말 외화 평가 배치가 타임존 경계에서 돌아간다. 서머
  타임 전환 주간은 수기 재확인.

### 그룹 6 · 자금·보조

- `bank_account` / `bank_reconciliation` / `bank_transaction` — 은행.
- `cash_flow_forecast` — 현금흐름 예측.
- `loan_*` / `lease_*` — 대출·리스 상각표.
- `fund_transfer` — 계좌 간 이체.
- `dunning` — 독촉.
- `severance_reserve` — 퇴직급여충당금.
- `payment_order` / `payment_terms_template` — 지급 지시·결제 조건.
- `deferred_*` — 이연수익·비용.
- `segment_report` / `financial_ratio_report` — 세그먼트·재무비율.
- `accounting_dimension` / `accounting_dimension_value` — 분석 차원.
- `bank_statement_import` / `terms_and_conditions` — 명세 import·약관.

## 주요 API 흐름 3개

### 흐름 A · 전표 작성 → 포스팅

```
POST /api/v1/journal-entries              (draft 생성)
PATCH /api/v1/journal-entries/{id}/submit (승인 대기)
PATCH /api/v1/journal-entries/{id}/approve
PATCH /api/v1/journal-entries/{id}/post   (총계정원장 반영, 이벤트 발행)
```

- 상태: `draft → submitted → approved → posted`.
- `post` 시점에 `journal_entry.posted` 이벤트 발행 → analytics / audit /
  budget 이 각각 소비.
- **실패 케이스**: 기간이 `closed` 면 `post` 가 409 로 거부된다.

### 흐름 B · 회계기간 마감

```
POST /api/v1/accounting-periods/{id}/close
```

- 사전 조건: 해당 기간의 `draft`/`submitted` 전표가 0 건이어야 함.
- 동작: `period_closing_voucher` 생성(이월) → 상태 `closed` 전이 →
  `accounting_period.closed` 이벤트 발행.
- 실패 시: 차단 원인을 응답 body `blocking_entries` 배열에서 확인.

### 흐름 C · 부가세 신고

```
POST /api/v1/vat-returns                  (초안 생성)
PATCH /api/v1/vat-returns/{id}/prepare    (국세청 계산 검증)
POST /api/v1/vat-returns/{id}/submit      (전송)
```

- `submit` 은 비동기 202 응답. `status` 폴링으로 최종 결과 확인
  (`accepted` / `rejected` / `failed`).
- 바로빌·국세청 장애 시 `failed` 로 전이 후 재시도 큐에 적재된다.

## 권한 모델

전역 RBAC(gateway 의 OPA 정책)과 테넌트 범위 RBAC 의 2 계층.

| 역할 | 허용 범위 |
|------|-----------|
| `accounting.viewer` | 전 자원 read-only |
| `accounting.operator` | 전표 `draft` 생성·수정, `submit` |
| `accounting.approver` | `approve`·`post`·`reverse` |
| `accounting.closer` | `accounting_period.close`, 기간 잠금 해제 |
| `accounting.tax` | 부가세·원천세·전자세금계산서 전담 |
| `accounting.admin` | 전권 + 구성 변경(계정과목·차원) |

세부 매핑은 `policies/accounting/routes.rego` (Wave D 생성 예정) 에서
확인. gateway 는 JWT 의 `scope` 클레임으로 역할을 전달한다.

## 감사 로그

ADR-0019 §4 에 따라 다음 이벤트가 `audit_events` 컬렉션에 기록된다.

| 이벤트 | 트리거 | 필드 |
|--------|--------|------|
| `accounting.create` | 전표/기간/예산 생성 | actor, tenant_id, resource, payload |
| `accounting.update` | 변경 | actor, tenant_id, resource, diff |
| `accounting.delete` | 삭제 | actor, tenant_id, resource |
| `accounting.submit` | 전표 상태 전이 | actor, tenant_id, resource, from, to |
| `accounting.approve` | 승인 | actor, tenant_id, resource |
| `accounting.post` | 포스팅 | actor, tenant_id, resource, amount_total |
| `accounting.reverse` | 역분개 | actor, tenant_id, resource, original_id |
| `accounting.close` | 기간 마감 | actor, tenant_id, resource (period_id) |

감사 로그는 `audit_hooks.py` 의 `emit()` 이 단일 진입점이다. 변경 이벤트
가 누락되면 G3-4 게이트가 fail 한다.

## 장애 대응 (Runbook)

### 증상 A · 전표 `post` 가 401/403 반복

1. gateway 인증 로그에서 JWT 만료·서명 오류 여부 확인.
2. `accounting.approver` 역할이 사용자에게 부여되어 있는지 keycloak
   에서 확인.
3. OPA 정책 (`policies/accounting/routes.rego`) 의 최근 배포 시각 확인.

### 증상 B · 기간 마감이 409 로 거부됨

1. 응답 body `blocking_entries` 에서 차단 전표 ID 확인.
2. 해당 전표를 `post` 또는 `reverse` 로 정리.
3. 재시도.

### 증상 C · 부가세 신고 `failed`

1. `vat_returns/{id}` 조회로 `error_code` 확인.
2. 국세청 측 장애는 `nts_api_client` 로그에 `503/504` 로 기록.
3. 재시도 큐가 돌고 있는지 `period_closing_service` 워커 상태 점검.
4. 12 시간 이상 지속되면 `compliance` 팀에 수동 제출 전환 요청.

### 증상 D · 외화 평가 배치 실패

1. `multi_currency_revaluation_service` 로그에서 환율 소스 확인.
2. `currency_exchange` 최신 레코드가 전일 기준인지 확인.
3. 필요 시 수기로 환율 등록 후 재실행.

### 증상 E · 감사 로그 누락

1. `audit_hooks.emit` 호출이 해당 라우트에 들어있는지 grep.
2. `MODULE_ACTIONS` 허용 액션 목록에 신규 액션이 추가됐는지 확인.
3. G3-4 mutation 테스트 재실행(`pytest tests/unit/test_audit_mutation.py`).

## 마이그레이션 규약

### 스키마 변경

1. `models/` 에 신규 필드 추가 시 기본값(nullable) 보장. 백필 스크립트
   는 `scripts/migrations/accounting/YYYYMMDD-slug.py` 로 작성.
2. EntityMeta 등록 순서를 유지(`entities.py` 하단 튜플). 삭제는 deprecated
   플래그 후 1 릴리즈 뒤 실제 제거.

### 라우트 변경

1. 기존 경로 deprecated 시 `Sunset` 헤더로 2 릴리즈 유예.
2. OpenAPI 덤프(`openapi.yaml`) 를 동시 갱신.

### 이벤트 스키마 변경

1. `EventType` 에 version 서픽스 추가(`.v2`).
2. 핸들러는 v1·v2 를 병행 소비 후 v1 제거.

## FAQ

**Q1.** `post` 후 금액 오류를 발견했습니다. 어떻게 정정하나요?

A. `reverse` 로 역분개한 뒤 새 전표를 작성합니다. 원 전표는 절대 수정
하지 않습니다(감사 연속성).

**Q2.** 마감된 기간의 자료가 꼭 필요합니다.

A. `accounting.closer` 권한으로 임시 재개(`reopen`) 가능하지만, 감사
로그에 영구 흔적이 남습니다. 차라리 당기 기간에 조정 전표를 작성하는
것을 권장합니다.

**Q3.** 국세청 전송이 주말에 실패하면 재시도 큐는?

A. 매 30 분 재시도. 최대 72 시간. 이후에도 실패면 수동 전환 필요.

**Q4.** 외화 원금과 원화 평가액 중 보고서 기준은?

A. 그룹 5(환율) 에 정의된 `multi_currency_revaluation` 결과를 기준으로
보고서가 생성됩니다. 원화 평가액 기준.

**Q5.** 감사 로그 보존 기간은?

A. 법정 5 년. `audit_events` 컬렉션은 Hot(1 년) + Cold(4 년) 계층으로
운영합니다.

**Q6.** 전자세금계산서 발급이 지연됩니다.

A. 바로빌 Open API 의 TPS 상한(테넌트당 5 TPS)에 걸렸을 가능성이 큽니다.
`barobill_client` 로그에서 `429` 빈도를 확인하고, 필요 시 배치 발급으로
전환합니다.

**Q7.** 원천세 신고 기한을 놓쳤습니다.

A. `tax_calendar` 에 등록된 다음 납부일에 가산세 포함 전송합니다.
`withholding_tax_service` 가 가산세 계산을 지원합니다.

**Q8.** K-IFRS 매핑 오류가 의심됩니다.

A. `kifrs_service` 의 `validate()` 로 매핑 정합성 점검. 매핑 파일은
`kifrs_mapping` 엔티티에 저장됩니다.

**Q9.** 예산 초과 전표가 그대로 포스팅됩니다.

A. `budget` 의 `enforce_limit` 플래그가 꺼져 있을 수 있습니다. 확정
예산은 기본 on 이 권장값입니다.

**Q10.** 연결결산 차이가 큽니다.

A. `consolidation_entry` / `elimination_entry` 의 내부거래 제거가 누락
되지 않았는지 확인합니다. `consolidation_service.reconcile()` 로 자동
정합성 체크가 가능합니다.

## 관측성 지표 (G4-2)

운영자가 가장 먼저 확인할 메트릭·로그·트레이스 3 계층.

### 메트릭 (Prometheus)

| 이름 | 타입 | 의미 | SLO |
|------|------|------|-----|
| `accounting_journal_post_total{status}` | counter | 전표 post 성공/실패 | 실패율 < 0.1% |
| `accounting_period_close_duration_seconds` | histogram | 기간 마감 소요 | p95 < 30s |
| `accounting_vat_submit_total{outcome}` | counter | 부가세 제출 outcome | accepted 비율 ≥ 99% |
| `accounting_audit_emit_total` | counter | 감사 emit 건수 | 라우트 호출 대비 ≥ 100% (누락 금지) |
| `accounting_etax_issue_latency_seconds` | histogram | 전자세금계산서 발급 지연 | p95 < 5s |
| `accounting_repository_query_duration_seconds` | histogram | Repository 쿼리 | p95 < 100ms |

### 로그

- `logger=accounting.journal`·`logger=accounting.period` 등 서브도메인
  별 logger 이름 규칙.
- 구조화 로그: `timestamp`, `level`, `logger`, `message`, `tenant_id`,
  `trace_id`, `actor`.

### 트레이스

- `X-Request-ID` / `traceparent` 헤더를 gateway 가 주입. accounting 은
  그대로 전파한다.
- 주요 스팬: `journal.post`, `period.close`, `vat.submit`, `etax.issue`.

## 성능 및 용량 기준

| 항목 | 기준 | 비고 |
|------|------|------|
| 단일 테넌트 일일 전표 | ≤ 100k | post RPS 한계 100 |
| 단일 전표 line | ≤ 999 | DB 단일 document 크기 상한 |
| 부가세 신고 건 | ≤ 10k/분기 | 배치 처리 |
| 전자세금계산서 | ≤ 50k/월 | 바로빌 TPS 5 |
| 연결결산 법인 | ≤ 500 | 단일 consolidation_group |

초과 예측 시 ADR-0014 plane 축으로 tenant-plane 분리 검토.

## 설정 가이드

`CoreSettings` 를 상속한 `Settings`(`oneerp_accounting_app/config.py`) 가
다음 항목을 읽는다.

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `ONEERP_BAROBILL_CERT_ID` | (없음) | 바로빌 인증 ID |
| `ONEERP_NTS_API_KEY` | (없음) | 국세청 Open API 키 |
| `ONEERP_OPENBANKING_CLIENT_ID` | (없음) | 오픈뱅킹 클라이언트 |
| `ONEERP_CODEF_ACCOUNT` | (없음) | CODEF 계정 |
| `ONEERP_PERIOD_CLOSE_BATCH` | `true` | 기간 마감 배치 자동화 on/off |
| `ONEERP_VAT_RETRY_MAX` | `5` | 부가세 재시도 상한 |

운영 환경의 시크릿은 `deploy/secrets/accounting/externalsecret.yaml`
(Wave D) 를 통해 주입한다. 하드코딩 금지.

## 배포 체크리스트

1. `uv run ruff check services/finance/accounting` — 신규 코드 0 error.
2. `uv run pytest services/finance/accounting/tests/unit -x` — green.
3. `uv run pytest services/finance/accounting/tests/security -v` —
   skipped 또는 green (스테이징 없음 상태에서는 skip 허용).
4. `docker buildx build --builder masblue-builder …` — 이미지 빌드.
5. ArgoCD 의 accounting application sync.
6. gateway 의 라우트 정책(policies/accounting/routes.rego) 재배포 확인.
7. 배포 후 `/health` 200 OK, `/api/v1/journal-entries` 샘플 호출 200.

## 롤백 절차

1. 이전 image tag 로 Deployment `rollout undo`.
2. 스키마 역호환성이 깨졌을 때만 데이터 복구 절차 발동:
   - 파이프라인: 백업 snapshot 복원 → 재적용 → 감사 로그 보존.
3. 롤백 후 `docs/ops/drills/G4-5/accounting-YYYY-MM-DD.md` 에 기록.

## 보안 체크리스트

G3-1 ~ G3-5 게이트에 대응하는 운영자 점검 항목.

### AuthN (G3-1)

- [ ] JWT 만료(`exp`) 초과 시 401 확인
- [ ] JWT 서명 오검증 시 401 확인
- [ ] audience 불일치 시 401 확인
- [ ] issuer 불일치 시 401 확인
- [ ] nonce 재사용 시 401 확인
- [ ] replay token 감지 시 401 확인
- [ ] scope 부족 시 403 확인

### AuthZ (G3-2)

- [ ] `accounting.viewer` 가 mutation 라우트 호출 시 403
- [ ] 다른 테넌트 자원 접근 시 404(정보 은폐) / 403

### 입력 검증 (G3-3)

- [ ] JournalEntry 차대변 합계 불일치 시 422
- [ ] 과거 기간(closed) 전표 생성 시 409

### 감사 로그 (G3-4)

- [ ] 모든 mutation 라우트에서 `audit_hooks.emit` 호출 흔적 존재
- [ ] `MODULE_ACTIONS` 외 액션 호출 시 `accounting.unknown.*` 로 기록

### 의존성 (G3-5)

- [ ] `pip-audit --format json` vulnerabilities == 0
- [ ] 최신 결과: `artifacts/T1/G3-5/accounting/pip-audit-2026-04-22.json`

## 장기 운영 요령

### 월말 결산 체크리스트

1. 전주까지 모든 전표 `post` 완료.
2. 외화 평가 배치 실행 로그 확인 (`multi_currency_revaluation`).
3. 은행 매칭 (`bank_reconciliation`) 미결 건 0 확인.
4. 기간 마감(`POST /accounting-periods/{id}/close`).
5. 결산 보고서 생성 (`/reports/income-statement`, `/reports/balance-sheet`).
6. 감사 로그 백업 상태 확인.

### 분기말 · 연말 추가 절차

- 부가세 분기 신고 (`/vat-returns/{id}/submit`).
- 원천세 지급명세서 제출.
- 연말에는 `period_closing_voucher` 이월 손익 검증.
- 연결결산(`consolidation_service`) 실행 및 제거분개 확인.
- K-IFRS 공시 자료(`kifrs_service.export()`) 생성.

## 알려진 제약

1. `app.openapi()` 자동 덤프는 Pydantic forward-ref 문제로 현재 실패
   (근거: `artifacts/T1/G1-2/accounting/openapi-generated.log`). `openapi.yaml`
   수동 스텁으로 대체 운영 중.
2. 70 라우트 × 23 서비스 단일 프로세스 운영 — tenant-plane 분리 미적용.
3. 국세청·바로빌 Open API 타임아웃은 외부 의존이므로 SLO 보장 불가.

## 문의 · 에스컬레이션

| 상황 | 1차 대응 | 2차 (에스컬레이션) |
|------|----------|---------------------|
| 전표 포스팅 장애 | 재무 운영팀 | accounting 플랫폼팀 |
| 감사 로그 누락 의심 | 감사팀 + 플랫폼팀 | 보안팀 |
| 국세청 장애 | 세무팀 | 외부 CS + compliance |
| 대량 성능 저하 | 플랫폼팀 | SRE + DBA |

## 참조

- `docs/kb/adr/0019-accounting-bounds.md` (G1-1)
- `services/finance/accounting/openapi.yaml` (G1-2)
- `services/finance/accounting/oneerp_accounting_app/routes/` (70 엔드포인트)
- `services/finance/accounting/oneerp_accounting_app/services/` (23 도메인 서비스)
- `docs/manual/gateway.md` 구조 미러 원본(`docs/user-manual/gateway.md`)
- `docs/tutorial/accounting-flow.md` (G5-2 튜토리얼)
- ADR-0011 코드 클러스터 축, ADR-0014 런타임 plane 축
- Spec III 설계: `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md`
- Spec III 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` Wave B-2

## 시작하기

Accounting 모듈에 처음 접속하는 사용자를 위한 절차다.

1. **로그인** — 사내 SSO 포털(`https://erp.example.com`)에 접속 후 회사 계정으로 로그인한다. 2FA 필수.
2. **권한 신청** — 기본 계정은 조회 권한만 가진다. 저널 작성·결재가 필요한 경우 상위 조직장에게 `accounting.journal.write`, `accounting.approval.*` 역할을 요청한다(Jira 티켓 `IAM-*`).
3. **첫 접속** — 좌측 내비게이션에서 **회계 > 대시보드** 선택. 최초 1회 회사/회계기간 선택 다이얼로그가 표시된다.
4. **사전 체크리스트** — 브라우저는 Chrome 최신 버전 권장, 팝업 차단 해제, VPN(`oneerp-vpn`) 접속 권장(사외 접근 시 필수).
5. **헬프데스크** — 로그인·권한 이슈는 `#accounting-support` 슬랙 채널, 장애는 `#oncall-accounting` 채널 이용.

## 주요 화면

모듈 핵심 화면 4종의 위치·역할을 요약한다. (스크린샷은 `docs/images/accounting/` 하위에 박제 예정)

| 화면 | 경로 | 역할 | 캡처 |
|------|------|------|------|
| 대시보드 | `/accounting/dashboard` | 마감률·미결전표 수·현금흐름 요약 | `![대시보드](../images/accounting/dashboard.png)` |
| 저널 목록 | `/accounting/journal` | 저널 엔트리 조회·필터·내보내기 | `![저널목록](../images/accounting/journal-list.png)` |
| 저널 상세 | `/accounting/journal/:id` | 분개 라인 편집·결재 요청·히스토리 | `![저널상세](../images/accounting/journal-detail.png)` |
| 예산 | `/accounting/budget` | 예산 vs 실적, 기간별 drill-down | `![예산](../images/accounting/budget.png)` |
| 리포트 | `/accounting/reports` | 재무상태표·손익계산서·현금흐름표 | `![리포트](../images/accounting/reports.png)` |

각 화면 상단의 **도움말(?)** 아이콘은 본 매뉴얼의 해당 섹션으로 deep-link된다.

## 자주 쓰는 작업

사용 빈도가 높은 운영 태스크 5종의 절차를 정리한다.

### 저널 생성
1. `저널 목록 > 신규` 버튼 클릭.
2. 회계기간·거래일·적요 입력 → 분개 라인 추가(최소 2라인, 차대 합계 0).
3. **저장(Draft)** → 상급자에게 **결재 요청**.

### 저널 조회·검색
- 상단 필터바에서 기간·계정과목·금액범위·전표상태(`draft/pending/posted/void`) 조합 검색.
- 고급 검색은 `?` 버튼으로 query DSL 입력 가능(예: `amount:>1000000 AND account:531*`).

### 결재 처리
1. `결재함 > 대기` 에서 항목 선택.
2. 분개 라인 검토 후 **승인/반려**. 반려 시 사유 필수.
3. 승인 완료 전표는 자동으로 `posted` 상태가 된다.

### 리포트 다운로드
- `리포트 > 원하는 보고서 > 기간 선택 > PDF/Excel 내보내기`.
- 대용량(>10만 라인)은 비동기 export로 자동 전환되며, 완료 시 인앱 알림이 온다.

### 월마감 · 기마감
1. `마감 > 월마감` 진입 → 체크리스트(미결전표/대사 불일치/환산 오류) 자동 스캔.
2. 모든 체크 PASS 시 **마감 확정** 클릭. 확정 후 해당 기간 전표 편집 불가.
3. 기마감은 재무팀장 승인 필요.

## 설정

관리자 전용 설정 항목이다. 변경 시 감사 로그(`audit.accounting.settings.*`)가 자동 기록된다.

- **권한(Role)** — `accounting.admin` · `accounting.approver` · `accounting.operator` · `accounting.viewer` 4단계. 사용자별 회사·사업부 scope 분리 가능.
- **회계기간(Period)** — 회사별 회계연도 시작월, 분기 정의, 마감 잠금 기한 설정. 최소 단위는 월.
- **계정과목(Chart of Accounts)** — 트리 구조 편집, 계정 병합·분리 이력 보관. 신규 계정 추가는 결재 필수.
- **세금 코드(Tax Code)** — 부가세율·원천징수율·과표 매핑. 세법 개정 시 effective_from 필드로 버전 관리.
- **연동(Integration)** — 은행 API, 국세청 Hometax, SAP Connector. 인증 토큰은 Vault에 저장.

## 제한사항

현재 버전의 알려진 제약이다.

- **동시편집 제한** — 동일 전표에 대해 2명 이상이 동시에 편집할 수 없다. 뒤늦게 접근한 사용자는 read-only 모드로 진입한다(낙관적 락 충돌 시 재시도 안내).
- **결재 후 수정 불가** — `posted` 상태 전표는 직접 수정할 수 없고, **역분개 전표** 생성으로만 정정 가능.
- **마감 이후 편집 금지** — 월마감·기마감 확정된 기간의 전표는 재오픈 절차(재무팀장 승인)를 거쳐야만 수정 가능.
- **API Rate Limit** — 사용자당 600 req/min, IP당 6000 req/min. 초과 시 `429 Too Many Requests`.
- **대량 업로드 한도** — 1회 CSV 업로드 최대 5만 라인, 파일 크기 50MB.
- **첨부파일** — 파일당 25MB, 저널당 최대 10개 첨부.
- **브라우저** — IE/Edge Legacy 미지원.

## 장애 대응

장애 유형별 1차 대응 절차다. 상세 runbook은 상단 **## 장애 대응 (Runbook)** 섹션 및 `docs/runbooks/accounting/` 참조.

| 증상 | 1차 조치 | 에스컬레이션 | Runbook |
|------|---------|-------------|--------|
| 로그인 실패 | 세션 쿠키 삭제·재로그인, SSO 상태 확인 | `#iam-support` | [`sso-outage.md`](../runbooks/accounting/sso-outage.md) |
| 저장 에러(500) | 새로고침 후 재시도, 브라우저 콘솔 로그 캡처 | `#oncall-accounting` | [`journal-save-error.md`](../runbooks/accounting/journal-save-error.md) |
| 대사 불일치 | 대사 리포트 실행 → 차이 확인 → 역분개 검토 | 재무팀장 | [`reconciliation-mismatch.md`](../runbooks/accounting/reconciliation-mismatch.md) |
| 결재 지연 | 결재선 점검, 대체결재자 지정 | 조직장 | [`approval-stuck.md`](../runbooks/accounting/approval-stuck.md) |
| 리포트 타임아웃 | 기간 축소 재시도, 비동기 export 이용 | `#oncall-accounting` | [`report-timeout.md`](../runbooks/accounting/report-timeout.md) |

장애 신고 시 **회사/사업부 · 사용자 ID · 전표 ID · 타임스탬프 · 스크린샷**을 함께 전달한다.

## Change Log

| 일자 | 변경 | 근거 |
|------|------|------|
| 2026-04-22 | 최초 작성 (G5-1 L0) | Spec III Wave B-2 Task B2-8 박제 |
| 2026-04-22 | 필수 섹션 보강 (시작하기/주요 화면/자주 쓰는 작업/설정/제한사항/장애 대응) | G5-1 엔진 요건 충족 |
