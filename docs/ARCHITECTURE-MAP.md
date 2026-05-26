---
role: reference
audience:
  - newcomer
  - stakeholder
  - ai-agent
status: active
last_updated: 2026-04-12
last_commit: ca39c47
cross_refs:
  status_sot: null  # 과거 STATUS.md 제거됨
  roadmap: .planning/ROADMAP.md
  gsd_state: .planning/STATE.md
  project: .planning/PROJECT.md
  release_criteria: .planning/program/releases/RELEASE-CRITERIA.md
  scope_root: docs/product/scope/README.md
  scope_modules: docs/product/scope/modules/README.md
  l2_specs: docs/product/scope/modules/
  br_commits: docs/product/scope/modules/*/BR-COMMITS.md
  strategy_streams:
    - .planning/strategy/erp/ERP-MASTER-STRATEGY.md
    - .planning/strategy/groupware/GROUPWARE-MASTER-STRATEGY.md
    - .planning/strategy/ai/AI-STRATEGY.md
  reduction_roadmap: /Users/phil/.claude/plans/sparkling-growing-emerson.md
auto_regenerate: null  # 수동 갱신. 마일스톤 완료 시 last_commit·표 상태·arch-baseline 수치 갱신.
---

# OneERP 전체 구조 지도 (Architecture Map)

> **5분 안에 OneERP가 무엇이고·지금 어디이며·v1.0까지 어디로 가는지** 파악할 수 있는
> 단일 entry-point 문서입니다. 세부 수치·절차는 각 cross-ref 문서로 흘러갑니다.

## § 0. 이 문서의 위치

- **정본(SoT)**: 이 문서는 **SoT가 아닙니다**. 상태·수치는 `STATUS 문서(제거됨)`
  가 단일 진실 공급원이며, 본 문서는 그 내용을 **관측자용 지도로 재배치**합니다.
- **파생 관계**: `PROJECT.md` → `ROADMAP.md` → `STATUS.md` → (본 문서) → 독자. 즉
  본 문서는 체인의 말단 entry-point이지, 원본을 갱신하지 않습니다.
- **갱신 주기**: 수동. 마일스톤(Wave / M / Phase) 완료 시 frontmatter `last_commit`·
  § 4 표의 ⏳/🚧/✅ 토글·§ 5 arch-baseline 3 수치만 갱신하면 지속 가능.

---

## § 1. 도메인 지도 — 48 services, 13 카테고리, 4 성격

실측(`ls services/*/`): 13 카테고리 디렉토리 중 `deploy/`·`scripts/`·`tests/` 3개는
인프라/도구이고, 나머지 **10 도메인 카테고리 × 총 48 서비스**.

### 1-1. 카테고리별 요약

| 성격 | 카테고리(services/) | 서비스 수 | 서비스 목록 |
|---|---|---:|---|
| **ERP 트랜잭션** | `sales/` | 7 | selling, crm, pos, rental, reservation, subscriptions, ecommerce |
| **ERP 트랜잭션** | `scm/` | 5 | buying, stock, manufacturing, quality, maintenance |
| **ERP 트랜잭션** | `finance/` | 5 | accounting, payroll, expenses, consolidation, esg |
| **ERP 트랜잭션** | `hr/` | 3 | hr, lms, workreport |
| **ERP 트랜잭션** | `logistics/` | 3 | tms, fleet, advanced-planning |
| **ERP 트랜잭션** | `marketing/` | 3 | marketing, marketing-automation, gtm |
| **ERP 트랜잭션** | `assets/` | 2 | assets, plm |
| **ERP 트랜잭션** | `compliance/` | 2 | compliance, clm |
| **ERP 트랜잭션** | `ehs/` | 1 | ehs |
| **포털·통신 그룹웨어** | `portal/` | 4 | portal, messenger, mail, directory |
| **협업 도구** | `collab/` | 7 | calendar, documents, projects, wiki, board, knowledge, survey |
| **플랫폼·인프라** | `platform/` | 6 | gateway, rpa, iot, analytics, integration-hub, automation-orchestrator |
| **합계** |   | **48** |   |

성격별 집계: **ERP 31** · **그룹웨어 4** · **협업 7** · **플랫폼 6**.

### 1-2. 성격별 공통 런타임 특성

| 성격 | 상태 모델 | 주 통신 | 권한 단위 | 이벤트 패턴 |
|---|---|---|---|---|
| ERP 트랜잭션 | `DocStatus`(Draft/Submitted/Cancelled) + 감사 + 버전 | HTTP + Outbox | `*:*` Role/Tenant | 제출 시 `emit_doc_event()` |
| 그룹웨어 | 실시간·status/presence | NATS push + HTTP | Team·Channel 멤버십 | 알림 브로드캐스트 |
| 협업 | 문서·스레드·boards | HTTP + optimistic UI | 워크스페이스 | 변경 스트림 |
| 플랫폼 | 크로스컷팅(공용) | HTTP dispatch / event fan-out | 서비스 ID + 테넌트 | Publisher 허브 |

### 1-3. 모듈 명세

- **L2 스펙**: `docs/product/scope/modules/README.md`를 모듈 인덱스로 두고,
  각 모듈의 `L2-spec.md`와 `BR-COMMITS.md`를 하위 진입점으로 사용한다.
- **BR 매핑**: `docs/product/scope/modules/*/BR-COMMITS.md` (자동 동기화
  `scripts/docs/sync_br_codes.py`) — 16 BR prefix × 24 모듈 현재 집계.

---

## § 2. 공통 커널 & 프론트엔드

### 2-1. 공통 커널 `core/oneerp_core/`

**구조**(실측 `ls core/oneerp_core/`): 36 단일 모듈 + 3 서브 패키지.

| 층 | 파일 | 목적 |
|---|---|---|
| 기반 | `config.py`, `deps.py`, `db.py`, `cache.py`, `logging.py`, `telemetry.py` | 설정 DI, DB/Cache, 로깅·텔레메트리 |
| HTTP | `app_factory.py`, `auth.py`, `middleware.py`, `health.py`, `metrics.py` | FastAPI 앱 팩토리, 인증 미들웨어 |
| 문서·저장 | `document.py`(+`ApprovalMixin`·`SubmitTransitionMixin`), `repository.py`, `crud_router.py`, `models.py` | 표준 문서 계약, Repository, CRUD 라우터 |
| M1 확장 | `dto.py`, `error_catalog.py`, `idempotency.py`, `uow.py`, `service_base.py`, `testing.py` | ResponseDTO, ERR 14종, 멱등, UoW, DomainService, 테스트 유틸 |
| 유틸 | `line_items.py`, `naming.py`, `permissions.py`, `pricing.py`, `pricing_rule.py`, `route_helpers.py`, `entity_meta.py`, `audit.py`, `modules.py`, `errors.py`, `_app_utils.py` | 라인 합계·작명·권한·가격 규칙 |
| 서브 | `events/`, `valuation/`, `workflow/` | 이벤트 버스, 가치평가 전략, 워크플로우 |

### 2-2. 프론트엔드 `web/app/` (Next.js 16, App Router, Turbopack)

**실측**(`ls web/app/`):

| 경로 | 용도 |
|---|---|
| `(admin)/` | 관리자 콘솔 |
| `(modules)/` | 도메인 모듈 UI (sales/scm/finance/hr/portal 등) |
| `api/` | Next.js API 라우트 (프록시 계층) |
| `docs/` | 내부 문서 뷰어 |
| `login/`, `onboarding/`, `unauthorized/` | 인증·온보딩 |
| `permission-matrix/` | 권한 매트릭스 편집 UI |
| `tokens.css`, `globals.css`, `layout.tsx`, `page.tsx` | 디자인 토큰·전역 스타일·루트 |

**스택**: Radix UI + Tabler icons, Tailwind 4 (CSS-first), Biome, TanStack Query/Table,
React Hook Form + Zod, Recharts, @react-pdf/renderer, openapi-typescript(BE 계약 생성),
vitest + @testing-library/react.

### 2-3. 의존 방향

```
core/oneerp_core  ←─  services/{domain}/*  ←─  web/app/(modules)/
      (공통 커널)        (FastAPI 도메인)        (Next.js UI)
```

단방향. FE는 서비스 OpenAPI를 `openapi-typescript`로 타입 생성해 import.

---

## § 3. 이벤트 체인 — 58 schemas

### 3-1. 흐름

```
 ┌─ Document Submission (Route / Service)
 │      │
 │      ▼  emit_doc_event(type, payload)
 │  core/oneerp_core/events/bus.py
 │      │
 │      ▼  Repository.write_outbox()
 │  outbox collection (tenant 격리)
 │      │
 │      ▼  events/nats_publisher.py
 │  NATS JetStream
 │      │
 │      ▼  events/nats_consumer.py
 │  EventHandlerRegistry (서비스별)
 │      │
 │      ▼  handlers/*.py → HTTP dispatch
 └─ 후속 서비스 엔드포인트
```

### 3-2. 스키마·연결 현황

- **EventType 총 58개** (실측 `core/oneerp_core/events/schemas.py` 상수 카운트).
- **연결(wired) 5**: `approval_request.approved` (gateway→multi), `opportunity.converted`
  (crm→selling), `sales_order.submitted` (→ stock, **Wave 7 P0**), `purchase_receipt.submitted`
  (→ stock+accounting, **Wave 7 P0**), `journal_entry.posted` (payroll→accounting).
- **갭 53**: 58 − 5. Wave 7 이후 20+ 추가 목표.

### 3-3. 참고 파일

- `core/oneerp_core/events/schemas.py` — EventType 정의
- `core/oneerp_core/events/handler_registry.py` — 구독 등록
- `core/oneerp_core/events/handlers/` — approval/stock/journal 레퍼런스 구현
- `core/oneerp_core/events/bus.py` — 단일 `emit_doc_event()` API

---

## § 4. 로드맵 3-축 타임라인 ★ 핵심

OneERP는 **3개의 축**이 병행 운영됩니다:

1. **Wave** — 실행 단위(1 세션 ≒ 1 Wave). 누적 결과.
2. **M** — 복잡성·아키텍처 감축 로드맵(외부 `sparkling-growing-emerson.md`).
3. **Phase 1~7** — v1.0 릴리스 관점의 `.planning/ROADMAP.md` 정의.

STATUS.md에는 과거 Phase A~G 분류도 함께 존재합니다. 독자가 자주 혼동하므로 아래
**Rosetta 매핑표**를 먼저 보십시오.

### 4-1. Rosetta — Phase 1~7 ↔ Phase A~G ↔ Wave ↔ 현재 상태

| .planning/ROADMAP (Phase 1~7) — v1.0 관점 | STATUS 구 Phase A~G | Wave 대응 | 현재 |
|---|---|---|---|
| **Phase 1** 이벤트 체인 안정화 | Phase C FL1 | Wave 5-N 핸들러 + **Wave 7 P0 엔드포인트** | 🚧 진행 |
| **Phase 2** 핵심 운영 흐름 E2E (구매·경비·급여·제조) | Phase C FL2~FL4 | Wave 7 P0 후속 | ⏳ 대기 |
| **Phase 3** 협업·영업·전자결재 UI | Phase C FL5~FL7 + Phase D1 | 미지정 | ⏳ 대기 |
| **Phase 4** 대시보드·보고서·PDF | Phase D2~D3 | 미지정 | ⏳ 대기 |
| **Phase 5** 파일럿 운영 인프라 | Phase E I1~I4 | **Wave 7 P1** | 🚧 부분 |
| **Phase 6** 통합 QA·성능·보안 | Phase F T1~T4 | 미지정 | ⏳ 대기 |
| **Phase 7** 문서·튜토리얼 마감 | Phase G G1~G4 | 미지정 | ⏳ 대기 |

두 체계는 **동일한 작업을 다른 관점으로 본 것**입니다. 신규 커밋은 `(Wave N-X)` 접미사만
사용하고, Phase 1~7은 v1.0 릴리스 기준 충족 여부로 닫힙니다.

### 4-2. Wave 궤적 (완료 + 진행)

- **Wave 0** 감사 (Phase A Foundation 검증) — 완료
- **Wave 1~3** 13 엔진 긴급 fix + 전 서비스 깊이 (Phase B) — 완료
- **Wave 4~5** Order-to-Cash FL1 + 이벤트 체인 reference (Phase C FL1) — 완료
- **Wave 6** 2차 서비스 확장 — PR #54 (`d90aa38`) 완료
- **Wave 7** — 🚧 진행 중
  - **P0**: 5 이벤트 엔드포인트 실구현(`stock from-purchase-receipt`·
    `stock from-sales-order`·`accounting apply-to-ledger`·`accounting from-payroll-entry`·
    `gateway approval-actions/dispatch`) + sales-invoice PDF 실연동
  - **P1**: I3 관측성 실운영(Prometheus/Grafana) + I4 백업 복구 리허설

### 4-3. M 병행 스트림 (복잡성 감축)

로드맵: `/Users/phil/.claude/plans/sparkling-growing-emerson.md`

| M | 내용 | 상태 |
|---|---|---|
| **M0** | 8 PR: empty log 9,660 제거 · worktree 45→2 · STATUS.md SoT · Wave 컨벤션 · versions.toml · BR 자동매핑 · QUICKSTART · CI 게이트 5종 warn-only | ✅ 완료 |
| **M1** | 커널 보강 4 PR: 9 모듈 확장 · conftest 48개 공통화(-1,571 LOC) · 거대파일 헬퍼 · 3-layer 경계 검사 + baseline | ✅ 완료 |
| **M2** | selling SalesInvoiceService P1~P7 파일럿 | ✅ 완료 |
| **M3** | 도메인 확산 Wave A~D: SubmitMixinService 7 도메인 + Route→Service 분리. arch-baseline direct **244→236**, import **146→139** (이번 세션 8 커밋) | 🚧 진행 |
| **M4** | 전체 strict (ruff/ty/biome) + FE-BE OpenAPI diff 게이트 승격 | ⏳ 대기 |

### 4-4. v1.0 파일럿 릴리스 기준

출처: [`.planning/program/releases/RELEASE-CRITERIA.md`](../.planning/program/releases/RELEASE-CRITERIA.md).

**최소 기준 6**:
1. 핵심 ERP 흐름 자동화 테스트 통과
2. 전자결재 및 주요 사용자 UI 동작 확인
3. 배포 및 관측성 검증 완료
4. 복구 런북 검증 완료
5. 성능·보안 점검 결과 기록
6. 사용자 시나리오/매뉴얼/튜토리얼 현행화

**4 Release Gate**:
- **Product**: 핵심 사용자 흐름이 문서와 동일 / ERP↔그룹웨어 경험 연결 / 보고서·대시보드·결재 화면이 "제품 같다"는 인상
- **Engineering**: 루트 workflow(`.gitea/workflows/quality-gates.yml`) → `./scripts/ci/run.sh` → `./scripts/ci/run_contract_tests.sh` 기준선 / API·UI E2E 전 통과
- **Operations**: 배포·관측성·복구 경로 재현 / 장애 시나리오 최소 1회 점검
- **Pilot**: 파일럿 고객 역할별 시연 준비 / 데이터 입력→승인→조회→출력 무중단

**Blocking 3**:
- 결재·회계·재고 핵심 흐름 중 하나라도 수동 개입 없이 끝까지 검증 불가
- 운영 문서와 실제 배포 절차 불일치
- KPI/리스크 문서가 최신 기준과 어긋남

현재 release blocker는 `web/lib/types/generated/gateway.ts` 계열 generated drift와 기존 FE lint debt다.

### 4-5. 현재 → v1.0 최단 경로

```
지금 (Wave 7 P0 / M3 진행)
   │
   ▼  ① Wave 7 P0 완료 (5 엔드포인트)               → Phase 1 만족
   │  ② Phase 2 E2E (P-to-P · E-to-P · Pay-to-Acct · M-to-S)
   │  ③ Phase 3 CRM→Selling + 전자결재 UI          ← 그룹웨어 스트림 첫 연동
   │  ④ Phase 4 대시보드·PDF
   │  ⑤ Phase 5 인프라 검증 (Wave 7 P1 흡수)
   │  ⑥ Phase 6 통합 QA + M4 strict                ← M 스트림 수렴점
   │  ⑦ Phase 7 문서·파일럿 검증
   ▼
v1.0 파일럿 출시
```

M 스트림은 Phase 6(품질 게이트)에서 Phase 1~7 스트림과 수렴합니다. 따라서 **Wave 7
완료 전까지는 Phase 1~7과 M 스트림이 병행**되며, 병행 가속이 이번 세션의 작업 패턴.

---

## § 5. 크로스컷팅 — gateway 61 엔티티 분해 후보

`services/platform/gateway/`는 ERP와 그룹웨어 양쪽이 공유하는 **크로스컷팅 허브**
(61 엔티티). 현재는 단일 서비스지만 향후 분해 후보가 명확합니다.

### 5-1. 혼합 기능 표

| 기능 | 현재 위치 | 성격 | 분해 권고 | 시점 |
|---|---|---|---|---|
| 전자결재 (Approval) | gateway | 플랫폼 (ERP+그룹웨어 공용) | **`platform/approval/` 독립 후보** | Phase 3 이후 |
| 알림 (Notifications) | gateway | 플랫폼 | **`platform/notification/` 독립 후보** | Phase 5 이후 |
| 문서 (Document) | gateway | ERP+컴플라이언스 | gateway 유지 또는 `platform/document/` | v1.1 |
| 포털 UI gateway | gateway | 그룹웨어 UI↔ERP 데이터 | 현행 유지 권장 | — |
| API Gateway (순수 프록시) | gateway | 플랫폼 | gateway 계속 | — |

**비범위 주석**: 실제 분해는 **본 지도 문서가 아닌 별도 PR**. 본 § 5는 **식별·로드맵상
위치 지정**만.

### 5-2. arch-baseline 감축 추세 (M3 진행)

출처: `.arch-baseline.json` (실측 2026-04-12).

| 규칙 | 기준(M1) | 현재 | Δ |
|---|---:|---:|---:|
| OE002-route-direct-repo-instantiate | 244 | **236** | -8 |
| OE002-route-import-repository | 146 | **139** | -7 |
| OE004-models-define-create-dto | 1,125 | 1,125 | 0 (미착수) |

**다음 타깃 route 파일** (STATUS.md Wave D 섹션 참고):
`quotations` / `sales_partners` / `sales_invoices` / `delivery_notes` / `sales_orders` / `price_lists`.

---

## § 6. 문서 SoT 체인 재확인 + 정비 권고

### 6-1. 현재 체인

```
.planning/PROJECT.md   (v1.0 파일럿 정의)
      │
      ▼
.planning/ROADMAP.md   (Phase 1~7)
      │
      ├── .planning/strategy/{erp,groupware,ai}/    (3 스트림 비전·전략)
      ├── .planning/program/{milestones,metrics,releases,risks,pilot}/
      ├── docs/product/scope/README.md
      ├── docs/product/scope/modules/README.md
      └── docs/product/scope/modules/*/{L2-spec,BR-COMMITS}.md   (112 명세)
      │
      ▼
