---
title: ADR-0018 · Commercial Grade v2 Spec III/II.5/품질 게이트 · 세션 1 도달점
date: 2026-04-22
status: accepted
tags: [commercial-grade-v2, spec3, spec2.5, quality, milestone]
---

# ADR-0018 · Commercial Grade v2 Spec III/II.5/품질 게이트 · 세션 1 도달점

## Context

2026-04-22 단일 자율 세션에서 Commercial Grade v2 Spec III/II.5/품질 게이트 통합 설계(487L)와 6주 구현 플랜(2055L)을 작성하고, 라이브 환경 불필요 구간 전량을 착수·완료했다. 총 42+ 커밋 main 랜딩.

## Decision

**품질 게이트 floor = 0** 채택 (플랜의 option 0).

- Wave A 자동/수동 ruff 정리로 73 errors → 0 달성
- 신규 코드(Spec III accounting/hr · Spec II.5 staging/T3 IaC) 전부 `ruff check . → All checks passed!` 상태로 착지
- ratchet CI로 향후 PR count 증가 방향 영구 차단

## Outcome — Wave/Track 단위

### Wave A · 품질 게이트
- ruff 73 → 0 (100% ↓, 43건 unsafe-fix + 30건 수동/noqa 분류)
- ratchet CI 설치 (`.github/workflows/ruff-ratchet.yml`)
- 공용 count 스크립트 (`scripts/ci/count-ruff-errors.sh`)

### Wave B-1 · staging IaC (라이브 배포 대기)
- `deploy/staging/`: namespace + kustomization + externalsecrets + monitoring-overlay
- `scripts/staging/`: seed_tenants / seed_auth / seed_monitoring (TDD · 3 tests)
- `.github/workflows/staging-deploy.yml` (buildx + kustomize)
- `scripts/secrets/rotate-gateway.sh` → `rotate_secret(module, tier)` 범용화

### Wave B-2 · Spec III accounting L0
- T2 artifact 수집기 (`scripts/ci/collect_t2_artifacts.py` + 4 TDD tests) — Spec II 회귀 차단
- G1-1 ADR-0019 accounting bounds (238L 실측 기반)
- G1-2 OpenAPI 스텁 + 자동 덤프 실패 로그 박제 (pydantic forward-ref 후속 이슈)
- G3-1 AuthN 7 tests (스테이징 조건부)
- G3-4 audit_hooks + 10 mutation tests
- G3-5 pip-audit 134 deps · CVE 0
- G5-1 매뉴얼 445L · G5-2 튜토리얼 478L

### Wave C-1 · Spec II.5 T3 6셀 IaC (실드릴 대기)
- G2-2 k6 부하 + workflow
- G2-4 chaos PodChaos + workflow
- G4-3 backup · G4-4 rollback · G4-5 on-call 드릴 문서 + workflows
- G5-3 UAT 247L (페르소나 3 × 시나리오 5)

### Wave C-2 · hr 선행 정합 + L0
- HRSettings(CoreSettings) + lru_cache DI · 2 tests
- event_registry + 7 handlers (employee.hired/terminated/transferred/department.reorganized/designation.changed/payroll.run.completed/leave.approved) · 2 tests
- core 서브모듈: `EventType` 7종 확장
- G1-1 ADR-0020 hr bounds 212L
- G1-2/G3-5/G5-1 432L/G5-2 543L · G3-1 17 tests PASS · G3-4 3 mutation tests

### Wave D · L1 (로컬 완료 구간)
- D1-b accounting ExternalSecret prod+staging
- D1-c accounting OPA rego + 6 tests (`policies/accounting/`)
- D2-b hr ExternalSecret prod+staging
- D2-c hr OPA rego + 9 tests (`policies/hr/`, payroll_admin 분리)
- D3 floor = **0** · ratchet 확정
- D4 본 ADR-0018

## Consequences

- 모든 ruff 에러가 0인 상태에서 Spec III 수평 확장 계속 — 신규 코드가 baseline을 올릴 수 없음 (ratchet)
- accounting/hr 모듈 게이트 증거가 파일 단위로 박제돼 있으므로 commercial-engine 모듈 등록 직후 score 상승 가능
- 라이브 환경 작업(staging k8s 배포 · T3 6셀 실드릴 · CI artifact 실수집)이 전부 workflow로 박제 — 트리거만 하면 실행 가능

## Non-goals (본 ADR이 주장하지 않는 것)

- commercial-engine score 23/23 달성 — 엔진의 모듈 레지스트리에 accounting/hr 등록 작업이 별도 필요
- 프로덕션 배포 — Spec II.5 범위에서 명시 제외
- Playwright UI 실행 — FE 서버 + 브라우저 기동 필요 (Wave D 후속)
- 46개 잔여 모듈 수직 완성 — Spec IV 범위

## Evidence

- 설계: `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md` (487L, commit `26a770be`)
- 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` (2055L, commit `343b5c76`)
- HANDOFF: `docs/superpowers/plans/2026-04-22-spec3-staging-quality-HANDOFF.md` (268L+ 최종)
- 선행 ADR: ADR-0017 (ratchet baseline)
- 관련 ADR: ADR-0019 accounting bounds, ADR-0020 hr bounds
- 실측 숫자 (세션 종료 시점):
  - main 커밋 수: 42+
  - ruff errors: 0 (73 → 0)
  - 신규 파일 수: 60+
  - 신규 테스트 수: 40+ (TDD)
  - 신규 gate 증거 파일: 15+
  - 신규 IaC/workflow: 12 k8s manifest + 7 GitHub Actions workflow
  - 신규 ADR: 3편 (0017, 0018, 0019, 0020)

## Next (Spec IV 대비)

1. commercial-engine 모듈 레지스트리에 accounting/hr 공식 등록 → score 상승 확인
2. staging k8s 클러스터 확보 → Wave B-1 실배포 → C-1 실드릴 순차 실행
3. CI artifact 실수집 파이프라인 트리거 → 기존 gateway PARTIAL 4셀(G1-2/G1-3/G1-5/G3-1) 소급 PASS
4. Spec IV: 46개 잔여 모듈 × 23 gate roadmap
