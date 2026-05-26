# Commercial Grade v2 · 3자원 증거 엔진 — Design Spec

> 작성: 2026-04-22
> 저자: Phil · Claude Opus 4.7
> 상태: Draft (사용자 리뷰 대기)
> 후속: 이 문서가 승인되면 writing-plans 스킬로 구현 계획 작성

## 0. 요약

OneERP 47 모듈 × 23 게이트 = 1,081 셀을 **실증 증거 기반 상용 제품 수준**으로 끌어올리는 엔진을 설계·구현한다. 현 감사 체계(v1)는 "파일 존재 = PASS" 라는 얕은 기준으로 978/1081 = 90.5% 에 도달했으나, 평균 드릴 28 라인·UAT 36 라인·audit_hooks 37 개 중 실제 route 호출 1 개 등 상용 수준의 실체는 없다. 이 스펙은 다음을 수행한다.

1. Ralph-Loop 자기구동 루프 폐기 → 문서 기반 명시 호출 모델로 전환
2. `commercial_readiness.py v2` 로 감사 기준 전면 강화 (라인·섹션·frontmatter·Tier·증거 artifact)
3. 기존 978 PASS 를 `not_implemented` 로 전면 리셋 (예상 baseline ~14%)
4. 3 자원(에이전트 팀 · Python Playwright · Computer Use) 을 병렬 활용하는 wave 엔진 구축
5. 파일럿 3 셀(gateway × G1-1/G1-4/G4-2) 으로 엔진 작동 증명

본 스펙(Spec I)의 범위는 **엔진 자체**이며, 46 모듈의 실제 상용 완성은 후속 스펙(Spec II·III·…) 에서 진행한다.

## 1. 배경 및 문제 정의

### 1.1 현 상태 (2026-04-22 07:30Z)

- Ralph-Loop iter 19 완료, `PROGRESS.md` 기준 978/1081 = 90.5% passed
- 라벨: commercial-ready **0**, pre-commercial 36, beta 11, alpha 0
- 품질 게이트 baseline 319 대비 현재 **323** (ruff 75·ty 247·biome 0)
- E2E 부트스트랩 4종 중 `test_procure_to_pay.py` 500 에러 미해소 (iter 2 부터)

### 1.2 v1 감사의 구조적 함정

- 드릴 142건 **평균 28 라인**, 141건이 50 라인 미만 (상용 수준 기대치 ≥150)
- UAT 47건 **평균 36 라인**, 전원 50 라인 미만 (기대치 ≥200)
- audit_hooks.py 37 개 배치되었으나 **route 실제 호출은 1 건** (accounting journal_entries)
- iter 6 에서 허위 참조 스크립트 9건 적발 — v1 의 "파일 있음 = PASS" 가 원인

### 1.3 근본 원인

v1 의 감사 스크립트(`scripts/audit/commercial_readiness.py`, 1059 라인) 는 게이트별 특수 로직으로 파일 존재·경로 매칭만 본다. 실행 증거·라인 수·섹션·frontmatter·cross-link 재실행 가능성 등 상용 수준의 실체를 요구하지 않는다.

## 2. 목표 (Non-Goals 명시)

### 2.1 목표

- 3 자원을 병렬 활용하는 문서 기반 엔진
- `commercial_readiness.py v2` — 실증 증거 기반 23 게이트 검증
- 5-Role 에이전트 팀 (`ce-planner`, `ce-artisan`, `ce-scribe`, `ce-executor`, `ce-reviewer`)
- 3-Tier 증거 모델 (T1 로컬·T2 CI·T3 staging) + `artifacts/` 디렉토리 표준
- Ralph-Loop 폐기 + v1→v2 전면 리셋 마이그레이션
- 파일럿 3 셀 (gateway × G1-1/G1-4/G4-2) 로 엔진 작동 증명

### 2.2 Non-Goals (명시적으로 하지 않음)

- 46 모듈 실제 상용 완성 (후속 스펙)
- 새 기능 개발 (기존 기능의 증거·리팩토링·문서화만)
- Ralph-Loop 자기구동 복원 (영구 폐기)
- slash command 명칭 유동화 (확정: `/commercial-engine`)

## 3. 핵심 원칙 (불변)