STATUS 문서(제거됨)         (SoT · 현 Wave / M / arch-baseline / 최근 커밋)
      │
      ├── .planning/STATE.md   (GSD 슬래시 명령 frontmatter state — 상호 cross-ref)
      └── /Users/phil/.claude/plans/sparkling-growing-emerson.md   (M0~M4 외부)
      │
      ▼
docs/ARCHITECTURE-MAP.md  (← 본 문서: 관측자용 entry-point)
      │
      ▼
독자 / AI 에이전트 / 이해관계자
```

### 6-2. 식별된 중복·정비 권고

1. **Wave 7 P0 3중 기재** (STATUS.md 여러 섹션에 중복) — STATUS.md 29~42줄 한 곳에
   정본화하고, 다른 언급은 cross-ref로 축약. 본 문서 § 4-2는 요약만 유지.
2. **M0~M4 외부 로드맵 참조** — `sparkling-growing-emerson.md`가 프로젝트 외부 경로에
   있어 fresh 보장 어려움. v1.1 시점에 `docs/archive/roadmap-m0-m4-reduction.md`로
   내재화 권고.
3. **Phase A~G ↔ Phase 1~7 명명 불일치** — 본 § 4-1 Rosetta 매핑표로 **영구 해소**.
   신규 커밋은 Wave 체계만 사용하는 것이 현행 정책(STATUS.md 71줄).

### 6-3. 본 문서의 갱신 규칙

- frontmatter `last_commit` 은 STATUS.md 값을 **1:1 복사**하지 말고, 본 지도를
  갱신한 시점의 커밋으로 독립 기록.
- § 4-2/4-3 표의 ⏳/🚧/✅ 토글만 바꾸면 충분. 세부 수치·커밋 id는 STATUS.md로 링크.
- § 5-2 arch-baseline 3 수치는 `.arch-baseline.json` 현재 값으로 월 1회 갱신.

---

## 한 줄 요약

OneERP = **48 FastAPI 서비스**(ERP 31 + 그룹웨어 4 + 협업 7 + 플랫폼 6) · **1 공통 커널**
(`core/oneerp_core`) · **1 Next.js 16 앱**(`web/app`) · **58 EventType** 이벤트 버스(5
wired) · **Phase 1~7 / Wave 0~7 / M0~M4** 3-축 로드맵으로 **v1.0 파일럿 출시**를
향하는 대규모 모노레포.
