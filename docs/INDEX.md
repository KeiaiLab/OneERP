# OneERP 문서 인덱스

> 마지막 갱신: 2026-04-14

---

## 진입 정본 (Entry SoT)

| 문서 | 역할 | 설명 |
|------|------|------|
| **[ARCHITECTURE-MAP.md](ARCHITECTURE-MAP.md)** | 정본 | **전체 구조 지도** — 48 서비스·이벤트 체인·Wave/M/Phase 3-축 로드맵·v1.0 경로 entry-point |
| **[product/roadmap/README.md](product/roadmap/README.md)** | 정본 | **통합 상용화 로드맵** — 4축 좌표계(Phase·Wave·Stream·Plane) × 2층 독자. Executive 30초 랜딩 + 실행 레이어 분리 |
| **STATUS.md** | 정본 | 프로젝트 상태 SoT — 현재 Wave / M / arch-baseline / 최근 커밋 |

---

## 문서 역할 규칙

| 역할 | 의미 |
|------|------|
| 정본 | 현재 기준으로 가장 신뢰해야 하는 문서 |
| 보조 | 정본을 탐색하거나 실행하는 데 도움을 주는 문서 |
| 참고 | 특정 주제의 확장 설명 또는 비교 자료 |
| 보관 | 과거 분석/이력 보존용 문서. 최신 판단 기준으로 직접 사용하지 않음 |

정리 원칙:

- 사용자-facing 최상위 정본은 `tutorials/`와 `user-manual/`이다.
- `product/scope/modules/`, `product/scope/comparisons/`, `product/scope/08-amaranth10-gap-analysis.md` 계열은 내부 근거 문서로 사용한다.
- 구현 실행 기준은 `IMPLEMENTATION-MASTER-PROMPT`를 우선하고, 서비스 구조/레이어 규칙은 `MASTER-DOC-GUIDE`를 내부 기준으로 사용한다.
- 운영 정책 정본은 `infra/ops/`, 모듈별 runbook은 `ops/`이다.
- 스토리별 visual-log 체크리스트는 `superpowers/visual-log/checklists/`에 보존한다.

---

## product/ — 제품 범위·분석·계획

### 제품 전략 문서

| 문서 | 상태 | 설명 |
|------|------|------|
| **product/COMPETITIVE-GAP-ANALYSIS.md** | **신규** | **경쟁사 Gap 분석 종합 보고서** |
| product/IMPLEMENTATION-GAP-REPORT.md | 신규 | 구현 갭 분석 보고서 |
| product/PROJECT-INTEGRITY-REPORT.md | 신규 | 서비스/문서 무결성 검증 보고서 |
| ../.planning/ROADMAP.md | 확정 | OneERP Capability Expansion 실행 정본 |
| product/plans/2026-03-26-government-grant-business-plan.md | 확정 | 정부지원사업 사업계획서 초안 |
| product/plans/oneerp-full-implementation-prompt.md | 확정 | 과거 전체 구현 프롬프트 (참고) |

### product/scope/ — 범위 정의·분석 문서

