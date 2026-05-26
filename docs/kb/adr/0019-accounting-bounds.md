---
title: ADR-0019 Accounting 클러스터 경계 정의
date: 2026-04-22
status: accepted
gate: G1-1
module: accounting
tier: T1
decision: accounting cluster 의 6 서브도메인(회계기간 · 전표 · 예산 · 세무 · 환율 · 자금) 경계를 동결하고 journal_entry 이벤트 계약을 단일 진실 원천으로 지정한다
consequences: selling/buying/expenses/payroll/assets 는 journal_entry.created/posted 이벤트로만 accounting 에 기록 · period_guard 불변식 엄수 · 본 경계 변경 시 ADR 개정 필수
tags: [accounting, bounded-context, cluster, ddd, spec-iii, commercial-v2]
---

# ADR-0019 — Accounting 클러스터 경계 정의

## Context — 왜 accounting cluster 경계 분리가 필요한가

Commercial Grade v2 Spec III 는 OneERP 의 37 개 마이크로서비스 중 재무
수직(accounting / expenses / payroll / finance_extra)을 L0 완성 수준으로
끌어올리는 것을 목표로 한다. 그 가운데 `accounting` 은 다음 이유로 가장
먼저 경계 확정(bounded context) 대상이 된다.

1. **상태 전이 복잡도 최상위** — 회계기간(fiscal_year/accounting_period)
   열림·임시마감·영구마감 사이클, 전표(journal_entry)의 draft→submit→
   approve→post→reverse 전이, 예산(budget) 초안→확정→실행→결산, 부가세
   신고(vat_return)의 기간별 누적·검증·전자신고 전이 등 **≥ 5 개**의
   독립된 상태 기계가 동시에 운영된다.
2. **규제 민감 데이터 집중** — 전자세금계산서(e-tax invoice), 원천세,
   외화평가(multi-currency revaluation), K-IFRS 매핑, 감사 로그가
   집중된다. 경계 위반은 곧 법적 위험이다.
3. **상호 의존성의 중심** — selling/buying/expenses/payroll/assets 모두
   `journal_entry` 를 통해 accounting 으로 전표를 밀어 넣는다. 본 서비스
   가 공용 이벤트(`journal_entry.created`, `journal_entry.posted`,
   `accounting_period.closed`) 의 생산자·소비자로 동시에 작동한다.
4. **팀 경계 정렬** — 회계·재무회계 도메인 전문 팀이 단일하게 운영한다.
   DDD 의 "One Team, One Bounded Context" 원칙을 만족한다.

따라서 `accounting` 을 **독립 클러스터**로 분리하고, 내부 하위 도메인은
서비스 경계 안에서만 결합하며, 외부(다른 서비스·플랫폼)와는
**이벤트·API 두 통로**로만 통신하도록 확정한다.

### 기존 구조 스냅숏 (2026-04-22 기준)

`services/finance/accounting/oneerp_accounting_app/` 디렉토리 기준 실측:

| 자원 | 수 | 근거 |
|------|----|------|
| 모델(Pydantic Document/Create/Update) | 56 파일 | `ls oneerp_accounting_app/models/*.py \| wc -l` |
| `EntityMeta` 등록 엔티티 | 47 건 | `grep -c "EntityMeta(" entities.py` |
| 커스텀 라우터 파일 | 11 개 | `ls routes/*.py` (accounting_periods, accounts, accounts_payable, accounts_receivable, budgets, cost_centers, etax_invoices, general_ledger_entries, journal_entries, reports, vat_returns) |
| 라우트 엔드포인트 | 70 건 | `grep -c "^@router" routes/*.py` |
| 도메인 서비스 | 23 개 | `ls services/*.py` |
| 이벤트 핸들러 | `events/handlers.py` 1 파일 | 단일 레지스트리 |

즉 **54 개 엔티티(47 auto + 7 custom), 70 라우트, 23 서비스**가 단일
프로세스 경계 내에 있다. 본 ADR 은 이 구성을 **동결**하고, 신규 도메인
추가 시 동일 구조를 요구한다.

