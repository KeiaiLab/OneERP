---
slug: agent-team-composition
created: 2026-04-30
status: Proposed
authors: phil
type: design
scope: SP1 + SP2 (라우팅 매트릭스 + 신규 OneERP 전용 에이전트 정의)
tier: T2
pipeliner: false
adr_required: true
---

# OneERP 에이전트 팀 구성 — Design

## 1. 요약

OneERP에서 *commercial-engine 외부의 일반 PR* 변경 사이클(BE 핸들러/스키마 → openapi 덤프 → FE 타입 생성 → FE 컴포넌트 → visual 검증)을 *한 사이클로* 자동 진행할 통합 단일 에이전트 `oe-feature-pipeliner`를 정의하고, 기존 ce-* 5종 + 글로벌 13종 + 신규 1종을 어떤 작업에 어떻게 라우팅할지 라우팅 매트릭스(`_routing-matrix.md`)로 명문화한다. 진입점은 *사용자 명시 호출*과 *auto-cycle Phase 3 자동 dispatch* 둘이며, 후자는 변경 경로 패턴 또는 plan 메타 `pipeliner: true` override로 발동한다.

## 2. 결정 사항 (브레인스토밍 로그)

| Q | 항목 | 선택 | 근거 |
|---|---|---|---|
| Q1 | 목적 | D — 신규 정의 + 기존 정비 동시 | 신규만 정의하면 글로벌 13종과 역할 충돌, 기존만 정비하면 OneERP 고유 워크플로 결손 |
| Q2 | 분해 전략 | b — SP1+SP2 묶음 (T2) | 매트릭스의 "빈 칸"이 곧 신규 에이전트 후보 — 묶는 게 자연스러움 |
| Q3 | 결손 우선순위 | (2) FE+visual → (1) BE 라이프사이클 → (6) 타입 동기화 | 세 결손이 한 사슬로 연결됨 (Frontend feature pipeline) |
| Q4 | 분업 구조 | A — 통합 단일 에이전트 | atomic 커밋 선호 + BE/타입/FE drift는 같은 PR에서 묶여 발생 |
| Q5 | 호출 트리거 | B — auto-cycle Phase 3 자동 + 사용자 직접 호출 | 자율 dispatch 우선, 사람 게이트는 Phase 4 verify로 대체 |
| Q6 | 트리거 감지 | e — 경로 패턴 자동 + plan 메타 override | 자동 감지 누락은 plan 메타 `pipeliner: true|false`로 강제 |
| Q7 | 완료 게이트 | b — 4단계 게이트 + Edit 후 grep ground-truth | Phase 4가 회귀를 담당하므로 cycle 내부는 ground-truth가 핵심 |
| Q8 | 책임 경계 | b — pipeliner는 BE/타입/FE/visual만, ADR은 documentation-sync-agent에 sub-Task 위임 | 도구 화이트리스트 좁게 유지 + 글로벌 에이전트 가치 살림 |

## 3. 변종 비교

| 변종 | 차이 | 트레이드오프 | 채택 |
|---|---|---|---|
| **V1. 기본** | `oe-feature-pipeliner` 1종 + 라우팅 매트릭스 1장 + ADR 트리거 시 documentation-sync-agent 위임 | 단일 진입점, 도구 화이트리스트 한정, plan 메타 on/off | ✅ |
| V2. 확장 | V1 + `oe-doc-sync-router`(ADR 라우팅 전담 보조 에이전트) | pipeliner 도구 더 좁아짐. 1년차 over-engineering | ❌ (지금) |
| V3. 축소 | pipeliner 없이 매트릭스에 *기존 글로벌+ce-* 호출 룰만* 문서화 | 결손 (1)(2)(6)을 사람이 메움. Q5의 B 결정과 모순 | ❌ |

## 4. 아키텍처

### 4-1. 시스템 외형