| 문서 | 상태 | 설명 |
|------|------|------|
| product/scope/MASTER-DOC-GUIDE.md | 확정 | 구조/레이어/구현 관례 내부 기준 |
| **product/scope/MODULE-SERVICE-MAP.md** | **신규** | **모듈-서비스 매핑 테이블** |
| product/scope/RALPH-PROMPT.md | 확정 | Ralph용 래퍼 프롬프트 |
| product/scope/entity-aliases.yaml | 확정 | 엔티티 별칭 정의 |
| product/scope/00-source-of-truth.md | 초안 | Capability 카탈로그 소스 오브 트루스 |
| product/scope/01-module-catalog.csv | 초안 | 모듈/기능 카탈로그 (CSV) |
| product/scope/02-gap-analysis.md | 초안 | 경쟁사 capability gap와 우선순위 근거 |
| product/scope/03-e2e-scenarios.md | 초안 | E2E 핵심 시나리오 |
| product/scope/03-phase-roadmap.md | 초안 | Capability 구현 phase 로드맵 |
| product/scope/04-competitive-capability-matrix.md | 초안 | 경쟁사 capability 매트릭스 |
| product/scope/05-competitive-analysis-korea.md | 초안 | 국내 경쟁사 분석 |
| product/scope/06-competitive-analysis-global.md | 초안 | 글로벌 경쟁사 분석 |
| product/scope/07-oneerp-feature-inventory.md | 초안 | OneERP 기능 인벤토리 |
| product/scope/08-amaranth10-gap-analysis.md | 초안 | Amaranth10 Gap 분석 |
| product/scope/09-composable-saas-strategy.md | 초안 | Composable SaaS 전략 |
| product/scope/IMPLEMENTATION-MASTER-PROMPT.md | 초안 | 실행 프롬프트 정본 |

### product/scope/comparisons/ — 클러스터별 비교 분석 (7개)

| 문서 | 설명 |
|------|------|
| comparisons/00-comparison-index.md | 비교 분석 인덱스 |
| comparisons/CL1-finance-accounting.md | CL1: 재무/회계 |
| comparisons/CL2-hr-payroll.md | CL2: 인사/급여 |
| comparisons/CL3-manufacturing-quality.md | CL3: 제조/품질 |
| comparisons/CL4-sales-crm.md | CL4: 판매/CRM |
| comparisons/CL5-approval-collaboration.md | CL5: 전자결재/협업 |
| comparisons/CL6-system-admin.md | CL6: 시스템/관리 |

### product/scope/competitors/ — 경쟁사 프로파일 (18개)

- **ERP** (7개): douzone-erp10, erpnext, ms-dynamics365-bc, odoo, oracle-netsuite, sap-s4hana, youngrimwon-ksystem
- **그룹웨어** (10개): douzone-gw, flow, google-workspace, hancom-ncloud, jandi, kakao-work, ms365, naver-works, slack-salesforce, youngrimwon-gw
- competitors/00-competitor-index.md — 경쟁사 인덱스

### product/scope/modules/ — 모듈별 상세 문서 (56개 디렉토리)

각 디렉토리에 L1(개요), L2(사용자 시나리오), L3(API 명세) 문서가 포함됩니다.
상세 링크: modules/INDEX.md

| 그룹 | 모듈 |
|------|------|
| 재무/회계 | accounting, advanced-accounting, consolidation, treasury |
| 인사/급여 | hr-core, payroll, leave-management, shift-management, recruitment, performance-mgmt |
| 판매/CRM | selling, crm, pos, rental, subscriptions, e-commerce |
| 구매/재고 | buying, stock, wms |
| 제조/품질 | manufacturing, quality, plm, advanced-planning, maintenance |
| 자산/경비 | assets, expenses, fleet |
| 프로젝트 | projects |
| 분석 | analytics, esg, ehs, iot |
| 마케팅 | marketing, marketing-automation, gtm |
| 전자결재/협업 | approvals, documents, calendar, internal-mail, internal-messenger, internal-wiki, board-notices, survey-poll, work-report, knowledge, company-portal, organization-directory |
| 시스템 | integration-hub, rpa, tms, clm, compliance, korean-compliance, lms, field-service, resource-reservation |

---

## engineering/ — 아키텍처·데이터·UI·CI

| 문서 | 상태 | 설명 |
|------|------|------|
| [engineering/standards.md](engineering/standards.md) | 진행중 | 개발 표준 (BE: ruff/ty, FE: biome) |