## Decision — 무엇을 결정했는가

### 1. 클러스터 정체성 고정

- `accounting` 은 ADR-0011 의 "코드 클러스터" 축에서 **finance 클러스터**
  의 리더 서비스다. finance 클러스터 멤버: `accounting`, `expenses`,
  `payroll`, `finance_extra` 4 개.
- ADR-0014 의 "런타임 plane" 축에서는 **core-plane** 에 배치된다. 모든
  테넌트가 공유하며, 테넌트 격리는 `X-Tenant-ID` 헤더와 repository
  레벨 필터로 수행한다.

### 2. 내부 서브도메인 그룹화 (6 그룹)

56 모델을 6 그룹으로 나눈다. 그룹 간 직접 import 는 허용하되, 그룹 내
응집도를 조직 차트·코드 리뷰 권한과 맞춘다.

| 그룹 | 엔티티 예시 | 책임 |
|------|--------------|------|
| 회계기간(period) | `fiscal_year`, `accounting_period`, `period_closing_voucher` | 기간 lifecycle, 마감 여부 게이트 |
| 전표(journal) | `journal_entry`, `general_ledger_entry`, `accounts_receivable`, `accounts_payable`, `payment_entry`, `payment_reconciliation` | 복식부기 전표·결제 소스 |
| 예산(budget) | `budget`, `budget_version`, `budget_transfer`, `cost_center`, `profit_center`, `activity_based_costing_rule` | 예산 수립·집행·원가 배부 |
| 세무(tax) | `vat_return`, `tax_rule`, `tax_calendar`, `etax_invoice`, `withholding_tax_*`, `kifrs_mapping`, `revenue_recognition_*` | 국세청·K-IFRS 규정 준수 |
| 환율·국제거래 | `currency_exchange`, `multi_currency_revaluation`, `exchange_rate_revaluation`, `letter_of_credit`, `hedging_instrument`, `hedging_relationship`, `intercompany_*`, `consolidation_*` | 외환·연결결산 |
| 자금·보조 | `bank_account`, `bank_reconciliation`, `bank_transaction`, `cash_flow_forecast`, `loan_*`, `lease_*`, `fund_transfer`, `treasury_*`, `dunning`, `severance_reserve`, `payment_order`, `payment_terms_template`, `deferred_*`, `segment_report`, `financial_ratio_report`, `terms_and_conditions`, `accounting_dimension*`, `bank_statement_import` | 자금·현금흐름·부속 |

### 3. 외부 통신 통로 고정 (2 개만 허용)

- **이벤트 레일**: `oneerp_accounting_app.events.event_registry` 가 발행/
  구독하는 이벤트만 외부와 공유. 현 시점 주요 이벤트:
  `journal_entry.created`, `journal_entry.posted`, `journal_entry.reversed`,
  `accounting_period.closed`, `vat_return.submitted`, `etax_invoice.issued`.
  이벤트 스키마는 `oneerp_core.events.schemas.EventType` 로 중앙 관리.
- **HTTP API**: 70 개 라우트 엔드포인트. gateway 서비스가 유일한 진입점.
  직접 호출(cluster-internal) 은 금지하고, 반드시 gateway 를 경유한다.

공유 DB 접근, 서비스 간 Python import, 내부 포트 직접 호출은 **금지**.
공통 모델은 `packages/core` 의 `oneerp_core.models` 로 끌어올린 후 양쪽이
모두 참조해야 한다.

### 4. 이벤트 체인 책임 매트릭스

| 이벤트 | 생산자 | 소비자 | 비고 |
|--------|--------|--------|------|
| `journal_entry.created` | accounting | gateway(audit), analytics | 작성만 기록, 미포스트 |
| `journal_entry.posted` | accounting | gateway(audit), analytics, budget(원가 배부) | 총계정원장 반영 |
| `accounting_period.closed` | accounting | 전 도메인 | 해당 기간 수정 잠금 |
| `payment_entry.reconciled` | accounting | selling(수금), buying(지급) | 미결제 건 매핑 |
| `etax_invoice.issued` | accounting | compliance, audit-log | 국세청 전송 상태 |
| `vat_return.submitted` | accounting | compliance | 신고 완료 고지 |