```
                 ┌─────────────────────────────────────────────────────┐
                 │ 진입점 1 — 사용자 명시                              │
사용자 ─────────►│ Task(subagent_type="oe-feature-pipeliner",          │──┐
                 │      prompt="<자연어>")                              │  │
                 └─────────────────────────────────────────────────────┘  │
                                                                          │
                 ┌─────────────────────────────────────────────────────┐  │
                 │ 진입점 2 — auto-cycle Phase 3 dispatcher            │  │
auto-cycle ─────►│ if (path 패턴 매치 OR plan 메타 pipeliner=true):    │──┤
   Phase 3       │     dispatch oe-feature-pipeliner                   │  │
                 └─────────────────────────────────────────────────────┘  │
                                                                          ▼
                 ┌──────────────────────────────────────────────────────────┐
                 │ oe-feature-pipeliner   (sonnet, 도구 화이트리스트 한정)  │
                 │ ────────────────────────────────────────────────────     │
                 │  Stage 1 ─ BE        ruff format/check + ty + pytest     │
                 │  Stage 2 ─ TYPE      openapi 덤프 → FE codegen → diff    │
                 │  Stage 3 ─ FE        biome + tsc --noEmit + next build   │
                 │  Stage 4 ─ VISUAL    playwright + 스크린샷 diff          │
                 │ ────────────────────────────────────────────────────     │
                 │  매 Edit 직후: grep ground-truth 의무                    │
                 │  ADR 자동 감지: sub-Task → documentation-sync-agent      │
                 └────────────────────────┬─────────────────────────────────┘
                                          │ verdict JSON
                                          ▼
                 ┌─────────────────────────────────────────────────────┐
                 │ verdict: PASS | FAIL | PARTIAL | BLOCK              │
                 │ next_action: commit+ship+deploy | review | block    │
                 │ stages, ground_truth, files_changed, dispatcher     │
                 └────────────────┬────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
       Phase 4 verify                       사용자 검토
       (회귀 영향 검증)                     (PARTIAL/BLOCK 시)
```

### 4-2. 진입점 일관성 룰

1. auto-cycle Phase 3가 호출했다면 prompt 본문에 `dispatcher: auto-cycle, plan_slug: <X>` marker 포함 → verdict에 `dispatcher: auto-cycle` 기록
2. 사용자가 직접 호출하면 marker 없음 → verdict에 `dispatcher: user`
3. 동일 task에 대해 *두 진입점이 동시 발화*하면 *후행이 즉시 종료* (verdict: `BLOCK`, reason: `concurrent_dispatch`)

### 4-3. 핵심 결정 (요약)

| 항목 | 값 |
|---|---|
| 위치 | `OneErp/.claude/agents/oe-feature-pipeliner.md` |
| 라우팅 매트릭스 | `OneErp/.claude/agents/_routing-matrix.md` |
| 모델 | `sonnet` |
| 도구 화이트리스트 | `Read, Write, Edit, Grep, Glob, Bash, Task, TaskCreate` |
| 외부 위임 | `documentation-sync-agent` (글로벌, ADR 트리거 시) |
| Bash 권한 범위 | 프로젝트 정의 명령 화이트리스트만 (§6-5) |
| 진입점 | 사용자 명시 / auto-cycle Phase 3 (commercial-engine은 제외) |

## 5. 컴포넌트

### 5-1. `oe-feature-pipeliner.md` 에이전트 정의

```yaml
---
name: oe-feature-pipeliner
description: OneERP 일반 PR의 BE + 타입 + FE + visual 통합 변경 사이클 실행. commercial-engine 외부 진입점 (사용자 명시 / auto-cycle Phase 3 dispatch).
tools: Read, Write, Edit, Grep, Glob, Bash, Task, TaskCreate
model: sonnet
---
```

본문 구성 (~100~150줄):