### engineering/architecture/ (9개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [architecture/api-standards.md](engineering/architecture/api-standards.md) | 진행중 | API 표준 |
| [architecture/repo-structure-rules.md](engineering/architecture/repo-structure-rules.md) | 확정 | 저장소 구조/네이밍/소유권 정본 |
| [architecture/event-contracts.md](engineering/architecture/event-contracts.md) | 신규 | 이벤트 schema_version / 호환성 계약 |
| [architecture/authz.md](engineering/architecture/authz.md) | 진행중 | 인증/권한 |
| [architecture/be-context-map.md](engineering/architecture/be-context-map.md) | 진행중 | BE 컨텍스트 맵 |
| [architecture/i18n.md](engineering/architecture/i18n.md) | 초안 | 국제화(i18n)/현지화(l10n) |
| [architecture/migration-contracts.md](engineering/architecture/migration-contracts.md) | 신규 | expand/migrate/contract 및 deploy validate 계약 |
| [architecture/multitenancy.md](engineering/architecture/multitenancy.md) | 진행중 | 멀티테넌시 |
| [architecture/shared-libraries.md](engineering/architecture/shared-libraries.md) | 진행중 | 공통 라이브러리 분리 기준 |
| [architecture/refactor-boundaries.md](engineering/architecture/refactor-boundaries.md) | 초안 | 대규모 리팩토링 경계 가드레일 |

### engineering/ci/ (2개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [ci/quality-gates.md](engineering/ci/quality-gates.md) | 강제 | CI 품질 게이트 (BE + FE 통합) |
| [ci/test-strategy.md](engineering/ci/test-strategy.md) | 진행중 | 테스트 전략 |

### engineering/data/ (6개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [data/audit-log-spec.md](engineering/data/audit-log-spec.md) | 진행중 | 감사로그 스펙 |
| [data/er-entities.md](engineering/data/er-entities.md) | 초안 | 도메인 핵심 엔티티 |
| [data/ferretdb.md](engineering/data/ferretdb.md) | 진행중 | 데이터 레이어: FerretDB |
| [data/ferretdb-compat-matrix.md](engineering/data/ferretdb-compat-matrix.md) | 초안 | FerretDB 호환성 매트릭스 |
| [data/indexing-strategy.md](engineering/data/indexing-strategy.md) | 초안 | 인덱스 전략 |
| [data/perf-benchmarks.md](engineering/data/perf-benchmarks.md) | 초안 | 성능 벤치마크 |

### engineering/ui/ (7개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [ui/design-system.md](engineering/ui/design-system.md) | 진행중 | FE Design System |
| [ui/tokens.md](engineering/ui/tokens.md) | 초안 | Design Tokens |
| [ui/components.md](engineering/ui/components.md) | 초안 | 컴포넌트 카탈로그 |
| [ui/page-templates.md](engineering/ui/page-templates.md) | 초안 | 페이지 템플릿 |
| [ui/accessibility.md](engineering/ui/accessibility.md) | 초안 | 접근성 기준 |
| [ui/crud-patterns.md](engineering/ui/crud-patterns.md) | 진행중 | CRUD UI 패턴 가이드 |
| [ui/references.md](engineering/ui/references.md) | 확정 | UI 레퍼런스(오픈소스) 선정 |

---

## generated/ — 자동 생성 ERD (47개)

`erd-{모듈명}.md` 형식. 모듈: accounting, advanced-planning, analytics, assets, board, buying, calendar, clm, compliance, consolidation, crm, directory, documents, ecommerce, ehs, esg, expenses, fleet, gateway, gtm, hr, integration-hub, iot, knowledge, lms, mail, maintenance, manufacturing, marketing, marketing-automation, messenger, payroll, plm, portal, pos, projects, quality, rental, reservation, rpa, selling, stock, subscriptions, survey, tms, wiki, workreport
전체 링크: [generated/INDEX.md](generated/INDEX.md)

---

## governance/ — ADR·팀 운영

### governance/adr/ (재구축 진행 중 — 2026-04-13 전면 폐기 후 재작성)

> 기존 ADR-0004/0006/0007/0010/0011/0014는 본 일자에 모두 삭제됐다.
> "상용 제품 수준 격상"을 최우선 과제로 ADR-0001~0012를 신규 작성 중이다.
> 진척 상황은 표 하단 "작성 예정" 참조.

