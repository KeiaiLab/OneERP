# Requirements: OneERP

**Defined:** 2026-04-02
**Core Value:** 한국 제조·유통 기업의 핵심 업무 흐름이 끊기지 않고 자동화 테스트로 검증되는 ERP를 제공한다.

## v1 Requirements

### Core Flows

- [ ] **FLOW-01**: 사용자는 구매 요청부터 지급까지 Procure-to-Pay 흐름을 자동화 E2E로 검증할 수 있다.
- [ ] **FLOW-02**: 사용자는 법인카드 거래부터 경비 정산과 지급까지 Expense-to-Payment 흐름을 자동화 E2E로 검증할 수 있다.
- [ ] **FLOW-03**: 사용자는 근태와 급여 계산 결과가 회계 전표까지 연결되는 Payroll-to-Accounting 흐름을 자동화 E2E로 검증할 수 있다.
- [ ] **FLOW-04**: 사용자는 생산 계획과 재고 이동이 연결되는 Manufacture-to-Stock 흐름을 자동화 E2E로 검증할 수 있다.
- [ ] **FLOW-05**: 사용자는 CRM 파이프라인 결과가 판매 흐름으로 이어지는 CRM-to-Selling 흐름을 자동화 E2E로 검증할 수 있다.
- [ ] **FLOW-06**: 사용자는 전자결재 요청, 위임, 승인, 감사 추적이 연결된 Approval-Anywhere 흐름을 자동화 E2E로 검증할 수 있다.

### Frontend

- [ ] **UI-01**: 사용자는 웹 화면에서 전자결재 흐름을 생성·승인·추적할 수 있다.
- [ ] **UI-02**: 사용자는 로그인 후 KPI 대시보드에서 핵심 지표를 확인할 수 있다.
- [ ] **UI-03**: 사용자는 재무/급여 결과를 보고서와 PDF 형태로 출력할 수 있다.

### Operations

- [ ] **OPS-01**: 운영자는 Cilium Gateway와 Kubernetes 매니페스트를 이용해 외부 트래픽을 안정적으로 라우팅할 수 있다.
- [ ] **OPS-02**: 운영자는 Prometheus/Grafana 기반 Observability로 핵심 서비스 상태를 확인할 수 있다.
- [ ] **OPS-03**: 운영자는 백업/복구 런북을 실행해 데이터 복구 가능성을 검증할 수 있다.
- [ ] **OPS-04**: plane 간 이벤트 계약(NATS subject/payload 스키마)은 `docs/engineering/architecture/event-contracts.md`를 단일 진실 원천(SoT)으로 고정하며, plane 경계 재정렬 트랙과 docker-compose→k3s/devspace 전환 트랙의 CI 게이트는 이 계약에 대해 동일하게 통과해야 한다. (추가: 2026-04-15, /gsd-explore 리팩토링 방향)

### Release Readiness

- [ ] **REL-01**: 개발팀은 API E2E 전체 스위트를 통과시켜 핵심 비즈니스 흐름 회귀를 막을 수 있다.
- [ ] **REL-02**: 개발팀은 UI E2E 전체 스위트를 통과시켜 사용자 화면 회귀를 막을 수 있다.
- [ ] **REL-03**: 개발팀은 성능과 보안 점검을 통해 파일럿 출시 기준선을 충족할 수 있다.
- [ ] **REL-04**: 운영팀은 시나리오 문서, 튜토리얼, 사용자 매뉴얼, 파일럿 검증 자료를 최신 코드와 일치시킬 수 있다.

## v2 Requirements

### Korea Competitive Gaps

- **KOR-01**: 홈택스/위택스 전자신고와 금융 CMS 실연동을 제공한다.
- **KOR-02**: 주52시간 실시간 통제와 연차사용촉진 자동화를 제공한다.
- **KOR-03**: 직원 셀프서비스와 증명서/전자근로계약서 발급을 제공한다.

### Advanced Capabilities

- **ADV-01**: AI/ML, 모바일 전용 UX, 포탈 고도화를 P4 이후 로드맵에 맞춰 제공한다.
- **ADV-02**: PLM, ESG, E-Commerce, Subscription 등 P2/P3 capability 확장을 파일럿 이후 재개한다.

## Out of Scope

| Feature | Reason |
|---------|--------|
| 신규 capability 대량 추가 | 현재 마일스톤은 기존 구현 완성과 파일럿 검증이 우선 |
| 모바일 앱 전용 구현 | `03-phase-roadmap.md`상 P4 범위이며 현재 웹 흐름 완성이 먼저 |
| AI 코파일럿/추천 기능 | 핵심 업무 흐름과 출시 기준선에 직접 연결되지 않음 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FLOW-01 | Phase 2 | Pending |
| FLOW-02 | Phase 2 | Pending |
| FLOW-03 | Phase 2 | Pending |
| FLOW-04 | Phase 2 | Pending |
| FLOW-05 | Phase 3 | Pending |
| FLOW-06 | Phase 3 | Pending |
| UI-01 | Phase 3 | Pending |
| UI-02 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| OPS-01 | Phase 5 | Pending |
| OPS-02 | Phase 5 | Pending |
| OPS-03 | Phase 5 | Pending |
| REL-01 | Phase 6 | Pending |
| REL-02 | Phase 6 | Pending |
| REL-03 | Phase 6 | Pending |
| REL-04 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 after milestone bootstrap from existing project docs*