| 섹션 | 내용 |
|---|---|
| 책임 | 4 단계(BE/타입/FE/visual) + Edit 직후 ground-truth + ADR 트리거 위임 |
| 불변 규칙 | 도구 화이트리스트 외 사용 금지 / Bash 명령 화이트리스트 (§6-5) / Edit 직후 grep 의무 / ADR 시 sub-Task 위임 / 한국어 주석 / `print()` 금지 / `from __future__ import annotations` |
| Stage 1 BE | 영향 파일: `services/<svc>/**/*.py`, `packages/core/**/*.py`. entry: 변경 파일 식별. exit: ruff format/check + ty check + 영향 모듈 pytest 통과. skip 조건: 영향 파일 0 |
| Stage 2 TYPE | entry: Stage 1 PASS + 변경된 서비스 식별 + *공개 인터페이스 변경 감지*(`@router.<verb>` decorator 추가/제거 OR `services/**/schemas/*.py` 클래스 정의 diff OR `services/**/models/*.py` Pydantic 공개 필드 diff). 명령: `uv run --directory services/<svc> python -m app.openapi_dump` → `pnpm --filter @oneerp/web exec openapi-typescript`. exit: `git diff --exit-code apps/web/app/types/` 통과 (drift 0). skip 조건: BE 변경 없음 OR BE 변경 있지만 공개 인터페이스 미변경(내부 리팩토링·docstring 등) |
| Stage 3 FE | 영향 파일: `apps/web/app/**`, `apps/web/lib/**`, `apps/web/components/**`. exit: `pnpm --filter @oneerp/web lint && typecheck && build`. skip 조건: FE 영향 0 |
| Stage 4 VISUAL | entry: Stage 3 PASS + visual-dual-loop 스킬 인지. 명령: playwright + 스크린샷 비교. 결과 → `docs/superpowers/visual-log/<slug>/`에 before/after 기록. skip 조건: visible UI 변경 0 |
| Ground-truth 검증 | 매 Edit 직후 `grep "<인용>"` 으로 적용 검증. 미스 시 즉시 BLOCK |
| ADR 자동 감지 | Stage 1 종료 후 §6-4 패턴 검사. 트리거 시 sub-Task |
| 진입점 marker | dispatcher / plan_slug / task_id 추출 |
| 출력 포맷 | verdict JSON (§부록 A) |
| 사용자 시나리오 예시 | 1~2개 |

### 5-2. `_routing-matrix.md` 라우팅 매트릭스

위치: `OneErp/.claude/agents/_routing-matrix.md`. `_` prefix는 *에이전트 정의가 아님*을 표시 (Claude Code agent loader가 frontmatter를 보고 결정하지만 명시적 표기가 운영에 안전).

```markdown
# OneERP 에이전트 라우팅 매트릭스

## 목적
어떤 작업에 어느 에이전트를 1차로 호출하고, 어떤 2차 위임이 발생하는지를 표로 명시.
신규 작업 패턴은 행 추가, 기존 룰 변경은 ADR + 본 문서 수정.

## 표

| 작업 유형                              | 호출자             | 1차 에이전트          | 2차 위임                  | Stage skip          |
|----------------------------------------|--------------------|----------------------|---------------------------|---------------------|
| BE+FE 동시 (일반 PR)                   | 사용자/auto-cycle  | oe-feature-pipeliner | documentation-sync-agent  | —                   |
| BE only (일반 PR, 공개 인터페이스 미변경) | 사용자/auto-cycle  | oe-feature-pipeliner | documentation-sync-agent  | typebridge,fe,visual|
| BE only (공개 인터페이스 변경 포함)    | 사용자/auto-cycle  | oe-feature-pipeliner | documentation-sync-agent  | fe,visual           |
| FE only (일반 PR)                      | 사용자/auto-cycle  | oe-feature-pipeliner | —                         | be,typebridge       |
| 타입 only sync                         | 사용자/auto-cycle  | oe-feature-pipeliner | —                         | be,fe,visual        |
| FE 디자인(시각 단독)                   | 사용자             | oe-feature-pipeliner | —                         | be,typebridge       |
| Commercial Engine wave (G1-*~G5-*)     | /commercial-engine | ce-planner           | ce-artisan/scribe/executor| —                   |
| 의존성 감사                            | 사용자             | dependency-auditor   | —                         | —                   |
| 배포 전 검증                           | 사용자             | pre-deploy-validator | —                         | —                   |
| 외부 SDK·라이브러리 평가               | 사용자             | system-architect     | planning-decision-support | —                   |
| 코드 리뷰 (PR 후)                      | 사용자             | feature-dev:code-reviewer | —                    | —                   |
| 한국어 구현 일반 (스크립트/유틸)       | 사용자             | korean-dev-implementer | —                       | —                   |
| 관측성 결손 분석                       | 사용자             | observability-gap-analyzer | —                     | —                   |
| 배포 가드 / 운영 검토                  | 사용자             | ops-deployment-guardian | —                      | —                   |
| 의존 체인 모니터링                     | 사용자/cron        | dependency-chain-monitor | —                      | —                   |
| 크로스 프로젝트 표준화                 | 사용자             | cross-project-standardizer | —                     | —                   |
| 다언어 코드 품질 게이트                | 사용자/auto-cycle  | code-quality-gate    | —                         | —                   |
| 분석/리뷰 (한국어)                     | 사용자             | professional-analyst-ko | —                      | —                   |

## 판정 우선순위

1. **호출자 기준 1차 분기**: `/commercial-engine` 호출이면 → ce-planner. 그 외는 일반 흐름.
2. **변경 경로 자동 감지**: services/* + apps/web/* 동시 → oe-feature-pipeliner (BE+FE 행). services/* only → oe-feature-pipeliner (BE only 행, Stage skip 적용). apps/web/* only → oe-feature-pipeliner (FE only 행).
3. **plan 메타 override**: `docs/plans/<slug>/INDEX.md`에 `pipeliner: true|false`가 있으면 자동 감지 결과를 덮어씀.
4. **명시 작업 유형**: 위 표의 *비-pipeliner 행*(의존성 감사, 배포 전 검증 등)은 사용자가 직접 호출.

## 충돌 해소 룰

- 동일 task에 두 진입점이 동시 발화 → 후행 BLOCK (verdict: concurrent_dispatch)
- pipeliner와 ce-* 동시 dispatch → 호출자 기준 분기 룰 적용 (commercial-engine 우선)
- 매트릭스에 없는 작업 유형 → 사용자 확인 + 매트릭스 행 추가 (행 추가는 ADR 불필요, 룰 변경은 ADR 필요)

## 변경 절차

- 행 추가: 직접 PR
- 행 의미 변경: ADR 먼저 (`docs/governance/adr/`)
- 1차/2차 에이전트 교체: ADR 필수
```