| 문서 | 설명 |
|------|------|
| [adr/0000-template.md](governance/adr/0000-template.md) | ADR 템플릿 (강화 버전) |
| [adr/0001-commercial-grade-definition.md](governance/adr/0001-commercial-grade-definition.md) | 상용 제품 정의(DoD)와 23개 통과 게이트 |
| [adr/0002-commercialization-waves.md](governance/adr/0002-commercialization-waves.md) | 모듈 상용화 웨이브 분류 방법론 |
| [adr/0003-test-strategy-and-coverage-gates.md](governance/adr/0003-test-strategy-and-coverage-gates.md) | 4계층 테스트 피라미드·라벨별 커버리지 임계값·PR patch coverage 게이트 |
| [adr/0004-database-standard-ferretdb.md](governance/adr/0004-database-standard-ferretdb.md) | FerretDB 채택 + 사용 화이트리스트 + 데이터 등급 + 5개 출구 트리거 |
| [adr/0005-multitenancy-isolation-tiers.md](governance/adr/0005-multitenancy-isolation-tiers.md) | 3단 격리 등급(Shared/Schema/Dedicated) + 강제 메커니즘 + 무중단 승급 |
| [adr/0006-authorization-model-rbac-abac.md](governance/adr/0006-authorization-model-rbac-abac.md) | RBAC 코어 + ABAC 보강 · 결정 함수 · 모듈별 권한 매트릭스 의무 |
| [adr/0007-api-stability-versioning-contract.md](governance/adr/0007-api-stability-versioning-contract.md) | URL 메이저 버전 · breaking 자동 차단 · 6개월 deprecation · 안정성 등급 |
| [adr/0008-observability-baseline.md](governance/adr/0008-observability-baseline.md) | OTel + Prometheus + JSON 로그 + Audit 4축 + 의무 메트릭/로그/trace 카탈로그 |
| [adr/0009-backup-recovery-rpo-rto.md](governance/adr/0009-backup-recovery-rpo-rto.md) | 등급 A/B/C × Tier 1/2/3 매트릭스 · WAL 연속 · 5개 복구 유형 · 분기 리허설 |
| [adr/0010-deployment-pipeline-standard.md](governance/adr/0010-deployment-pipeline-standard.md) | buildx + masblue-builder · SemVer 태깅 · expand/migrate/contract · 카나리 + 5분 롤백 |
| [adr/0011-runtime-cluster-decomposition.md](governance/adr/0011-runtime-cluster-decomposition.md) | 코드 조직 — 12 도메인 클러스터 디렉토리 (런타임은 ADR-0014와 직교 N:M) |
| [adr/0012-commercialization-wave-mapping.md](governance/adr/0012-commercialization-wave-mapping.md) | 47 모듈 4축 점수 + Wave 1(12) / Wave 2(13) / Wave 3(14) / Wave 4(8) 매핑 + 21개월 일정 |
| [adr/0014-runtime-plane-decomposition.md](governance/adr/0014-runtime-plane-decomposition.md) | 런타임 plane 분해 — 6 plane(api/realtime/worker/scheduler/edge/extension) — `deploy/catalog/planes.yaml` SoT |
| [adr/0015-boundary-first-refactor-guardrails.md](governance/adr/0015-boundary-first-refactor-guardrails.md) | 대규모 리팩토링 하이브리드 구조 + 경계 우선 가드레일 |

#### ADR Cross-reference (주제 통합 진입점, W1.3 2026-05-14 갱신)

> ADR 번호 재사용 금지 정책 (글로벌 `standards/adr.md` §1) 정합. 주제 합본은 *별 파일 없이* INDEX cross-reference 만으로 처리.

