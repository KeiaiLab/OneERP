# Roadmap: OneERP

## Overview

OneERP v1.0 마일스톤은 이미 구현된 Foundation과 엔진을 실제 사용자 흐름, 웹 UI, 운영 인프라, 전체 검증 체계까지 닫아 파일럿 출시 가능한 기준선을 만드는 여정이다. 기존 capability를 확장하기보다 `PROGRESS.md`와 gap 문서에 남아 있는 미완료 흐름을 정리하고, 자동화 테스트와 운영 런북으로 제품 신뢰도를 확보한다.

## 🚧 v1.0 파일럿 출시

**Milestone Goal:** 핵심 업무 흐름, 사용자 접점 UI, 운영 인프라, 전체 검증과 문서를 마감해 파일럿 출시 기준선을 만든다.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: 이벤트 체인 안정화** - 남은 E2E 흐름의 공통 전제인 outbox/NATS/핸들러 체인을 안정화한다.
- [ ] **Phase 2: 핵심 운영 흐름 E2E 완성** - 구매, 경비, 급여, 제조 흐름을 자동화 E2E로 닫는다.
- [ ] **Phase 3: 협업·영업 흐름과 전자결재 UI 완성** - CRM-to-Selling, Approval-Anywhere, 전자결재 웹 UI를 완료한다.
- [ ] **Phase 4: 대시보드·보고서 사용자 출력 완성** - KPI 대시보드와 보고서/PDF 출력을 사용자 기준으로 마감한다.
- [ ] **Phase 5: 파일럿 운영 인프라 마감** - 게이트웨이, 배포 매니페스트, 관측성, 백업/복구를 검증한다.
- [ ] **Phase 6: 통합 QA·성능·보안 검증** - API/UI 전체 E2E와 성능·보안 점검을 통과한다.
- [ ] **Phase 7: 문서·튜토리얼·파일럿 검증 마감** - 시나리오, 튜토리얼, 사용자 문서와 파일럿 검증 자료를 현행화한다.

## Phase Details

### Phase 1: 이벤트 체인 안정화
**Goal**: Outbox → NATS → Handler 이벤트 체인을 안정화해 이후 흐름 E2E의 공통 전제를 마련한다.
**Depends on**: Nothing (first phase)
**Requirements**: [FLOW-01, FLOW-02, FLOW-03, FLOW-04]
**Stream impacts**: ERP
**Canonical refs**: `.planning/strategy/erp/ERP-MASTER-STRATEGY.md`, `.planning/strategy/erp/ERP-CAPABILITY-MAP.md`, `.planning/program/milestones/v1.0-program.md`, `.planning/program/risks/RISK-REGISTER.md`, `PROGRESS.md`, `docs/product/IMPLEMENTATION-GAP-REPORT.md`
**Success Criteria** (what must be TRUE):
  1. 개발자는 FL2~FL4에서 사용하는 이벤트 체인을 자동화 테스트로 재현할 수 있다.
  2. 서비스 간 이벤트 발행과 핸들러 소비가 로컬/CI 환경에서 일관되게 동작한다.
  3. `PROGRESS.md`에 기록된 FL1 blocker가 제거되고 회귀 테스트가 통과한다.
**Plans**: TBD

### Phase 2: 핵심 운영 흐름 E2E 완성
**Goal**: 구매, 경비, 급여, 제조의 핵심 운영 흐름을 사용자 시나리오 기준 E2E로 완료한다.
**Depends on**: Phase 1
**Requirements**: [FLOW-01, FLOW-02, FLOW-03, FLOW-04]
**Stream impacts**: ERP
**Canonical refs**: `.planning/strategy/erp/ERP-MASTER-STRATEGY.md`, `.planning/strategy/erp/ERP-CAPABILITY-MAP.md`, `.planning/program/milestones/v1.0-program.md`, `.planning/program/pilot/PILOT-READINESS.md`, `docs/product/scope/03-e2e-scenarios.md`, `docs/product/scope/comparisons/CL1-finance-accounting.md`, `docs/product/scope/comparisons/CL2-hr-payroll.md`, `docs/product/scope/comparisons/CL3-manufacturing-quality.md`
**Success Criteria** (what must be TRUE):
  1. 사용자는 Procure-to-Pay 전체 흐름을 자동화 E2E로 검증할 수 있다.
  2. 사용자는 Expense-to-Payment와 Payroll-to-Accounting 흐름을 자동화 E2E로 검증할 수 있다.
  3. 사용자는 Manufacture-to-Stock 흐름에서 생산과 재고 반영 결과를 자동화 E2E로 검증할 수 있다.
  4. 각 흐름에 필요한 단위/통합 테스트가 함께 통과한다.
**Plans**: TBD

### Phase 3: 협업·영업 흐름과 전자결재 UI 완성
**Goal**: CRM-to-Selling, Approval-Anywhere, 전자결재 웹 UI를 묶어 사용자 협업 흐름을 마감한다.
**Depends on**: Phase 2
**Requirements**: [FLOW-05, FLOW-06, UI-01]
**Stream impacts**: ERP, Groupware
**Canonical refs**: `.planning/strategy/groupware/GROUPWARE-MASTER-STRATEGY.md`, `.planning/strategy/groupware/GROUPWARE-CAPABILITY-MAP.md`, `.planning/strategy/erp/ERP-MASTER-STRATEGY.md`, `.planning/program/milestones/v1.0-program.md`, `docs/product/scope/comparisons/CL4-sales-crm.md`, `docs/product/scope/comparisons/CL5-approval-collaboration.md`
**Success Criteria** (what must be TRUE):
  1. 사용자는 CRM 파이프라인 결과가 판매 프로세스로 이어지는 흐름을 자동화 E2E로 검증할 수 있다.
  2. 사용자는 웹 화면에서 결재 요청, 위임, 승인, 감사 추적을 수행할 수 있다.
  3. Approval 관련 BE/FE 회귀 테스트와 Playwright 검증이 통과한다.