1. **3-Tier 증거**: 각 게이트는 요구 Tier 지정. 일부만 충족 시 `partial`, 전부 미충족 시 `fail` 또는 `not_implemented`.
2. **영속 증거만 PASS**: Chrome MCP 일회성 조작 산출물은 증거로 불인정. 브라우저 증거는 Python Playwright 스크립트(`tests/playwright/`) 경유.
3. **사용자 승인 게이트**: T3 실행 · Computer Use 발동 · 블로커 감지 시 `AskUserQuestion` 필수.
4. **문서 기반 진행**: 스펙·플랜이 SoT. 엔진은 문서를 읽어 wave 계획. 자기구동 루프 금지.
5. **5-Role 팀**: planner · artisan · scribe · executor · reviewer. 판단 기준 차이로 역할 분리.
6. **전면 리셋**: 기존 978 PASS 는 모두 `not_implemented` 복원 후 v2 기준 재평가.

## 4. 아키텍처

### 4.1 구성 요소

```
┌──────────────────────────────────────────────────────┐
│ Claude Code Session                                  │
│                                                      │
│  [Slash Command] /commercial-engine {subcommand}     │
│       ↓                                              │
│  ┌──────────────────────────────────────────────┐   │
│  │ ce-planner  (singleton)                      │   │
│  │  - preflight (11 블로커 이식)                │   │
│  │  - wave 계획 (독립 게이트 묶음)              │   │
│  │  - 감사 재평가 · 위조 탐지                   │   │
│  └─────────────┬────────────────────────────────┘   │
│                │ dispatch                             │
│   ┌────────────┼─────────────┐                       │
│   ▼            ▼             ▼                       │
│ ┌──────┐  ┌─────────┐  ┌──────────┐                 │
│ │artisan│ │ scribe  │  │ executor │  (병렬 N 인스턴스)│
│ │(코드) │ │(문서)   │  │(Bash)    │                 │
│ └──┬───┘  └────┬────┘  └────┬─────┘                 │
│    │           │            │                        │
│    └───────────┴────────────┘                        │
│                │ outputs                              │
│                ▼                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ ce-reviewer (singleton)                      │   │
│  │  - 교차 검증 · 회귀 감지                     │   │
│  │  - 사용자 승인 게이트 준비                   │   │
│  └──────────────────────────────────────────────┘   │
│                │                                      │
│                ▼                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ AskUserQuestion (T3 / Computer Use 승인)     │   │
│  └──────────────────────────────────────────────┘   │
│                │                                      │
└────────────────┼──────────────────────────────────────┘
                 ▼
   ┌─────────────────────────────────────────────┐
   │ Filesystem / Git                            │
   │  - artifacts/<tier>/<gate>/<module>/...     │
   │  - docs/generated/commercial-status.json    │
   │  - PROGRESS.md (v2 헤더 + iter log 누적)    │
   │  - scripts/engine/*.py                      │
   │  - tests/playwright/*/test_*.py             │
   │  - .claude/agents/ce-*.md                   │
   └─────────────────────────────────────────────┘
```

### 4.2 시스템 경계

**엔진 내부 (Spec I)**

- `/commercial-engine` slash command + 8 subcommand (`status`/`plan`/`wave`/`audit`/`reset-v1`/`staging`/`replay`/`escalate`)
- 5 에이전트 정의 (`.claude/agents/ce-*.md`)
- `scripts/engine/` Python 모듈 (`evidence`, `validators`, `wave_planner`, `dispatcher`, `artifact_writer`, `replay`, `migration/reset_v1`)
- `commercial_readiness.py v2` 업그레이드
- `tests/playwright/` 디렉토리 뼈대 + 샘플 (gateway UI 1)
- `artifacts/` 디렉토리 구조 + 메타데이터 표준
- 마이그레이션 스크립트 (v1 → v2 전면 리셋)

**엔진 외부 (후속 스펙)**

- 모듈별 실제 코드·테스트·문서 작성 (파일럿 3 셀 제외)
- 실제 staging 환경에서 T3 드릴 실행
- 46 모듈 확산 플레이북

## 5. 자원 모델

### 5.1 3 자원의 정확한 정의

| 자원 | 정의 | 증거 성격 |
|---|---|---|
| **에이전트 팀** | Task tool 병렬 subagent — 분석·작성·교차 검증·리뷰 | 문서·리포트·분석 결과 |
| **Python Playwright** | 영속 `.py` 스크립트 — 브라우저 시나리오 재실행·스크린샷·trace | HTML report · screenshot · trace.zip |
| **Computer Use** | 데스크톱 GUI 자동화 — 사용자가 직접 해야 할 일을 대리 | GUI 조작 스크린샷 (제한적) |
| *(기반) Bash* | 셸 명령 실행 (pytest, k6, schemathesis, opa, uv, pnpm, git, ...) | stdout·stderr·exit code·artifact 파일 |

### 5.2 Computer Use 발동 조건 (제한 목록)