| 주제 | 참조 ADR | 용도 |
|------|----------|------|
| SaaS 멀티테넌트 × RBAC | [ADR-0005](governance/adr/0005-multitenancy-isolation-tiers.md) + [ADR-0006](governance/adr/0006-authorization-model-rbac-abac.md) | 격리 등급 + 권한 결정 함수. *과거 `0010-saas-multitenant-rbac.md` alias 파일 폐기 (W1.3, 2026-05-14)* |

> 신규 ADR 0001~0012 채택 완료(2026-04-13). 동일자 ADR-0011 §0 노트 + ADR-0014 §0 부활: 코드 조직(0011)과 런타임 plane(0014)은 직교 2축으로 공존. 2026-04-14 ADR-0015 경계 우선 가드레일 추가.

| 문서 | 설명 |
|------|------|
| [governance/team-split.md](governance/team-split.md) | 에이전트 팀 작업 분할 |

---

## infra/ — 인벤토리·운영

| 문서 | 상태 | 설명 |
|------|------|------|
| [infra/env-secrets.md](infra/env-secrets.md) | 진행중 | 환경 변수/시크릿 정책 |

### infra/inventory/ (7개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [inventory/00-checklist.md](infra/inventory/00-checklist.md) | 진행중 | Phase 0 인벤토리 체크리스트 |
| [inventory/auth-oidc.md](infra/inventory/auth-oidc.md) | 초안 | OIDC(SSO) 인벤토리 |
| [inventory/cicd.md](infra/inventory/cicd.md) | 진행중 | CI/CD 인벤토리 |
| [inventory/data-storage.md](infra/inventory/data-storage.md) | 초안 | 데이터/스토리지/백업 |
| [inventory/dns-tls.md](infra/inventory/dns-tls.md) | 초안 | DNS/TLS |
| [inventory/k8s.md](infra/inventory/k8s.md) | 초안 | Kubernetes |
| [inventory/network.md](infra/inventory/network.md) | 초안 | 네트워크/보안 경계 |
| [inventory/repo.md](infra/inventory/repo.md) | 진행중 | 레포/모노레포/공용 라이브러리 |

### infra/ops/ (운영 정책 정본, 4개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [ops/README.md](infra/ops/README.md) | 확정 | 운영 정책 정본 역할 |
| [ops/backup-restore.md](infra/ops/backup-restore.md) | 초안 | 백업/복구 |
| [ops/observability.md](infra/ops/observability.md) | 진행중 | Observability |
| [ops/rollback.md](infra/ops/rollback.md) | 초안 | wave 종료/forward-only 롤백 전략 |
| [ops/slo.md](infra/ops/slo.md) | 초안 | SLO |

---

## api/ — API 가이드

| 문서 | 상태 | 설명 |
|------|------|------|
| [api/README.md](api/README.md) | 진행중 | API 완전 가이드 (인증, CRUD, 권한, 이벤트) |

---

## developer/ — 개발자 가이드 (5개)

| 문서 | 상태 | 설명 |
|------|------|------|
| [developer/00-environment-setup.md](developer/00-environment-setup.md) | 확정 | 개발 환경 설정 |
| [developer/01-add-new-service.md](developer/01-add-new-service.md) | 확정 | 새 서비스 추가 방법 |
| [developer/02-add-business-logic.md](developer/02-add-business-logic.md) | 확정 | 비즈니스 로직 추가 방법 |
| [developer/03-testing-guide.md](developer/03-testing-guide.md) | 확정 | 테스트 가이드 |
| [developer/04-event-system.md](developer/04-event-system.md) | 확정 | 이벤트 시스템 가이드 |

---

## onboarding/ — 빠른 시작·구조 이해 (3개)

| 문서 | 상태 | 설명 |
|------|------|------|
| onboarding/00-quickstart.md | 초안 | 로컬 개발 빠른 시작 |
| [onboarding/01-architecture-overview.md](onboarding/01-architecture-overview.md) | 진행중 | 저장소 구조와 아키텍처 개요 |
| [onboarding/02-coding-guide.md](onboarding/02-coding-guide.md) | 진행중 | 구현/테스트/리뷰 규칙 |