**Plans**: TBD

### Phase 4: 대시보드·보고서 사용자 출력 완성
**Goal**: KPI 대시보드와 보고서/PDF 출력을 사용자 관점의 결과물로 마감한다.
**Depends on**: Phase 3
**Requirements**: [UI-02, UI-03]
**Stream impacts**: ERP, Groupware
**Canonical refs**: `.planning/strategy/erp/ERP-MASTER-STRATEGY.md`, `.planning/program/metrics/NORTH-STAR-KPI.md`, `.planning/program/milestones/v1.0-program.md`, `docs/product/COMPETITIVE-GAP-ANALYSIS.md`, `docs/product/scope/06-competitive-analysis-global.md`
**Success Criteria** (what must be TRUE):
  1. 사용자는 로그인 후 KPI 대시보드에서 핵심 운영 지표를 확인할 수 있다.
  2. 사용자는 재무/급여 결과를 보고서와 PDF로 출력할 수 있다.
  3. 대시보드와 보고서 UI가 기존 권한 체계와 충돌하지 않는다.
**Plans**: TBD

### Phase 5: 파일럿 운영 인프라 마감
**Goal**: 파일럿 배포에 필요한 네트워크, 배포, 관측성, 백업/복구를 운영 기준으로 검증한다.
**Depends on**: Phase 4
**Requirements**: [OPS-01, OPS-02, OPS-03]
**Stream impacts**: ERP
**Canonical refs**: `.planning/program/releases/RELEASE-CRITERIA.md`, `.planning/program/pilot/PILOT-READINESS.md`, `.planning/program/risks/RISK-REGISTER.md`, `docs/infra/ops/observability.md`, `docs/infra/ops/backup-restore.md`, `docs/ops/runbook-service-deploy.md`
**Success Criteria** (what must be TRUE):
  1. 운영자는 Cilium Gateway와 Kubernetes 매니페스트로 서비스를 배포할 수 있다.
  2. 운영자는 Prometheus/Grafana에서 핵심 메트릭과 알림을 확인할 수 있다.
  3. 운영자는 백업/복구 런북을 실행해 복구 가능성을 검증할 수 있다.
**Plans**: TBD

### Phase 6: 통합 QA·성능·보안 검증
**Goal**: API/UI 전체 회귀, 성능, 보안 점검을 통과해 출시 기준선을 닫는다.
**Depends on**: Phase 5
**Requirements**: [REL-01, REL-02, REL-03]
**Stream impacts**: ERP, Groupware, AI
**Canonical refs**: `.planning/program/releases/RELEASE-CRITERIA.md`, `.planning/program/metrics/NORTH-STAR-KPI.md`, `.planning/program/risks/RISK-REGISTER.md`, `docs/engineering/ci/quality-gates.md`, `docs/engineering/ci/test-strategy.md`
**Success Criteria** (what must be TRUE):
  1. 개발팀은 API E2E 전체 스위트를 통과시킨다.
  2. 개발팀은 UI E2E 전체 스위트를 통과시킨다.
  3. 성능 기준과 보안 점검 결과가 파일럿 출시 기준을 만족한다.
**Plans**: TBD

### Phase 7: 문서·튜토리얼·파일럿 검증 마감
**Goal**: 코드와 검증 결과에 맞춰 시나리오, 튜토리얼, 사용자 문서를 정리하고 파일럿 검증을 마감한다.
**Depends on**: Phase 6
**Requirements**: [REL-04]
**Stream impacts**: ERP, Groupware, AI
**Canonical refs**: `.planning/program/pilot/PILOT-READINESS.md`, `.planning/program/releases/RELEASE-CRITERIA.md`, `.planning/strategy/portfolio/PRODUCT-VISION.md`, `docs/product/scope/03-e2e-scenarios.md`, `docs/tutorials/`, `docs/user-manual/`
**Success Criteria** (what must be TRUE):
  1. S01~S14 시나리오와 튜토리얼이 최신 흐름 기준으로 갱신된다.
  2. 사용자 매뉴얼과 운영 문서가 실제 동작과 일치한다.
  3. 파일럿 검증 자료가 자동화 결과와 함께 남는다.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. 이벤트 체인 안정화 | 0/0 | Not started | - |
| 2. 핵심 운영 흐름 E2E 완성 | 0/0 | Not started | - |
| 3. 협업·영업 흐름과 전자결재 UI 완성 | 0/0 | Not started | - |
| 4. 대시보드·보고서 사용자 출력 완성 | 0/0 | Not started | - |
| 5. 파일럿 운영 인프라 마감 | 0/0 | Not started | - |
| 6. 통합 QA·성능·보안 검증 | 0/0 | Not started | - |
| 7. 문서·튜토리얼·파일럿 검증 마감 | 0/0 | Not started | - |