1. Playwright 첫 브라우저 로그인 세션 생성 (MFA/OAuth 콜백) — 1 회
2. Grafana 대시보드 수동 편집 (API 자동화 불가 시)
3. Staging 카오스 드릴 실행 직전 사용자 최종 승인
4. 시각적 회귀 판정이 애매할 때 사용자 대면 확인

### 5.3 게이트 × 주 자원 매핑

| 게이트 | 주 도구 | 보조 도구 | Tier |
|---|---|---|---|
| G1-1 ADR | ce-scribe | — | T1 |
| G1-2 OpenAPI | Bash (schemathesis) | scribe | T1+T2 |
| G1-3 통합 테스트 | Bash (pytest) | artisan | T1+T2 |
| G1-4 단위 테스트 | Bash (pytest+mutmut) | artisan | T1 |
| G1-5 UI | **Python Playwright** | artisan · Chrome MCP(탐색) | T1+T2 |
| G2-1 SLO | Bash (promtool·curl) | scribe | T2 |
| G2-2 부하 | Bash (k6) | artisan | T3 |
| G2-3 perf 회귀 | Bash (regression.py) | — | T1 |
| G2-4 chaos | Bash (fault-inject) | scribe | T3 |
| G2-5 i18n | Bash + scribe | — | T1 |
| G3-1 authN | Bash (pytest security) | artisan | T1+T2 |
| G3-2 시크릿 | Bash (rotation + grep) | scribe | T2 |
| G3-3 RBAC | Bash (opa test) | artisan | T1 |
| G3-4 감사 이벤트 | scribe + Bash(grep count) | artisan | T1 |
| G3-5 dep_audit | Bash (pip-audit·pnpm audit) | — | T1 |
| G4-1 모니터링 | **Python Playwright** (Grafana) | Bash · scribe | T2 |
| G4-2 런북 | ce-scribe | — | T1 |
| G4-3 백업 드릴 | Bash (drill runner) | scribe | T3 |
| G4-4 롤백 드릴 | Bash | scribe | T3 |
| G4-5 On-call 드릴 | Bash + scribe | — | T3 |
| G5-1 매뉴얼 | **Python Playwright** + scribe | — | T1+T2 |
| G5-2 튜토리얼 | scribe + Bash (smoke) | — | T1+T2 |
| G5-3 UAT | **Python Playwright + pytest-bdd** | scribe · Bash | T2+T3 |

## 6. 3-Tier 증거 모델

### 6.1 Tier 정의

| Tier | 성격 | 실행 장소 | 저장 | 수명 |
|---|---|---|---|---|
| **T1** | 로컬 로그 | 개발자 머신 / 세션 Bash | `artifacts/T1/` git-tracked | 90 일 |
| **T2** | CI 재실행 | GitHub Actions / Gitea | `artifacts/T2/` (run-id 참조) | 180 일 |
| **T3** | Staging 실증 | Kubernetes staging | `artifacts/T3/` (승인자 서명 포함) | 영구 |

### 6.2 `artifacts/` 디렉토리 구조

```
artifacts/
├── _meta/
│   ├── index.jsonl                        # append-only (sha256·gate·module·tier·ts·exit)
│   └── <sha256>.json                      # 개별 증거 메타
├── T1/<gate>/<module>/<iso-ts>.{log,json}
├── T2/<gate>/<module>/run-<workflow-id>.json
├── T3/<gate>/<module>/
│   ├── staging-<iso-ts>.log
│   └── approval-<iso-ts>.json             # 사용자 승인 서명
├── playwright/<module>/
│   ├── trace-<iso-ts>.zip
│   ├── screenshots/<scenario>.png
│   └── report-<iso-ts>.html
├── coverage/<module>-{unit,integration}.xml
├── mutation/<module>.json
├── schemathesis/<module>-<iso-ts>.log
├── k6/<module>-<iso-ts>.{csv,json}
├── chaos/<module>-<iso-ts>.log
└── drills/G4-{3,4,5}/<module>-<iso-ts>.log
```

### 6.3 메타데이터 표준 (`artifacts/_meta/<sha256>.json`)