### 5-3. plan 메타 schema

`docs/plans/<slug>/INDEX.md` frontmatter에 추가:

```yaml
---
slug: <slug>
created: YYYY-MM-DD
pipeliner: auto | true | false       # default: auto (경로 자동 감지에 위임)
pipeliner_skip_stages: []             # ["visual"] 등 명시 skip
adr_required: auto | true | false    # default: auto (감지 룰 사용)
---
```

3-state 디자인의 의미:
- `auto`: 자동 감지에 위임 (디폴트)
- `true`: 자동 감지가 매치되지 않아도 강제 발동
- `false`: 자동 감지가 매치되어도 발동 차단

### 5-4. ADR 자동 감지 룰

Stage 1 BE 종료 후 다음 패턴을 검사:

| 패턴 | 검출 방법 | 트리거 |
|---|---|---|
| API 엔드포인트 추가/제거 | `git diff` + grep `@router\.(get\|post\|put\|delete\|patch)` | ADR + INDEX |
| Pydantic 공개 스키마 추가/제거 | `git diff services/**/schemas/*.py` 클래스 정의 diff | ADR |
| 환경변수 추가 | `git diff` + grep `ONEERP_*` settings.py | ADR (CoreSettings 영향) |
| DB 마이그레이션 | `git diff migrations/` 또는 `alembic/versions/` | ADR + INC 잠재 |
| 의존성 추가/제거 | `git diff pyproject.toml uv.lock package.json pnpm-lock.yaml` | docs/kb/deps/YYYY-MM.md |

감지 시 호출:

```
Task(
  subagent_type="documentation-sync-agent",
  prompt="""
  ADR 트리거 자동 감지: <패턴>
  변경 파일: <목록>
  변경 diff 요약: <요약>
  OneERP SoT 위치:
    - ADR: docs/governance/adr/
    - 의존성 감사 로그: docs/kb/deps/YYYY-MM.md
    - INDEX: docs/governance/adr/INDEX.md
  적절한 ADR 또는 deps 로그 작성 후 verdict 반환.
  """
)
```

verdict에 `adr_triggered: true, sub_task_id: <X>, sub_verdict: <PASS|FAIL>` 기록.

### 5-5. Bash 명령 화이트리스트

```
# BE
uv run ruff format [--check] <path>
uv run ruff check <path>
uv run ty check <path>
uv run pytest [-q] [--cov] <path>
uv run --package oneerp-{서비스명} --directory services/{서비스명} python -m <module>

# 타입 브리지
uv run --directory services/<svc> python -m app.openapi_dump
pnpm --filter @oneerp/web exec openapi-typescript ../../services/<svc>/openapi.yaml -o app/types/<svc>.ts
git diff --exit-code apps/web/app/types/

# FE
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
pnpm --filter @oneerp/web build
pnpm --filter @oneerp/web test

# Visual
pnpm --filter @oneerp/web exec playwright test <path>
pnpm --filter @oneerp/web exec playwright test --update-snapshots   # 사용자 명시 호출에서만

# 검증
git diff / git status / git log (read-only)
grep / find / ripgrep (read-only)
make verify-roadmap
./scripts/ci/run.sh    # AGENTS.md 품질 게이트
```