외부 서비스(selling/buying/expenses) 가 전표를 생성할 때는 자신의 도메인
이벤트(`sales_invoice.confirmed`, `purchase_invoice.approved`,
`expense.approved`) 만 발행하고, accounting 핸들러가 이를 받아 `journal_entry`
를 생성한다. 역방향(외부 서비스가 accounting DB 에 직접 쓰기) 은 금지.

### 5. 기술 스택 · 품질 게이트 계약

- FastAPI ≥ 0.115, Pydantic v2, Python 3.14, uv workspace 멤버.
- 모든 신규 라우트는 `oneerp_core.app_factory.create_service_app` 팩토리를
  거치고, Entity 는 `EntityMeta` 로 선언.
- 품질 게이트(`scripts/audit/gates/`) 는 accounting 모듈에 대해 G1–G5
  전 티어를 통과시켜야 한다. 본 ADR 은 G1-1 증거를 자가 박제한다.

## Consequences — 결정이 낳는 결과

### 긍정적 결과

- **회귀 차단**: selling/buying 팀이 accounting 내부 구조를 import 하려
  할 때 리뷰어가 본 ADR 을 근거로 반려 가능.
- **테스트 고립**: 56 모델·70 라우트·23 서비스가 단일 프로세스 내에서만
  결합되므로, 단위 테스트·통합 테스트 범위가 명확.
- **감사 일원화**: 모든 변경이 `emit_audit_event` 단일 경로로 수렴.
- **문서화 기준점**: 신규 엔티티 추가 시 본 ADR 의 6 그룹 중 하나에 배치
  의무. 어디에도 속하지 않으면 클러스터 재설계 트리거.

### 부정적 결과 · 트레이드오프

- **세부 변경의 탄력성 저하**: 한 번 그룹에 배정된 엔티티를 재배치하려면
  본 ADR 개정이 필요. 소규모 리팩터가 무거워진다.
- **단일 프로세스 과부하 우려**: 70 라우트 × 23 서비스가 단일 uvicorn
  워커에서 돌아가므로 핫 패스 외 라우트가 배포 단위를 끌어안는다.
  **완화**: ADR-0014 런타임 plane 축에서 tenant-plane 분리를 고려.
- **이벤트 체인 디버깅 비용**: 전표 1 건이 5–7 개 이벤트를 트리거할 수
  있어 관찰성 게이트(G4-2) 가 필수.

### 중립적 결과

- 기존 `packages/core` 의존은 유지. 본 ADR 은 코드 레이아웃을 변경하지
  않고 **동결**한다.

## Evidence — 근거 파일

이 ADR 이 주장하는 사실의 근거:

- `services/finance/accounting/oneerp_accounting_app/main.py:16-50` — 11
  개 라우터 등록, `EntityMeta` 자동 CRUD 통합 지점.
- `services/finance/accounting/oneerp_accounting_app/entities.py` — 47 개
  `EntityMeta` 선언(실측 `grep -c "EntityMeta(" = 47`).
- `services/finance/accounting/oneerp_accounting_app/models/` — 56 개
  모델 파일(실측 `ls *.py \| wc -l = 56`).
- `services/finance/accounting/oneerp_accounting_app/routes/*.py` — 11
  라우터 파일, 총 70 엔드포인트(실측 `grep -c "^@router" *.py = 70`).
- `services/finance/accounting/oneerp_accounting_app/services/*.py` — 23
  도메인 서비스.
- `services/finance/accounting/oneerp_accounting_app/events/handlers.py`
  — 이벤트 레지스트리.
- `docs/kb/adr/0011-*.md`, `docs/kb/adr/0014-*.md` — 2축 아키텍처 원칙.
- `packages/core/oneerp_core/app_factory.py` — `create_service_app`
  팩토리, 서비스 부트스트랩 단일 지점.