```json
{
  "sha256": "a3f4...",
  "gate": "G1-4",
  "module": "gateway",
  "tier": "T1",
  "command": "uv run pytest services/platform/gateway/tests/ --cov=gateway --cov-report=xml",
  "executor": "ce-executor",
  "git_sha": "abc1234",
  "host": "darwin-25.4.0",
  "user": "phil",
  "started_at": "2026-04-22T07:00:00Z",
  "duration_seconds": 42,
  "exit_code": 0,
  "stdout_sha256": "bb12...",
  "stderr_sha256": "cc34...",
  "artifact_paths": [
    "artifacts/T1/G1-4/gateway/2026-04-22T0700Z.log",
    "artifacts/coverage/gateway-unit.xml"
  ],
  "verification": {
    "coverage_line_rate": 0.84,
    "mutation_score": 0.52,
    "meets_threshold_80pct": true
  },
  "parent_evidence": null,
  "replay_command": "scripts/engine/replay.py --sha a3f4..."
}
```

### 6.4 위조 방지

1. **해시 검증**: `scripts/engine/replay.py --sha <sha>` 가 `command` 재실행 시 stdout/stderr 해시와 `_meta` 값이 일치하는지 확인.
2. **Git 추적**: `artifacts/_meta/` 전체 git-tracked. 수정 시 diff 노출.
3. **T2 외부 검증**: CI workflow run id 로 GitHub/Gitea 조회.
4. **T3 승인자 서명**: `approval-<ts>.json` 에 `approver`, `approved_at`, `approval_context`. 승인자는 실제 사람 사용자.
5. **랜덤 샘플 replay**: `/commercial-engine audit --verify-evidence` 가 20% 증거를 재실행 해 무결성 확인. 불일치 시 `tampered` 상태.

### 6.5 Tier 요구 (게이트별)

- **T1 만**: G1-1, G1-4, G2-3, G2-5, G3-3, G3-4, G3-5, G4-2
- **T1+T2**: G1-2, G1-3, G1-5, G3-1, G5-1, G5-2
- **T2**: G2-1, G3-2, G4-1
- **T2+T3**: G5-3
- **T3 만**: G2-2, G2-4, G4-3, G4-4, G4-5

## 7. 5-Role 에이전트 팀

### 7.1 ce-planner (싱글톤)

파일: `.claude/agents/ce-planner.md`

- **책임**: preflight, wave 계획, dispatch 조정, 감사 재평가, 위조 탐지 호출
- **주 도구**: `Read`, `Grep`, `Glob`, `Bash`(read-only), `TaskCreate`, `TaskList`, `AskUserQuestion`, `Task`(dispatch)
- **금지**: `Write`, `Edit`
- **판단 기준**: 11 블로커 감지 → 중단; 독립성·선행조건·자원 한도 내 셀 선정; 영역 순위 G1 < G3 < G4 < G5 < G2

### 7.2 ce-artisan (병렬, 최대 5)

파일: `.claude/agents/ce-artisan.md`

- **책임**: 코드·테스트·Playwright 스크립트 작성. TDD 강제.
- **주 도구**: `Read`, `Write`, `Edit`, `Grep`, `Glob`, `Bash`(lint/typecheck/pytest), `Task`, `TaskCreate`
- **대상 게이트**: G1-3/4/5, G3-1/2/3/4 (route 주입), G4-1 (Playwright)
- **판단 기준**: TDD 절대 강제; 기존 패턴 추적; context7 MCP 조회; wave plan 파일만 수정; 한국어 주석

### 7.3 ce-scribe (병렬, 최대 5)

파일: `.claude/agents/ce-scribe.md`

- **책임**: ADR·런북·매뉴얼·튜토리얼·드릴·UAT 작성
- **주 도구**: `Read`, `Write`, `Edit`, `Grep`, `Glob`, `WebFetch`
- **금지**: 실행 Bash
- **대상 게이트**: G1-1, G4-2/3/4/5, G5-1/2/3
- **판단 기준**: v2 기준 충족 (라인수·섹션·frontmatter·cross-link); Broken link 발견 시 reviewer 리젝

### 7.4 ce-executor (병렬, 최대 8)

파일: `.claude/agents/ce-executor.md`

- **책임**: Bash 실행·artifacts 수집·메타 생성
- **주 도구**: `Bash`, `Read`, `Write`(한정: `artifacts/**`)
- **금지**: `Edit`
- **판단 기준**: 결정론적 실행·재시도 없음(planner 에 에스컬레이션); 매 실행 후 sha256 계산·`_meta` 저장

### 7.5 ce-reviewer (싱글톤)

파일: `.claude/agents/ce-reviewer.md`

- **책임**: 교차 검증·회귀 감지·위조 탐지·사용자 승인 준비
- **주 도구**: `Read`, `Grep`, `Glob`, `Bash`(replay·audit·git diff), `TaskCreate`, `AskUserQuestion`
- **금지**: `Write`, `Edit`
- **판단 기준**: trivial 테스트 차단(`assert True`); 얕은 문서 차단; broken cross-link; 회귀 셀 0; 위조 20% replay

