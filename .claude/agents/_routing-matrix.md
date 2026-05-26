# OneERP 에이전트 라우팅 매트릭스

## 목적
어떤 작업에 어느 에이전트를 1차로 호출하고, 어떤 2차 위임이 발생하는지를 표로 명시.
신규 작업 패턴은 행 추가, 기존 룰 변경은 ADR + 본 문서 수정.

## 표

| 작업 유형                                  | 호출자             | 1차 에이전트               | 2차 위임                  | Stage skip          |
|--------------------------------------------|--------------------|---------------------------|---------------------------|---------------------|
| BE+FE 동시 (일반 PR)                       | 사용자/auto-cycle  | oe-feature-pipeliner      | documentation-sync-agent  | —                   |
| BE only (일반 PR, 공개 인터페이스 미변경)  | 사용자/auto-cycle  | oe-feature-pipeliner      | documentation-sync-agent  | typebridge,fe,visual |
| BE only (공개 인터페이스 변경 포함)        | 사용자/auto-cycle  | oe-feature-pipeliner      | documentation-sync-agent  | fe,visual           |
| FE only (일반 PR)                          | 사용자/auto-cycle  | oe-feature-pipeliner      | —                         | be,typebridge       |
| 타입 only sync                             | 사용자/auto-cycle  | oe-feature-pipeliner      | —                         | be,fe,visual        |
| FE 디자인(시각 단독)                       | 사용자             | oe-feature-pipeliner      | —                         | be,typebridge       |
| Commercial Engine wave (G1-*~G5-*)         | /commercial-engine | ce-planner                | ce-artisan/scribe/executor | —                   |
| 의존성 감사                                | 사용자             | dependency-auditor        | —                         | —                   |
| 배포 전 검증                               | 사용자             | pre-deploy-validator      | —                         | —                   |
| 외부 SDK·라이브러리 평가                   | 사용자             | system-architect          | planning-decision-support | —                   |
| 코드 리뷰 (PR 후)                          | 사용자             | feature-dev:code-reviewer | —                         | —                   |
| 한국어 구현 일반 (스크립트/유틸)           | 사용자             | korean-dev-implementer    | —                         | —                   |
| 관측성 결손 분석                           | 사용자             | observability-gap-analyzer| —                         | —                   |
| 배포 가드 / 운영 검토                      | 사용자             | ops-deployment-guardian   | —                         | —                   |
| 의존 체인 모니터링                         | 사용자/cron        | dependency-chain-monitor  | —                         | —                   |
| 크로스 프로젝트 표준화                     | 사용자             | cross-project-standardizer| —                         | —                   |
| 다언어 코드 품질 게이트                    | 사용자/auto-cycle  | code-quality-gate         | —                         | —                   |
| 분석/리뷰 (한국어)                         | 사용자             | professional-analyst-ko   | —                         | —                   |

## 판정 우선순위

1. **호출자 기준 1차 분기**: `/commercial-engine` 호출이면 → ce-planner. 그 외는 일반 흐름.
2. **변경 경로 자동 감지**: `services/*` + `web/*` 동시 → oe-feature-pipeliner (BE+FE 행). `services/*` only → oe-feature-pipeliner (BE only 행, Stage skip 적용). `web/*` only → oe-feature-pipeliner (FE only 행).
3. **plan 메타 override**: `docs/plans/<slug>/INDEX.md`에 `pipeliner: true|false`가 있으면 자동 감지 결과를 덮어씀.
4. **명시 작업 유형**: 위 표의 *비-pipeliner 행*(의존성 감사, 배포 전 검증 등)은 사용자가 직접 호출.

## 충돌 해소 룰

- 동일 task에 두 진입점이 동시 발화 → 후행 BLOCK (verdict: concurrent_dispatch)
- pipeliner와 ce-* 동시 dispatch → 호출자 기준 분기 룰 적용 (commercial-engine 우선)
- 매트릭스에 없는 작업 유형 → 사용자 확인 + 매트릭스 행 추가 (행 추가는 ADR 불필요, 룰 변경은 ADR 필요)

## plan 메타 schema

`docs/plans/<slug>/INDEX.md` frontmatter에서 본 라우팅 시스템이 인식하는 필드:

| 필드                     | 타입                   | 디폴트  | 의미                                                                                                        |
|--------------------------|------------------------|---------|-------------------------------------------------------------------------------------------------------------|
| `pipeliner`              | `auto \| true \| false` | `auto`  | `auto`: 경로 자동 감지 위임. `true`: 자동 미매치라도 강제 dispatch. `false`: 자동 매치라도 dispatch 차단   |
| `pipeliner_skip_stages`  | `list[str]`            | `[]`    | 명시 skip 단계 (`["be","typebridge","fe","visual"]` 부분집합)                                              |
| `adr_required`           | `auto \| true \| false` | `auto`  | `auto`: ADR 자동 감지 룰 사용. `true`/`false`: 강제                                                        |

예시:

    ---
    slug: 2026-05-01-add-price-cache
    created: 2026-05-01
    pipeliner: auto
    pipeliner_skip_stages: ["visual"]
    adr_required: true
    ---

## 변경 절차

- 행 추가: 직접 PR (자동 감지 fallthrough만 영향)
- 행 의미 변경: ADR 먼저 (`docs/governance/adr/`)
- 1차/2차 에이전트 교체: ADR 필수