**금지**: 임의 shell, `kubectl`, `helm`, `docker`, `gh`, `pnpm install`, `pip install`, `uv sync`(자가수정 별도 책임), `git commit`, `git push`(commit은 호출자가 atomic 단위로 결정).

## 6. 데이터 흐름

### 6-1. 시나리오 A — 사용자 직접 호출

1. 사용자: `Task(subagent_type="oe-feature-pipeliner", prompt="가격 정책 변경: services/buying의 price 핸들러 + apps/web의 가격 화면")`
2. pipeliner 시작 → 변경 파일 식별 (Read/Grep) → Stage skip 룰 평가 → 진입점 marker 추출 (없으므로 dispatcher: user)
3. Stage 1 BE: ruff/ty/pytest 영향 모듈 → 통과 / 각 Edit 직후 grep ground-truth
4. ADR 트리거 감지 → sub-Task documentation-sync-agent (있을 때만)
5. Stage 2 TYPE: openapi 덤프 → FE codegen → diff 0 검증
6. Stage 3 FE: biome/tsc/build
7. Stage 4 VISUAL: playwright + 스크린샷 diff → `docs/superpowers/visual-log/<slug>/`
8. verdict JSON 반환 (PASS|FAIL|PARTIAL + next_action)
9. 사용자가 verdict 보고 commit/ship/deploy 결정

### 6-2. 시나리오 B — auto-cycle Phase 3 dispatch

1. auto-cycle Phase 3 시작 → 변경 파일 패턴 감지 (`services/**/*.py` AND `apps/web/**`) 또는 plan 메타 `pipeliner: true`
2. Phase 3 → `Task(subagent_type="oe-feature-pipeliner", prompt="dispatcher: auto-cycle, plan_slug: <X>, task_id: <Y>, ...")`
3. pipeliner 시나리오 A와 동일 진행, 단 marker 기록
4. verdict 반환 + dispatcher: auto-cycle
5. Phase 3 후속: `verdict.next_action == "commit+ship+deploy"` → 즉시 1 commit + 1 ship + 1 deploy
6. Phase 4 verify가 회귀 검증 → 100% PASS면 Phase 5 cleanup

### 6-3. 시퀀스 다이어그램

```
호출자 ─► oe-feature-pipeliner
            │
            ├─► Stage 1 BE   (uv ruff/ty/pytest)        ──fail─► verdict.FAIL.stage=be
            │       │
            │       └─► [ADR 감지] sub-Task documentation-sync-agent (트리거 시)
            │
            ├─► Stage 2 TYPE (openapi → codegen)         ──fail─► verdict.FAIL.stage=typebridge
            │
            ├─► Stage 3 FE   (biome/tsc/build)           ──fail─► verdict.FAIL.stage=fe
            │
            ├─► Stage 4 VISUAL (playwright/diff)         ──diff>thr─► verdict.PARTIAL.reason=visual_regression
            │
            ├─► ground-truth 검증 (모든 Edit grep)       ──miss─► verdict.BLOCK.reason=edit_not_applied
            │
            └─► verdict JSON 반환
```

## 7. 에러 처리

### 7-1. verdict 매트릭스

| 에러 | verdict | reason | 영향 |
|---|---|---|---|
| Stage 1 BE fail (lint/type/pytest) | FAIL | stage_be_failed | 다음 Stage skip |
| Stage 2 typebridge diff != 0 | FAIL | type_drift | Stage 3,4 skip. drift 파일 목록 verdict에 포함 |
| Stage 3 FE fail | FAIL | stage_fe_failed | Stage 4 skip |
| Stage 4 visual diff > threshold | PARTIAL | visual_regression | 사용자 검토 필요. before/after 경로 verdict에 포함 |
| ground-truth grep 미스 | BLOCK | edit_not_applied | 즉시 중단 (CLAUDE.md §8 cycle 1 학습) |
| ADR sub-Task 실패 | PARTIAL | adr_delegation_failed | 감지됐지만 작성 실패 — 사용자 검토 권고 |
| 화이트리스트 외 Bash 시도 | BLOCK | bash_whitelist_violation | 즉시 중단 |
| 동시 발화 (concurrent dispatch) | BLOCK | concurrent_dispatch | 후행 즉시 종료 |
| 토큰 부담 (sonnet 컨텍스트 80%) | PARTIAL | context_pressure | 부분 진행 보고 + HANDOFF 권고 |
| 시크릿 생성/회전/폐기 요구 | BLOCK | blocker_secret_lifecycle | 11 블로커 #1 |
| 운영 리소스 삭제 요구 | BLOCK | blocker_ops_destructive | 11 블로커 #2 |
| 외부 과금 액션 요구 | BLOCK | blocker_external_billing | 11 블로커 #3 |
| `git --amend` / `push --force` 시도 | BLOCK | blocker_git_destructive | 11 블로커 #5 |
| 동일 verify 명령 3회 연속 실패 | BLOCK | blocker_verify_loop | 11 블로커 #6 |