### 7.6 상호작용 경계

| From → To | 허용 |
|---|---|
| planner → artisan/scribe/executor | Task dispatch (병렬) |
| planner → reviewer | Task dispatch (싱글톤) |
| artisan/scribe → executor | 직접 호출 금지 — planner 경유 |
| executor → reviewer | 직접 호출 금지 — planner 경유 |
| reviewer → 사용자 | AskUserQuestion 직접 |
| 모든 에이전트 → 사용자 | planner·reviewer 만 직접 질의 |

### 7.7 병렬 상한

- artisan + scribe 합계 ≤ 5
- executor ≤ 8
- planner / reviewer = 1 (싱글톤)
- **총 최대 동시 subagent: 15**

## 8. Slash Command 표면

파일: `.claude/commands/commercial-engine.md`

Entry: `/commercial-engine <subcommand> [args]`

| Subcommand | 부작용 | 용도 |
|---|---|---|
| `status` | 없음 | 현재 감사 상태·진행률 표시 |
| `plan` | 없음 | 다음 wave 계획 생성·표시 |
| `wave [--module M] [--max N] [--dry-run]` | 있음 | 한 wave 전체 사이클 실행 |
| `audit [--verify-evidence]` | status 갱신 | v2 감사 재실행. 20% replay 검증. |
| `reset-v1 --confirm` | 대규모 (1회) | v1 PASS 전면 리셋 |
| `staging <module> <gate>` | T3 증거 생성 | Staging 에서 T3 게이트 실행 (승인 필수) |
| `replay <sha>` | 없음 | 특정 증거 재실행 |
| `escalate` | HANDOFF.md 작성 | 세션 중단·인수인계 |

## 9. Wave Workflow (7 단계)

```
[1] Preflight
    planner: 11 블로커 스캔
    → 하나라도 감지 시 AskUserQuestion + 중단
[2] Plan
    planner: commercial-status.json 읽음 → FAIL/NOT_IMPLEMENTED 중
             독립 가능 · 선행조건 충족 · 자원 한도 내 셀 선정
             → wave plan JSON 생성
[3] User Approval
    planner: AskUserQuestion 으로 plan 제시
[4] Dispatch (병렬)
    planner → Task(artisan × N) + Task(scribe × M) + Task(executor × K)
[5] Review
    planner → Task(reviewer, 싱글톤)
    → verdict: APPROVED / PARTIAL / BLOCKED
[6] Audit
    planner: commercial_readiness.py v2 재실행 → delta·회귀 확인
[7] Commit
    Step 7a (feature): git commit "feat(<scope>): G<x>-<y> PASS · <module>"
    Step 7b (progress): git commit "chore(progress): wave <id> 기록 (+<delta>/1081)"
```

### 9.1 실패 경로

| 단계 | 실패 동작 |
|---|---|
| Preflight | AskUserQuestion → continue/abort/manual-fix |
| Approval | 거부 시 세션 종료, 변경 0 |
| Dispatch | 개별 실패 → 해당 셀 제외 후 계속 |
| Review BLOCKED | stash/revert + AskUserQuestion |
| Audit 회귀 | 블로커 #9, 커밋 보류, HANDOFF 제안 |
| Commit 실패 | 훅 분석 → 새 커밋 (amend 금지) |

### 9.2 상태 파일

| 파일 | 성격 | 작성자 |
|---|---|---|
| `artifacts/_meta/index.jsonl` | append-only 증거 로그 | executor |
| `artifacts/_meta/<sha>.json` | 개별 증거 메타 | executor |
| `docs/generated/commercial-status.json` | 게이트 상태 SoT | planner (audit) |
| `docs/generated/commercial-status.md` | 사람 판독용 | planner |
| `PROGRESS.md` | wave log | planner (7b) |
| `.planning/engine/waves/<wave-id>.json` | wave plan 아카이브 | planner (2) |
| `HANDOFF.md` | 에스컬레이션 시만 | planner (`escalate`) |

### 9.3 커밋 규약

**Feature 커밋**
```
<type>(<scope>): G<x>-<y> PASS 달성 · <module> [· <module2>]

<본문: 변경 요약 1~3줄 + 증거 sha 참조>

Refs: artifacts/_meta/<sha>.json
      scripts/audit/commercial_readiness.py::_gate_G<x>_<y>

Evidence-SHA: <sha256>
Wave-ID: <wave-id>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Progress 커밋**
```
chore(progress): wave <wave-id> 기록 (+<delta>/1081)

<게이트별 delta 요약>