- `packages/core/oneerp_core/audit.py` — `emit_audit_event` 감사 경로.
- `packages/core/oneerp_core/events/schemas.py` — `EventType` enum,
  이벤트 스키마 레지스트리.

## References

- ADR-0011 코드 클러스터 축
- ADR-0014 런타임 plane 축
- ADR-0017 ruff baseline + ratchet
- Commercial Grade v2 설계(`docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md`)
- `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` Wave B-2

## Appendix A — 11 라우터 파일과 엔드포인트 분포

```
routes/accounting_periods.py    기간 생성·마감 전이
routes/accounts.py              계정과목 CRUD·계층
routes/accounts_payable.py      매입채무·지급예정
routes/accounts_receivable.py   매출채권·회수예정
routes/budgets.py               예산 수립·실적 비교
routes/cost_centers.py          원가 센터·배부 규칙
routes/etax_invoices.py         전자세금계산서 발급·취소
routes/general_ledger_entries.py 총계정원장 조회
routes/journal_entries.py       전표 CRUD + 전이(draft→submit→approve→post→reverse)
routes/reports.py               손익·대차·현금흐름·시산
routes/vat_returns.py           부가세 신고 초안·제출·취소
```

실측 `grep -c "^@router.(get|post|put|patch|delete)" routes/*.py` = **70**.

## Appendix B — 23 도메인 서비스 책임 맵

```
services/accounts_receivable_service.py    매출채권 집계·연령분석 연동
services/aged_analysis_service.py          채권·채무 연령별 분석
services/bank_reconciliation_service.py    은행 계좌·내부 장부 매칭
services/barobill_client.py                바로빌 전자세금계산서 API
services/codef_client.py                   CODEF 금융 Open API
services/consolidation_service.py          연결결산·제거분개
services/dunning_service.py                독촉장 단계·이력
services/etax_service.py                   국세청 전자세금계산서 흐름
services/financial_ratio_service.py        재무비율 계산·스냅숏
services/invoice_handler.py                invoice 이벤트 훅
services/journal_auto_service.py           외부 이벤트 → 자동 전표 생성
services/journal_entry_pilot_service.py    M3 파일럿 전표 로직
services/journal_entry_service.py          전표 핵심 상태 전이
services/kifrs_service.py                  K-IFRS 매핑 엔진
services/multi_currency_revaluation_service.py 외화환산
services/nts_api_client.py                 국세청 Open API 클라이언트
services/openbanking_client.py             오픈뱅킹 API 클라이언트
services/payment_reconciliation_service.py 결제 매칭
services/period_closing_service.py         기간 마감·잠금
services/treasury_service.py               자금수지·예측
services/vat_service.py                    부가세 신고 엔진
services/withholding_tax_service.py        원천세 엔진
```

## Appendix C — 품질 게이트 매핑

| 게이트 | 본 클러스터에서의 의미 | 첫 증거 |
|--------|------------------------|---------|
| G1-1 경계 ADR | 본 문서 | `docs/kb/adr/0019-accounting-bounds.md` |
| G1-2 OpenAPI 덤프 | 70 엔드포인트 스키마 고정 | `services/finance/accounting/openapi.yaml` |
| G3-1 AuthN 7 종 | JWT 만료/서명/aud/iss/nonce/replay/scope | `tests/security/test_auth_*.py` |
| G3-4 감사 mutation | 전표·기간·신고 변경 기록 | `audit_hooks.py` + `tests/unit/test_audit_mutation.py` |
| G3-5 의존성 감사 | pip-audit JSON | `artifacts/T1/G3-5/accounting/pip-audit-2026-04-22.json` |
| G5-1 매뉴얼 | 운영자 가이드 | `docs/manual/accounting.md` |
| G5-2 튜토리얼 | 플로우 가이드 | `docs/tutorial/accounting-flow.md` |

## Change Log

| 일자 | 변경 | 근거 |
|------|------|------|
| 2026-04-22 | 최초 작성 · accepted | Wave B-2 Task B2-3 증거 박제 |