### 7-2. verdict.next_action 결정 룰

- `PASS` + 모든 Stage 통과 + ground-truth OK → `commit+ship+deploy`
- `PARTIAL` (visual / ADR 위임 등) → `review_needed`
- `FAIL` (Stage 명시 실패) → `block` + 사용자 또는 Phase 4가 결정
- `BLOCK` (블로커) → `block` + 즉시 중단

### 7-3. 자가수정 정책 적용

`oe-feature-pipeliner`는 *코드 자체 수정*은 자가수정 영역(글로벌 §self-repair 허용 범위 — 빌드 설정·의존성·테스트 인프라). *시크릿/운영/과금/법적*은 모두 BLOCK으로 처리.

## 8. 테스트

### 8-1. 정적 검증

| 항목 | 명령 |
|---|---|
| 에이전트 frontmatter 유효성 | `python3 scripts/agents/validate_frontmatter.py .claude/agents/oe-feature-pipeliner.md` (신규) — name/description/tools/model 필드 검사 |
| 매트릭스 정합성 | `python3 scripts/agents/check_matrix_consistency.py .claude/agents/_routing-matrix.md` (신규) — 매트릭스 행이 실존 에이전트만 참조하는지 검증 |
| Bash 화이트리스트 정합성 | 매트릭스 + pipeliner 본문에 명시된 명령이 화이트리스트와 일치하는지 |

### 8-2. 단위 테스트

| 항목 | 위치 | 검증 |
|---|---|---|
| 라우팅 룰 판정 | `tests/agents/test_routing.py` (신규) | given(작업 유형, 호출자) → expected 1차 에이전트 |
| ADR 감지 패턴 매치 | `tests/agents/test_adr_detection.py` | git diff fixture 5종에 대해 패턴 매치 결과 |
| ground-truth 검증 결과 분기 | `tests/agents/test_ground_truth.py` | mock Edit 후 grep 결과 fail/pass 분기 |
| Stage skip 룰 평가 | `tests/agents/test_stage_skip.py` | 영향 파일 패턴별 expected skip 목록 |

### 8-3. 통합 (smoke)

OneERP에 *작은 BE+FE 변경 PR*을 만들고 `oe-feature-pipeliner` 호출 → 4 stage 모두 통과 / verdict.PASS / `next_action=commit+ship+deploy` 확인.

샘플 시나리오:
- BE: `services/gateway/app/routers/health.py`에 `/health/version` 엔드포인트 추가
- 타입: openapi 덤프 → FE codegen
- FE: `apps/web/app/admin/health/page.tsx`에 새 카드 추가
- visual: 스크린샷 비교, diff < 0.5%

### 8-4. 호환성 검증

- 기존 `visual-dual-loop` 스킬과 `docs/superpowers/visual-log/` 기록 형식 일치
- 기존 `ce-*` 5종과 호출자 기준 분기 충돌 없음 (commercial-engine 안 vs 밖)
- 글로벌 `documentation-sync-agent` sub-Task 호출 인터페이스 호환

## 9. Definition of Done (이번 세션)

- [ ] `OneErp/.claude/agents/oe-feature-pipeliner.md` 작성 + frontmatter 유효성 통과
- [ ] `OneErp/.claude/agents/_routing-matrix.md` 작성 + 정합성 통과
- [ ] plan 메타 schema 설명 추가 (`AGENTS.md` 또는 별도 문서)
- [ ] ADR 자동 감지 룰 룬북 (pipeliner 본문에 포함)
- [ ] Bash 화이트리스트 enumeration (pipeliner 본문에 포함)
- [ ] 정적 검증 스크립트 2종 (`validate_frontmatter.py`, `check_matrix_consistency.py`)
- [ ] 단위 테스트 4종 (`tests/agents/test_*.py`)
- [ ] smoke 시나리오 1회 실행 (verdict.PASS 확인)
- [ ] ADR 작성 — 본 디자인 결정 (Q1~Q8 결과 + V1 선택 근거)
- [ ] AGENTS.md에 `oe-feature-pipeliner` + 라우팅 매트릭스 위치 추가