Wave-ID: <wave-id>
```

## 10. 감사 v2 (`commercial_readiness.py v2`)

### 10.1 공용 헬퍼 `validate_evidence()`

파일: `scripts/engine/validators.py`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ValidationSpec:
    min_lines: int = 0
    required_sections: list[str] | None = None
    required_frontmatter: list[str] | None = None
    frontmatter_age_limits: dict[str, int] | None = None
    cross_links_required: list[str] | None = None
    required_tiers: list[str] | None = None
    artifact_glob: dict[str, str] | None = None
    min_fenced_code_blocks: int | None = None
    min_image_refs: int | None = None
    exit_code_required: int = 0
    stdout_contains: list[str] | None = None
    verification_fields: dict[str, object] | None = None

def validate_evidence(spec: ValidationSpec, gate: str, module: str) -> GateResult: ...
```

### 10.2 게이트 함수 예시

```python
def _gate_G4_2_runbook(module: str) -> GateResult:
    host = _module_to_host(module)
    path = Path(f"docs/ops/runbooks/{host}.md")
    return validate_evidence(
        ValidationSpec(
            min_lines=150,
            required_sections=["개요", "전제 조건", "진단 절차",
                               "복구 절차", "롤백 절차", "에스컬레이션"],
            required_frontmatter=["owner", "module", "last_reviewed"],
            frontmatter_age_limits={"last_reviewed": 90},
            cross_links_required=[
                f"docs/ops/drills/G4-3/*-{module}.md",
                "scripts/ops/*",
            ],
            required_tiers=["T1"],
        ),
        gate="G4-2",
        module=module,
    ).with_path(path)
```

### 10.3 v2 기준 체크리스트 (23 게이트)

| 게이트 | 최소 기준 |
|---|---|
| G1-1 ADR | ≥100 라인, `status`/`date`/`decision`/`consequences` frontmatter |
| G1-2 OpenAPI | `openapi.yaml` + 예시 3쌍 + schemathesis exit 0 |
| G1-3 통합 테스트 | 3+ 파일, pytest pass, coverage ≥60% |
| G1-4 단위 테스트 | coverage ≥80%, mutation ≥50% |
| G1-5 UI | Playwright 3 시나리오, a11y 0 violations, 비주얼 스냅샷 |
| G2-1 SLO | SLO 선언 + Prometheus 쿼리 + 30일 번다운 |
| G2-2 부하 | k6 스크립트 + p95/p99 실측 + baseline 비교 |
| G2-3 perf 회귀 | 최근 30일 회귀 0 건 |
| G2-4 chaos | 실행 로그 + 복구 증거 + MTTR 측정 |
| G2-5 i18n | ko/en/ja 95% 커버리지 + 하드코딩 0 |
| G3-1 authN | OIDC 라우트 + 7종 auth 테스트 pass |
| G3-2 시크릿 | ESO + rotation 스크립트 + 로그 + 평문 grep 0 |
| G3-3 RBAC | OPA 정책 + 테스트 5+ pass |
| G3-4 감사 | mutation route 당 최소 1건 `emit_audit_event` 호출 |
| G3-5 dep_audit | high/critical CVE 0 건 (7일 이내) |
| G4-1 모니터링 | Grafana JSON + 알림 5+ + 30일 fired 이력 |
| G4-2 런북 | ≥150 라인, 6 H2 섹션, `last_reviewed` ≤90일 |
| G4-3 백업 드릴 | ≥150 라인, `evidence` frontmatter, T3 로그, 포스트모템 |
| G4-4 롤백 드릴 | 동상, 마이그레이션 backwards-compat 증거 |
| G4-5 On-call 드릴 | 동상, 호출 체인 + 응답 시간 |
| G5-1 매뉴얼 | ≥250 라인, 스크린샷 5+, 8 H2 섹션 |
| G5-2 튜토리얼 | ≥300 라인, fenced code block 10+ |
| G5-3 UAT | ≥200 라인, Given/When/Then 5+, 승인자 서명, T2+T3 |

### 10.4 판정 룰

```
모든 Tier 충족 + 문서 기준 충족 → "pass"
일부 Tier 충족 + 문서 기준 충족 → "partial"
문서만 있고 Tier 미충족           → "not_implemented"
문서·증거 전혀 없음               → "fail"
증거 해시 불일치                  → "tampered"
```

### 10.5 `commercial-status.json v2` 스키마

