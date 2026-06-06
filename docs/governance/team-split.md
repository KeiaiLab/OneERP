# 에이전트 팀 작업 분할(SoT)

> 목적: 병렬 작업 시 충돌을 줄이고, 산출물의 단일 소스 오브 트루스(SoT)를 고정한다.

## 공통 규칙

- 결정은 ADR로만 확정: `docs/governance/adr/`
- 인벤토리 SoT: `docs/infra/inventory/`
- 기능 동등성 SoT: `docs/product/scope/`

## Agent A: ERPNext 기능/도메인 분해 & 화면 매핑

- 입력:
  - ERPNext 기준 버전/앱 구성(Phase 0 확정)
- 출력:
  - `docs/product/scope/01-module-catalog.csv` 채우기
  - `docs/engineering/ui/screen-mapping.csv` 생성
  - `docs/product/scope/03-e2e-scenarios.md` 확정

## Agent B: FE Design System/Metronic 컴포넌트화

- 입력:
  - Metronic 적용 방식/라이선스/브랜드 토큰
- 출력:
  - `docs/engineering/ui/tokens.md`, `docs/engineering/ui/components.md`, `docs/engineering/ui/page-templates.md` 확정
  - FE 스택 ADR 초안

## Agent C: BE 아키텍처/권한/워크플로우

- 입력:
  - OIDC 정책(issuer/claims), 테넌시 요구
- 출력:
  - `docs/engineering/architecture/be-context-map.md` 구체화
  - `docs/engineering/architecture/authz.md` 확정(ADR 포함)
  - 워크플로우/이벤트 방식 ADR 초안

## Agent D: 데이터(FerretDB)/마이그레이션/성능

- 입력:
  - FerretDB 운영 방식, 백업 스토리지/RPO/RTO
- 출력:
  - `docs/engineering/data/ferretdb-compat-matrix.md`
  - `docs/engineering/data/indexing-strategy.md`
  - `docs/infra/ops/backup-restore.md` 구체화

## Agent E: CI/CD/관측/운영

- 입력:
  - CI 제공자/Runner/Secret 관리
  - K8s/GitOps(Flux) 운영 표준
- 출력:
  - `docs/engineering/ci/quality-gates.md` 확정
  - `docs/infra/ops/observability.md`, `docs/infra/ops/slo.md`, `docs/ops/` 런북 초안
