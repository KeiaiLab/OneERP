# BE 컨텍스트 맵(초안)

> Phase 0 인벤토리(`docs/infra/inventory/`)를 기반으로 서비스 경계/통신/권한/데이터 경계를 확정한다.
> 본 문서는 “후보”이며, 최종 확정은 ADR로 기록한다.

## 후보 바운디드 컨텍스트(ERPNext 기준)

- Accounting
- Selling
- Buying
- Stock
- Manufacturing
- Projects
- CRM
- HR
- Payroll
- Support
- Assets
- Setup/Admin

## Phase 0 초기 구현 범위(기록)

이 섹션은 초기 스캐폴딩 시점의 기준선을 기록한다. 현재 저장소의 최신 서비스 현황은 47개 서비스 기준이며, 상세 대응은 `docs/product/scope/MODULE-SERVICE-MAP.md`와 `docs/product/PROJECT-INTEGRITY-REPORT.md`를 우선한다.

| 서비스 | 경로 | 설명 |
|--------|------|------|
| **Gateway** | `services/gateway/` | API Gateway (라우팅/인증 집계) |
| **Selling** | `services/selling/` | 판매 서비스 |
| **Stock** | `services/stock/` | 재고 서비스 |
| **Accounting** | `services/accounting/` | 회계 서비스 |

- 공통 커널: `packages/core/oneerp_core/` (auth, tenant, audit, db, errors, models, middleware)
- 모노레포 구조: uv workspace (BE) + pnpm workspace (FE)
- 서비스 간 통신: Phase 0에서는 독립 실행, 서비스 간 직접 통신 없음

## 확인 필요(Phase 1)

- 서비스 간 통신 패턴 (REST / gRPC / Message Queue) — ADR 필요
- 배포 방식(GitOps/ArgoCD): `docs/infra/inventory/cicd.md`, `docs/infra/inventory/k8s.md`
- 인증/권한(OIDC + 그룹/클레임): `docs/infra/inventory/auth-oidc.md`
- 멀티테넌시 경계: (법인/고객/사업부)
- Gateway 역할 확정 (API 라우팅/권한 집계 vs BFF)

## 산출물(DoD)

- [x] Phase 0 서비스 스캐폴딩 완료 (Gateway, Selling, Stock, Accounting)
- [ ] 컨텍스트 경계(모듈/데이터/권한)가 문서화됨
- [ ] 외부 API / 내부 API 분리 및 버저닝 정책이 정해짐(ADR)