```json
{
  "schema_version": "v2.0",
  "generated_at": "2026-04-22T09:00:00Z",
  "baseline": {
    "ruff_errors": 75,
    "ty_diagnostics": 247,
    "biome_errors": 0,
    "total_quality_debt": 322
  },
  "summary": {
    "passed": 3,
    "partial": 0,
    "not_implemented": 1078,
    "failed": 0,
    "tampered": 0,
    "commercial_ready_modules": 0,
    "pre_commercial_modules": 0,
    "beta_modules": 0,
    "alpha_modules": 1
  },
  "reports": [
    {
      "module": "gateway",
      "label": "alpha",
      "score": 3,
      "gates": [
        {
          "id": "G1-1",
          "status": "pass",
          "tiers_met": {"T1": true},
          "evidence_sha": "abc123...",
          "last_verified": "2026-04-22T08:55:00Z"
        }
      ]
    }
  ]
}
```

### 10.6 모듈 라벨 승격 규칙 (v2)

| 라벨 | 조건 |
|---|---|
| `alpha` | G1-1 + G1-2 PASS (≥2) |
| `beta` | G1-1/2/3/4 + G3-1 + G3-4 + G4-2 PASS (≥7) |
| `pre-commercial` | 18/23 PASS |
| `commercial-ready` | 23/23 PASS · 회귀 0 · 최근 180일 내 T3 드릴 존재 |

### 10.7 CLI

```bash
python3 scripts/audit/commercial_readiness.py
python3 scripts/audit/commercial_readiness.py --format json > docs/generated/commercial-status.json
python3 scripts/audit/commercial_readiness.py --module gateway
python3 scripts/audit/commercial_readiness.py --gate G4-2
python3 scripts/audit/commercial_readiness.py --verify-evidence
python3 scripts/audit/commercial_readiness.py --verify --strict  # 완료 판정
```

`--verify --strict` 의 exit 0 이 v1 의 `<promise>ONEERP_COMPLETE</promise>` 를 대체.

## 11. 마이그레이션

### 11.1 Phase 0A — Ralph-Loop 폐기

| 단계 | 액션 | 검증 |
|---|---|---|
| 1 | `.claude/skills/ralph-loop/` 삭제 | `ls .claude/skills/ralph-loop` → No such file |
| 2 | `RALPH-LOOP-PROMPT.md` 삭제 | `test -f RALPH-LOOP-PROMPT.md` → fail |
| 3 | `HANDOFF.md` 재작성 | `grep -i "ralph-loop" HANDOFF.md` → 0 |
| 4 | `AGENTS.md` · `CLAUDE.md` · `.claude/CLAUDE.md` 참조 제거 | `grep -rn "ralph-loop" .claude/ AGENTS.md CLAUDE.md` → 0 |
| 5 | 커밋: `chore(engine): Ralph-Loop 폐기 · /commercial-engine 전환 준비` | git log |

`PROGRESS.md` 의 iter 1~19 기록 보존. 새 헤더 `"## Ralph-Loop 시대 (v1 · 2026-04-16 ~ 2026-04-22)"` + `"## v2 Strict Mode (2026-04-22~)"` 분리.

### 11.2 Phase 0B — v1→v2 전면 리셋

Trigger: `/commercial-engine reset-v1 --confirm`
Executor: `scripts/engine/migration/reset_v1.py`

절차:
1. 사용자 명시 확인 (`--confirm` 필수)
2. 현재 `commercial-status.json` 백업 (`docs/generated/archived/`)
3. `commercial_readiness.py v1 → v2` 교체 (v1 은 `.archived` 로 git mv)
4. v2 감사 실행 (전면 리셋 자동 발생)
5. `PROGRESS.md` v2 baseline 헤더 append
6. 커밋: `chore(engine): v1→v2 전면 리셋 · baseline=<N>/1081`

예상 결과: baseline ~150/1081 = ~14%.

롤백: Phase 0B 직후 문제 발견 시 `git revert`, 1회 한정.

## 12. 파일럿 — 엔진 자체 검증 (3 셀)

### 12.1 작업 내용

| 셀 | 담당 | 검증 |
|---|---|---|
| `gateway × G1-1 ADR` | ce-scribe | ≥100 라인, frontmatter 4필드, T1 증거 |
| `gateway × G1-4 단위 테스트` | ce-artisan + ce-executor | coverage ≥80%, mutation ≥50%, T1 로그 |
| `gateway × G4-2 런북` | ce-scribe + ce-reviewer | ≥150 라인, 6 섹션, frontmatter 3필드, cross-link 2+ |

### 12.2 실행 순서

```
1. /commercial-engine status       # v2 baseline 확인
2. /commercial-engine plan          # 3셀 wave 계획
3. /commercial-engine wave          # 7단계 사이클 실행
4. /commercial-engine audit         # 최종 확인
5. /commercial-engine audit --verify-evidence  # 20% replay
```