---

## tutorials/ — 실습 튜토리얼 (사용자-facing 최상위 정본, 10개)

상위 진입점: [tutorials/INDEX.md](tutorials/INDEX.md)

| 문서 | 상태 | 설명 |
|------|------|------|
| [tutorials/01-order-to-cash.md](tutorials/01-order-to-cash.md) | 진행중 | 판매주문 → 출고 → 송장 → 수금 |
| [tutorials/02-procure-to-pay.md](tutorials/02-procure-to-pay.md) | 진행중 | 구매요청 → 발주 → 입고 → 매입전표 → 지급 |
| [tutorials/03-expense-approval.md](tutorials/03-expense-approval.md) | 진행중 | 경비청구 → 전자결재 → 승인 → 회계분개 |
| [tutorials/04-payroll-process.md](tutorials/04-payroll-process.md) | 확정 | 직원등록 → 급여구조 → 급여처리 → 급여명세 → 회계분개 |
| [tutorials/05-manufacturing-flow.md](tutorials/05-manufacturing-flow.md) | 확정 | BOM → MRP → 작업지시 → 생산실적 |
| [tutorials/06-asset-lifecycle.md](tutorials/06-asset-lifecycle.md) | 확정 | 자산등록 → 감가상각 → 이동 → 처분 |
| [tutorials/07-project-management.md](tutorials/07-project-management.md) | 확정 | 프로젝트 → 타임시트 → 원가 → 수익인식 |
| [tutorials/08-quality-control.md](tutorials/08-quality-control.md) | 확정 | 검사 → 부적합 → CAPA |
| [tutorials/09-crm-pipeline.md](tutorials/09-crm-pipeline.md) | 확정 | 리드 → 기회 → 견적 → 수주 |
| [tutorials/10-admin-setup.md](tutorials/10-admin-setup.md) | 확정 | 초기 설정 가이드 |

---

## user-manual/ — 사용자 매뉴얼 (사용자-facing 최상위 정본, 15개 + INDEX)

| 문서 | 상태 | 설명 |
|------|------|------|
| [user-manual/INDEX.md](user-manual/INDEX.md) | 확정 | 목차 |
| [user-manual/00-getting-started.md](user-manual/00-getting-started.md) | 확정 | 시작하기 |
| [user-manual/01-accounting.md](user-manual/01-accounting.md) | 확정 | 회계 |
| [user-manual/02-selling.md](user-manual/02-selling.md) | 확정 | 판매 |
| [user-manual/03-buying.md](user-manual/03-buying.md) | 확정 | 구매 |
| [user-manual/04-stock.md](user-manual/04-stock.md) | 확정 | 재고 |
| [user-manual/05-hr.md](user-manual/05-hr.md) | 확정 | 인사 |
| [user-manual/06-payroll.md](user-manual/06-payroll.md) | 확정 | 급여 |
| [user-manual/07-expenses.md](user-manual/07-expenses.md) | 확정 | 경비 |
| [user-manual/08-crm.md](user-manual/08-crm.md) | 확정 | CRM |
| [user-manual/09-assets.md](user-manual/09-assets.md) | 확정 | 자산 |
| [user-manual/10-manufacturing.md](user-manual/10-manufacturing.md) | 확정 | 제조 |
| [user-manual/11-projects.md](user-manual/11-projects.md) | 확정 | 프로젝트 |
| [user-manual/12-quality.md](user-manual/12-quality.md) | 확정 | 품질 |
| [user-manual/13-approval.md](user-manual/13-approval.md) | 확정 | 전자결재 |
| [user-manual/14-admin.md](user-manual/14-admin.md) | 확정 | 관리자 |

---

## ops/ — 모듈별 runbook

