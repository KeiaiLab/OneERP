# ADR Index — docs/governance/adr/

> 글로벌 `standards/adr.md` 준수. 신규 ADR 작성 시 본 INDEX.md 갱신 의무.

| ID | 파일 | 제목 | Status | Date |
|----|------|------|--------|------|
| 0001 | [0001-commercial-grade-definition.md](./0001-commercial-grade-definition.md) | 상용 제품 정의(DoD)와 통과 게이트 | Accepted | 2026-04-13 |
| 0002 | [0002-commercialization-waves.md](./0002-commercialization-waves.md) | 상용화 Wave 전략 | Accepted | 2026-04-13 |
| 0003 | [0003-test-strategy-and-coverage-gates.md](./0003-test-strategy-and-coverage-gates.md) | 테스트 전략과 커버리지 게이트 | Accepted | 2026-04-13 |
| 0004 | [0004-database-standard-ferretdb.md](./0004-database-standard-ferretdb.md) | 데이터베이스 표준 — FerretDB 채택과 출구 조건 | Accepted | 2026-04-13 |
| 0005 | [0005-multitenancy-isolation-tiers.md](./0005-multitenancy-isolation-tiers.md) | 멀티테넌시 격리 계층 | Accepted | 2026-04-13 |
| 0006 | [0006-authorization-model-rbac-abac.md](./0006-authorization-model-rbac-abac.md) | 인가 모델 RBAC+ABAC | Accepted | 2026-04-13 |
| 0007 | [0007-api-stability-versioning-contract.md](./0007-api-stability-versioning-contract.md) | API 안정성·버전 계약 | Accepted | 2026-04-13 |
| 0008 | [0008-observability-baseline.md](./0008-observability-baseline.md) | 관찰 가능성 베이스라인 | Accepted | 2026-04-13 |
| 0009 | [0009-backup-recovery-rpo-rto.md](./0009-backup-recovery-rpo-rto.md) | 백업·복구 RPO/RTO | Accepted | 2026-04-13 |
| 0010 | [0010-deployment-pipeline-standard.md](./0010-deployment-pipeline-standard.md) | 배포 파이프라인 표준 | Accepted | 2026-04-13 |
| 0011 | [0011-runtime-cluster-decomposition.md](./0011-runtime-cluster-decomposition.md) | 런타임 클러스터 분해 | Accepted | 2026-04-13 |
| 0012 | [0012-commercialization-wave-mapping.md](./0012-commercialization-wave-mapping.md) | 상용화 Wave 매핑 | Accepted | 2026-04-13 |
| 0013 | [0013-commercial-gate-drill-evidence.md](./0013-commercial-gate-drill-evidence.md) | 상용 게이트 드릴 증거 | Proposed | 2026-04-21 |
| 0014 | [0014-runtime-plane-decomposition.md](./0014-runtime-plane-decomposition.md) | 런타임 plane 분해 | Accepted | 2026-04-13 |
| 0015 | [0015-boundary-first-refactor-guardrails.md](./0015-boundary-first-refactor-guardrails.md) | 경계 우선 대규모 리팩토링 가드레일 | Accepted | 2026-04-14 |
| 0016 | [0016-commercial-grade-v2-evidence.md](./0016-commercial-grade-v2-evidence.md) | Commercial Grade v2 Evidence Engine | Accepted | 2026-04-22 |
| 0017 | [0017-oe-feature-pipeliner-agent-team.md](./0017-oe-feature-pipeliner-agent-team.md) | oe-feature-pipeliner + 라우팅 매트릭스 도입 | Accepted | 2026-04-30 |
| 0018 | [0018-ferretdb-to-mongodb-cutover.md](./0018-ferretdb-to-mongodb-cutover.md) | FerretDB 폐기, native MongoDB(k8s) 로 완전 cut-over | Proposed | 2026-05-14 |

## Cross-reference (주제 통합 진입점)

> 단일 ADR 번호로 묶이지 않는 *횡단 주제* 의 진입점. ADR 번호 재사용 금지 (글로벌 `standards/adr.md` §1).

| 주제 | 참조 ADR | 비고 |
|------|----------|------|
| SaaS 멀티테넌트 × RBAC 합본 | [ADR-0005](./0005-multitenancy-isolation-tiers.md) + [ADR-0006](./0006-authorization-model-rbac-abac.md) | 격리 등급 + 권한 결정 함수. *과거 `0010-saas-multitenant-rbac.md` alias 파일 폐기 (W1.3, 2026-05-14)*. 격리 등급 변경은 ADR-0005, 권한 결정 변경은 ADR-0006 에서 수행. |

## 변경 이력

| 날짜 | 변경 | 근거 |
|------|------|------|
| 2026-05-14 | ADR-0004 중복 파일 (`0004-ferretdb-database-engine.md`) 삭제 — sha256 완전 동일 pure duplicate. | W1.3 (refactor plan `~/.claude/plans/woolly-doodling-tarjan.md`) |
| 2026-05-14 | ADR-0010 alias 파일 (`0010-saas-multitenant-rbac.md`) 삭제 + 본 INDEX `## Cross-reference` 섹션 신설. ADR 번호 재사용 정책 정합 (글로벌 `standards/adr.md` §1). | 동일 |
| 2026-05-14 | ADR-0018 (`0018-ferretdb-to-mongodb-cutover.md`) 신규 — FerretDB 폐기 및 native MongoDB(k8s) full cut-over 결정. Status: Proposed. Wave 4 진입 시 Accepted 전환. | W4.1 (refactor plan Wave 4) |