### 12.3 파일럿 완료 체크 (8 항목)

- [ ] `ce-planner` wave plan 생성·사용자 승인
- [ ] `ce-scribe` gateway ADR·런북 생성
- [ ] `ce-artisan` gateway 단위 테스트 작성
- [ ] `ce-executor` pytest 실행·coverage·mutation 결과 수집
- [ ] `ce-reviewer` 교차 검증 통과
- [ ] `commercial_readiness.py v2` 3셀 PASS 판정
- [ ] `--verify-evidence` 20% replay 통과
- [ ] Feature + Progress 2 커밋, `PROGRESS.md v2` iter 20 기록

## 13. 구현 순서

| Step | 내용 | 커밋 |
|---|---|---|
| 1 | Phase 0A Ralph-Loop 폐기 | 커밋 1 |
| 2 | `scripts/engine/` 뼈대 (`evidence.py`, `validators.py`) + 단위 테스트 | 커밋 2 |
| 3 | `commercial_readiness.py v2` (게이트 23개) + 단위 테스트 | 커밋 3 |
| 4 | 5 에이전트 정의 (`.claude/agents/ce-*.md`) | 커밋 4 |
| 5 | `/commercial-engine` slash command + 8 subcommand | 커밋 5 |
| 6 | `tests/playwright/` 뼈대 + gateway 샘플 | 커밋 6 |
| 7 | `artifacts/` 디렉토리 + `.gitignore` 규칙 | 커밋 7 |
| 8 | Phase 0B `reset_v1.py` 실행 | 커밋 8 |
| 9 | 파일럿 실행 — gateway 3셀 PASS | 커밋 9+10 |
| 10 | ADR-0016 박제 + Spec I 종료 선언 | 커밋 11 |

## 14. Spec I 종료 조건

- [ ] Ralph-Loop 폐기 완료
- [ ] v2 전면 리셋 완료
- [ ] `/commercial-engine` + 8 subcommand 구현
- [ ] 5 에이전트 정의
- [ ] `commercial_readiness.py v2` 게이트 23 + 단위 테스트
- [ ] `scripts/engine/` 모듈 구현
- [ ] `tests/playwright/` 뼈대 + gateway 샘플
- [ ] `artifacts/` 디렉토리 구조
- [ ] 파일럿 3 셀 PASS + `--verify-evidence`
- [ ] 품질 게이트 회귀 0 (ruff/ty/biome 현상 유지)
- [ ] ADR-0016 커밋

## 15. 후속 스펙 (Non-Goals)

- **Spec II**: gateway 나머지 20 게이트 + 감사 v2 조정 1차
- **Spec III**: accounting·hr 완성 + 감사 v2 조정 2차
- **Spec IV**: Wave1 (12 모듈) 확산 플레이북
- **Spec V**: Wave2~4 확산 · 최종 ONEERP_COMPLETE

## 16. 위험·대응

| 위험 | 확률 | 대응 |
|---|---|---|
| v2 기준이 현실적으로 달성 불가 | 중 | 파일럿 후 기준 조정. ADR-0016 는 확장·완화 가능한 living doc |
| 전면 리셋 후 baseline 너무 낮아 사기 저하 | 중 | PROGRESS.md 에 "v1-grandfathered" 섹션으로 구작업 시각화 |
| Playwright 초기 세션(MFA) 설정 난항 | 중 | Computer Use 최초 1회 사용 절차를 별도 런북에 문서화 |
| 에이전트 상호작용 경계 위반 | 낮음 | planner/reviewer 만 AskUserQuestion — 규약 위반 시 즉시 에스컬레이션 |
| 위조 탐지 오탐 (결정론 불가 명령) | 낮음 | 비결정론 명령은 `verification` 필드에 관대 규칙 지정 |
| T3 staging 환경 미준비 | 높음 | Spec I 에서는 T3 안 건드림. Spec II 이후 staging 확보 전제 |

## 17. 참고

- ADR-0001 (23 품질 기준 정본): `docs/governance/adr/0001-commercial-grade-definition.md`
- ADR-0012 (Wave 매핑): `docs/governance/adr/0012-commercialization-wave-mapping.md`
- v1 Ralph-Loop spec: `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md`
- 기존 v1 감사 스크립트: `scripts/audit/commercial_readiness.py` (1059 라인)
- 전역 규약: `/Users/phil/.claude/CLAUDE.md`, `.claude/CLAUDE.md`, `AGENTS.md`