| 문서 | 상태 | 설명 |
|------|------|------|
| [ops/README.md](ops/README.md) | 확정 | 모듈별 runbook 역할 |
| [ops/runbook-service-deploy.md](ops/runbook-service-deploy.md) | 초안 | 서비스 배포/롤아웃 및 전후 검증 |
| [ops/runbook-incident-response.md](ops/runbook-incident-response.md) | 초안 | 장애 대응 |
| [ops/runbook-db-backup-restore.md](ops/runbook-db-backup-restore.md) | 초안 | DB 백업/복구 |
| [ops/runbook-certificate-renewal.md](ops/runbook-certificate-renewal.md) | 초안 | 인증서 갱신 |

---

## plans/ — 설계·업그레이드 계획 (9개)

| 문서 | 설명 |
|------|------|
| plans/MASTER-PLAN.md | 마스터 플랜 |
| plans/2026-03-26-ai-native-roadmap-design.md | AI-native 로드맵 설계 |
| plans/2026-03-26-ai-native-roadmap-plan.md | AI-native 로드맵 계획 |
| plans/2026-03-31-automation-orchestrator-design.md | Automation Orchestrator 설계 |
| plans/2026-03-31-automation-orchestrator-plan.md | Automation Orchestrator 실행 계획 |
| plans/2026-03-26-uv-011-upgrade-design.md | uv 0.11 업그레이드 설계 |
| plans/2026-03-26-uv-011-upgrade-plan.md | uv 0.11 업그레이드 계획 |
| plans/2026-04-02-document-structure-cleanup-design.md | 문서 구조 정리 설계 |
| plans/2026-04-02-document-structure-cleanup.md | 문서 구조 정리 실행 계획 |

---

## superpowers/ — 구현 계획·설계 명세·시각 증거

### superpowers/plans/ (9개)

| 문서 | 설명 |
|------|------|
| plans/2026-03-24-cilium-gateway-deployment.md | Cilium Gateway 배포 계획 |
| plans/2026-03-27-foundation.md | 기반 구현 계획 |
| plans/2026-03-27-core-flows.md | 핵심 플로우 구현 계획 |
| plans/2026-03-27-extended-flows.md | 확장 플로우 구현 계획 |
| plans/2026-03-27-e2e-infrastructure.md | E2E 인프라 구현 계획 |
| plans/2026-03-27-missing-engines.md | 누락 엔진 구현 계획 |
| plans/2026-03-28-competitive-user-scenarios.md | 경쟁력 기반 사용자 시나리오 계획 |
| plans/2026-03-28-document-alignment.md | 문서 정합성 계획 |
| plans/2026-03-28-master-doc-production.md | 마스터 문서 생산 계획 |

### superpowers/specs/ (5개)

| 문서 | 설명 |
|------|------|
| specs/2026-03-24-cilium-gateway-deployment-design.md | Cilium Gateway 배포 설계 |
| specs/2026-03-27-implementation-plan-redesign-design.md | 구현 계획 전면 재설계 (Hybrid 3계층) — **유일한 구현 기준** |
| specs/2026-03-28-competitive-user-scenarios-design.md | 경쟁력 기반 사용자 시나리오 설계 |
| specs/2026-03-28-document-alignment-design.md | 문서 정합성 설계 |
| specs/2026-03-28-user-scenarios-design.md | 사용자 시나리오 설계 |

### superpowers/visual-log/

| 문서 | 설명 |
|------|------|
| [visual-log/README.md](superpowers/visual-log/README.md) | before/after 스크린샷과 NOTES 증거 규약 |
| [visual-log/checklists/README.md](superpowers/visual-log/checklists/README.md) | 사용자 스토리별 visual-log 체크리스트 인덱스 |

---

## 기타

| 문서 | 설명 |
|------|------|
| gap-analysis-amaranth10.md | 보관 문서: 과거 Amaranth10 상세 갭 분석. 최신 판단은 `product/scope/08-amaranth10-gap-analysis.md`와 `product/COMPETITIVE-GAP-ANALYSIS.md` 우선 |
