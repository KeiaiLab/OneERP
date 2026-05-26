# OneERP 에이전트 운영 규칙

## 0단계(필수): 공유 리소스 인벤토리

**공유 리소스(인프라/클러스터/DB/스토리지/도메인/CI/CD/레포 구조/인증/공용 라이브러리)** 확인 없이,
아키텍처 확정/모듈 분해/일정 산출을 시작하지 않는다.

- 체크리스트/산출물 위치: `docs/infra/inventory/`
- 수집 스크립트 결과(증빙): `artifacts/` (커밋 금지)

## 단일 소스 오브 트루스(SoT)

- 인벤토리: `docs/infra/inventory/`
- 범위/기능 동등성 매트릭스: `docs/product/scope/`
- ADR(결정 기록): `docs/governance/adr/`
- 운영/CI: `docs/infra/ops/`
- UI Design System: `docs/engineering/ui/`

## ADR 규칙(충돌 해결)

설계/스택/경계/권한/테넌시/데이터/CI 등 “결정”은 ADR로만 확정한다.

- 템플릿: `docs/governance/adr/0000-template.md`
- PR에 ADR이 없으면: 해당 변경은 “제안”으로만 취급(merge 보류)

## 품질 게이트(필수)

- 로컬: `./scripts/ci/run.sh`
- CI: ruff/ty/tests(유닛/통합/E2E)/마이그레이션·스키마 검증을 필수 통과

## 브랜치/작업 분리

동시 작업은 가능한 한 worktree 기반으로 분리한다.

- 기본 디렉토리: `.worktrees/` (gitignore)

## FE 작업 규칙

- `web/` 내 FE 코드 변경 시 `.claude/skills/visual-dual-loop.md` 스킬을 준수한다. 모든 이터레이션은 before/after 스크린샷과 콘솔 점검 증거를 `docs/superpowers/visual-log/`에 남긴다.


## 에이전트 라인업 (2026-04-30~)

- 정의 위치: `.claude/agents/`
- 라우팅 매트릭스: `.claude/agents/_routing-matrix.md` (18종 협업 룰)
- 일반 PR 통합 변경 사이클: `oe-feature-pipeliner` (사용자 명시 / auto-cycle Phase 3 dispatch)
- Commercial Engine wave: `ce-planner` (`/commercial-engine` 호출)
- 검증 인프라: `scripts/agents/*.py` + `tests/unit/agents/test_*.py`
- 결정 기록: ADR-0017 (`docs/governance/adr/0017-oe-feature-pipeliner-agent-team.md`)

@~/.claude/CLAUDE.md
