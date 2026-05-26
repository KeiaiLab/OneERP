# OneERP

## What This Is

OneERP는 한국 규제 대응이 필요한 제조·유통 중심 중소~중견기업을 위한 멀티테넌트 SaaS ERP다. 현재 기준선은 47개 서비스와 56개 모듈 명세를 갖춘 코드베이스이며, 이번 마일스톤은 문서화된 엔진과 사용자 흐름을 실제로 끝까지 검증 가능한 제품 상태로 끌어올리는 데 집중한다.

## Core Value

한국 제조·유통 기업의 핵심 업무 흐름이 끊기지 않고 자동화 테스트로 검증되는 ERP를 제공한다.

## Current Milestone: v1.0 파일럿 출시

**Goal:** 핵심 E2E 흐름, 사용자 접점 UI, 운영 인프라, 통합 검증을 마감해 파일럿 출시 가능한 기준선을 만든다.

**Target features:**
- 7대 핵심 업무 흐름의 자동화 E2E 완성
- 전자결재 UI, KPI 대시보드, 보고서/PDF 출력 마감
- 배포 게이트웨이, 관측성, 백업/복구, 전체 QA 및 문서 검증 완료

## Requirements

### Validated

- ✓ 기본 14모듈 CRUD 스캐폴딩 완료 — P0
- ✓ Foundation 기반(FE 코드젠, CI/CD, 이벤트 인프라, 로컬 개발환경, E2E 프레임워크) 완료 — Phase A
- ✓ 핵심 비즈니스 엔진 13종 구현 및 테스트 완료 — Phase B
- ✓ FL1 Order-to-Cash 흐름 자동화 통과 — PROGRESS 기준 2026-03-28
- ✓ D1 FE EntityConfig 품질 게이트 통과 — PROGRESS 기준 2026-03-28
- ✓ SaaS 3-Tier 권한 시스템과 관리자 FE 기초 구현 완료 — TASKS 기준 Phase 5

### Active

- [ ] 7대 핵심 업무 흐름을 사용자 시나리오 기준으로 자동화 검증한다.
- [ ] 전자결재, 대시보드, 보고서 출력을 실제 사용자 화면 기준으로 마감한다.
- [ ] 파일럿 운영에 필요한 게이트웨이, 관측성, 백업/복구, 품질 게이트를 닫는다.
- [ ] 문서, 튜토리얼, 파일럿 검증 자료를 코드 기준선과 동기화한다.

### Out of Scope

- P2/P3 신규 capability 확장 전체 재개 — 현재 마일스톤은 기존 구현 완성과 검증이 우선
- AI/ML, 모바일 전용 UX, 포탈 고도화 — `docs/product/scope/03-phase-roadmap.md`상 P4 이후 범위
- 경쟁사 parity를 위한 신규 엔티티 대량 추가 — 현재는 `IMPLEMENTATION-GAP-REPORT`의 미완료 항목과 파일럿 출시 기준선만 다룸

## Context

- 실행 기준 문서는 `docs/product/scope/IMPLEMENTATION-MASTER-PROMPT.md`, `docs/product/scope/00-source-of-truth.md`, `docs/product/scope/03-phase-roadmap.md`, `docs/product/IMPLEMENTATION-GAP-REPORT.md`, `PROGRESS.md`다.
- 현재 코드베이스는 엔진 구현과 일부 E2E가 존재하지만, 남은 핵심 흐름과 운영 인프라, 사용자 접점 화면, 전체 회귀 검증이 미완료다.
- `PROGRESS.md` 기준 다음 미완료 묶음은 FL2~FL7, D2~D4, I1~I4, T1~T4, G1~G4다.
- 품질 게이트는 `./scripts/ci/run.sh`와 서비스별 pytest/Playwright 흐름으로 검증한다.
- 상세 제품 방향은 `.planning/strategy/`에서, 상세 프로그램 운영 기준은 `.planning/program/`에서 관리한다.

## Constraints

- **언어**: 모든 산출물과 작업 로그는 한국어 — AGENTS.md 강제 규칙
- **검증**: 테스트 없는 완료 선언 금지 — 자동화 검증이 선행돼야 함
- **E2E 도구**: 웹 E2E는 Playwright, 앱 E2E는 Appium — 전역 규칙
- **범위**: 기존 capability 확장보다 미완료 흐름 완성과 파일럿 출시 기준선 확보 우선 — `PROGRESS.md`, `IMPLEMENTATION-MASTER-PROMPT.md`
- **아키텍처**: SoT와 ADR을 우선하고 기존 서비스 경계를 유지 — `docs/governance/adr/`, `docs/product/scope/MODULE-SERVICE-MAP.md`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1.0 마일스톤을 파일럿 출시 기준선으로 정의 | 문서상 구현 범위는 넓지만 실제 미완료는 흐름/검증/운영 마감에 집중돼 있음 | — Pending |
| 활성 요구사항은 `PROGRESS.md`의 미완료 항목 중심으로 재정렬 | 현재 코드와 테스트 상태를 가장 직접적으로 반영하는 문서이기 때문 | ✓ Good |
| 신규 capability 확장보다 기존 엔진의 E2E/운영 마감 우선 | 파일럿 출시와 품질 게이트 닫기가 현재 제품 가치에 직접 연결됨 | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## Canonical Refs

- Product vision: `.planning/strategy/portfolio/PRODUCT-VISION.md`
- ERP + Groupware + AI thesis: `.planning/strategy/portfolio/ERP-GROUPWARE-AI-THESIS.md`
- ERP strategy: `.planning/strategy/erp/ERP-MASTER-STRATEGY.md`
- Groupware strategy: `.planning/strategy/groupware/GROUPWARE-MASTER-STRATEGY.md`
- AI strategy: `.planning/strategy/ai/AI-MASTER-STRATEGY.md`
- v1.0 program: `.planning/program/milestones/v1.0-program.md`

---
*Last updated: 2026-04-02 after milestone bootstrap from existing project docs*
