# ADR-0017: oe-feature-pipeliner + 라우팅 매트릭스 도입

- Date: 2026-04-30
- Status: Accepted
- Authors: @phil

## Context

OneERP는 2026-04-30 기준 18종 에이전트(commercial-engine 5종 + 글로벌 13종)를 운용한다. 그러나 *commercial-engine 외부의 일반 PR* — BE 핸들러 + 타입 덤프 + FE 컴포넌트 + visual 검증이 한 사슬로 묶인 변경 — 에 적합한 통합 디스패처가 없었다.

세 가지 구조적 결손이 한 사슬(`BE 핸들러 → openapi 덤프 → FE 타입 생성 → FE 컴포넌트 → visual 검증`)로 연결된다는 점에서 *통합 디스패처 + 협업 매트릭스*가 필요하다고 판단했다:

1. **결손 (1)**: `ce-artisan`은 commercial-engine wave에 묶여 있어 일반 PR에 사용 불가.
2. **결손 (2)**: `korean-dev-implementer`는 일반론적이며 FE+visual 사이클을 자동화하지 않는다.
3. **결손 (6)**: `visual-dual-loop` 스킬을 사람이 수동 추적하는 상태였다.

이에 더해 18종 에이전트 간 협업 룰이 비공식 구전 지식으로만 존재해 *라우팅 의사결정이 사람 의존*이었다.

## Decision

### 1. 신규 에이전트: `oe-feature-pipeliner`

- **모델**: sonnet, 도구 화이트리스트 한정
- **4 Stage**: BE(핸들러 구현) → 타입(openapi 덤프 + FE 타입 생성) → FE(컴포넌트 구현) → visual(스크린샷 검증)
- Edit 직후 grep ground-truth 검증 의무 (`Edit success ≠ 적용 보증`)
- ADR 자동 감지 시 `documentation-sync-agent`에 sub-task 위임
- `docs/governance/**` Write 권한 없음 — 문서는 위임

### 2. 진입점 2개

- 사용자 명시 호출
- auto-cycle Phase 3 dispatcher 자동 감지 (commercial-engine 제외)
- 트리거: 변경 경로 패턴 자동 감지 + plan 메타 `pipeliner: true|false` override

### 3. 라우팅 매트릭스

- 위치: `.claude/agents/_routing-matrix.md`
- 18종 에이전트 협업 룰을 markdown 표(18행)로 명문화
- 행 추가만으로 진화 가능 — 구조적 확장성 확보

### 4. 검증 인프라 6 모듈

`scripts/agents/` 아래 6 파이썬 모듈:

| 모듈 | 역할 |
|------|------|
| `validate_frontmatter.py` | 에이전트 YAML frontmatter 필수 필드 검증 |
| `check_matrix_consistency.py` | 매트릭스 행·열 정합성 검증 |
| `routing.py` | 경로 패턴 → 에이전트 매핑 |
| `adr_detection.py` | ADR 트리거 조건 자동 감지 |
| `ground_truth.py` | Edit 후 grep 검증 헬퍼 |
| `stage_skip.py` | Stage 조건부 스킵 로직 |

각 모듈에 단위 테스트 동반.

### 5. 책임 경계

- pipeliner 담당: BE/타입/FE/visual
- 문서(`docs/governance/**`) Write 권한 없음 — `documentation-sync-agent` 위임
- Bash 명령 화이트리스트 + 도구 화이트리스트로 권한 사고 위험 최소화

### 채택 근거 (Q1~Q8 / V1)

브레인스토밍에서 8개의 핵심 분기 질문을 거쳐 V1(통합 단일 에이전트 + 매트릭스 1장) 채택:

| Q | 결정 | 근거 |
|---|---|---|
| Q1 | D — 신규 정의 + 기존 정비 동시 | 기존만 정비하면 OneERP 고유 워크플로 결손 |
| Q2 | b — SP1+SP2 묶음 (T2) | 매트릭스의 빈 칸이 곧 신규 에이전트 후보 |
| Q3 | 결손 우선순위 (2)→(1)→(6) 사슬 | 세 결손이 한 사슬(Frontend feature pipeline) |
| Q4 | A — 통합 단일 에이전트 | atomic 커밋 선호 + drift 같은 PR에서 묶임 |
| Q5 | B — auto-cycle Phase 3 자동 + 사용자 직접 | 자율 dispatch 우선 |
| Q6 | e — 경로 자동 + plan 메타 override | 누락 케이스를 메타로 보완 |
| Q7 | b — 4단계 게이트 + Edit 후 grep ground-truth | Phase 4 회귀와 분업 |
| Q8 | b — pipeliner는 BE/타입/FE/visual만, 문서 위임 | 도구 화이트리스트 좁게 유지 |

V1 채택 근거: 단일 진입점 + 도구 화이트리스트 한정 + plan 메타 on/off. V2(확장)는 1년차 over-engineering, V3(축소)는 자율 dispatch 결정과 모순.

## Consequences

### 긍정

- *Atomic 커밋 선호*와 부합 — 한 사이클 = 한 에이전트 = 한 PR.
- 도구 화이트리스트 + Bash 화이트리스트로 권한 사고 위험 최소화.
- auto-cycle Phase 3 자율 dispatch 가능.
- 라우팅 매트릭스가 *살아있는 문서* — 18종 인지 부하를 데이터 구조에 위임.

### 부정

- 통합 단일 에이전트라 도구 화이트리스트가 분업안보다 넓음. 화이트리스트 + ground-truth 검증 + Phase 4 verify가 다층 방어.
- 라우팅 매트릭스 stale 시 라우팅 오류 발생 가능. 정적 검증 스크립트가 매 commit에서 PASS 강제.
- auto-cycle Phase 3 측 변경(marker 주입·경로 패턴 감지)은 별도 후속 작업.

### 트레이드오프

- 통합(A) 선택은 분업(B)보다 *내부 단계 격리*가 약하지만, *외부 인터페이스 단순함*과 *atomic 커밋 자연성*을 우선.
- haiku 분리(B의 typebridge)로 얻을 수 있는 비용 절감은 포기. 1년차에 over-engineering 회피 우선.

## Alternatives Considered

| 대안 | 기각 사유 |
|------|----------|
| V2 확장 (`oe-doc-sync-router` 추가) | ADR 라우팅 전담 보조 에이전트. 1년차 over-engineering, 필요 시 분할로 충분. |
| V3 축소 (pipeliner 없이 매트릭스만) | 결손 (1)(2)(6) 사람이 메움. 자율 dispatch 불가 — auto-cycle Q5의 B 결정과 모순. |
| B 분업 (3 에이전트, typebridge haiku 분리) | atomic 커밋과 sub-agent 컨텍스트 단절 비용 → 통합(A) 선택. |
| C 분업 (2 에이전트, BE+타입 / FE+visual) | 타입 drift 양쪽 검증 중복 → 통합(A) 선택. |

## Refs

- 디자인 스펙: `docs/superpowers/specs/2026-04-30-agent-team-composition-design.md`
- 구현 플랜: `docs/superpowers/plans/2026-04-30-agent-team-composition.md`
- 관련 ADR: ADR-0011 (코드 클러스터), ADR-0014 (런타임 plane), ADR-0016 (commercial-grade v2)
- 거버넌스: 글로벌 standards/adr.md, OneERP AGENTS.md