## 10. 한계와 다음 단계

### 10-1. 이번 세션 범위 외

- **SP3 — 중복/모순 제거**: 글로벌 13종 중 OneERP 컨텍스트에서 *덮어쓰기* 또는 *은퇴* 대상 식별. 이번에는 매트릭스에 *덮어쓰기 권고*만 표시 (예: `korean-dev-implementer` vs `oe-feature-pipeliner`의 책임 경계).
- **SP4 — 운영 모드 통합**: auto-cycle / commercial-engine / 수동의 동일 에이전트 호출 일관성. 이번에는 *호출자 기준 분기*로 충돌 회피만.
- **auto-cycle Phase 3 dispatcher 자체의 변경**: 본 스펙은 pipeliner *입장*에서 marker를 읽는 룰만 정의. *경로 패턴 감지 로직 추가* + *plan 메타 평가* + *marker 주입(prompt 작성)*은 auto-cycle skill(`~/.claude/skills/auto-cycle/SKILL.md`) 측 변경이 필요하며 별도 후속 작업으로 분리.

### 10-2. 후속 작업 후보

- pipeliner 실사용 1주 후 *덮어쓰기/은퇴* 판단 (SP3)
- auto-cycle Phase 3 dispatcher 룰의 false positive/negative 수집 → 패턴 보정
- ADR 자동 감지 룰의 누락 패턴 발견 시 추가
- visual diff threshold의 경험적 튜닝 (현재 5% = `0.05` 가정, §부록 A schema 참조)

### 10-3. 회귀 안전판

- 매트릭스 파일은 *살아있는 문서* — 행 추가만으로 라우팅 갱신
- pipeliner verdict JSON은 *append-only 인덱스*에 기록 (`artifacts/pipeliner/index.jsonl`) → 운영 데이터 누적
- 실패 패턴 분석을 통한 매트릭스 개정은 ADR 절차

## 11. 부록 A — verdict JSON 전체 schema

```json
{
  "schema_version": "1.0",
  "task_id": "F03",
  "dispatcher": "user | auto-cycle",
  "plan_slug": "<slug or null>",
  "verdict": "PASS | FAIL | PARTIAL | BLOCK",
  "reason": "<reason code or null>",
  "next_action": "commit+ship+deploy | review_needed | block",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "duration_seconds": 123.4,
  "stages": {
    "be": {
      "skipped": false,
      "ruff": "clean | dirty",
      "ty": "clean | dirty",
      "pytest": {"passed": 12, "failed": 0, "skipped": 0}
    },
    "typebridge": {
      "skipped": false,
      "openapi_dump": "ok | failed",
      "fe_codegen_diff": 0,
      "drifted_files": []
    },
    "fe": {
      "skipped": false,
      "biome": "clean | dirty",
      "tsc": "clean | dirty",
      "next_build": "ok | failed"
    },
    "visual": {
      "skipped": false,
      "screenshots_before": ["docs/superpowers/visual-log/<slug>/before-1.png"],
      "screenshots_after": ["docs/superpowers/visual-log/<slug>/after-1.png"],
      "diff_ratio": 0.012,
      "threshold": 0.05
    }
  },
  "ground_truth": {
    "edits_attempted": 7,
    "edits_verified": 7,
    "grep_mismatch": 0,
    "mismatch_files": []
  },
  "adr_triggered": false,
  "adr_sub_task_id": null,
  "adr_sub_verdict": null,
  "files_changed": ["services/buying/app/routers/price.py", "apps/web/app/buying/price/page.tsx"],
  "evidence_paths": ["artifacts/pipeliner/<sha>/log.txt"]
}
```

## 12. 부록 B — 변경 이력

| 날짜 | 변경 | 작성자 |
|---|---|---|
| 2026-04-30 | 초안 작성 (브레인스토밍 Q1~Q8 결과 종합) | phil |

---

> 본 디자인은 **Proposed** 상태. 사용자 리뷰 후 Accepted 전환 + writing-plans 스킬로 구현 플랜 작성.
