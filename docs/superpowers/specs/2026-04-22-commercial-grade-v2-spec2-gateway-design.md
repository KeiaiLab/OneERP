# Spec II · gateway 14 셀 Commercial Grade v2 실전 — Design

> 작성: 2026-04-22
> 저자: Phil · Claude Opus 4.7
> 상태: Draft (사용자 리뷰 대기)
> 선행: Spec I `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md` (머지됨 · PR #81)
> 선행 ADR: `docs/governance/adr/0016-commercial-grade-v2-evidence.md` · `docs/governance/adr/gateway-commercial-v2.md`

## 0. 요약

Spec I 에서 구축한 Commercial Grade v2 증거 엔진(`/commercial-engine`)을 **첫 실전 적용** 하여 gateway 모듈의 T1+T2 게이트 14 개를 commercial-ready 수준으로 끌어올린다. 파일럿 3 셀(G1-1/G1-4/G4-2)에 더해 14 셀이 PASS 되면 gateway 는 17/23 = pre-commercial 에 도달한다.

본 Spec 의 2 차 목적은 **엔진 실전 검증**. 14 셀 작업을 통해 ce-planner 의 dispatch · ce-reviewer 의 교차 검증·replay·회귀 감지 · `commercial_readiness.py v2` 의 판정이 현실에서 제대로 작동하는지 증명한다.

T3 6 셀(staging 필요)은 **Spec II.5** 로 분리. 이 Spec 은 T1+T2 만 다룬다.

## 1. 배경

### 1.1 Spec I 결과

- Ralph-Loop 영구 폐기 · v1→v2 전면 리셋 · 3-Tier 증거 모델 · 5-Role 에이전트 팀 · 23 게이트 `commercial_readiness.py v2` · `/commercial-engine` 8 subcommand · 파일럿 3 셀 PASS
- 전체 baseline: 3/1081 (0.28%)
- gateway score: 3/23
- 엔진 실전 사용: **0 건** (slash command 는 있지만 호출된 적 없음)

### 1.2 Spec II 필요성

Spec I 의 가장 큰 미지수는 "엔진이 실전에서 작동하는가". 파일럿 3 셀은 내가 직접 인라인으로 조작한 것이고, `/commercial-engine wave` 호출은 한 번도 없었다. 엔진이 현실에서 버그 없이 돌아야 Spec III~V 확산이 가능하므로, Spec II 에서 반드시 실전 검증이 필요하다.

## 2. 목표 / Non-Goals

### 2.1 목표

- gateway 14 셀 (T1+T2 게이트) 에 `/commercial-engine wave` 실전 적용
- ce-planner 병렬 dispatch 작동 검증 (artisan+scribe ≤5, executor ≤8)
- 2 레이어 의존 처리 (L0 11 셀 · L1 3 셀)
- gateway 라벨 beta 이상 도달
- 엔진 버그 노출 시 Spec II.1 분기

### 2.2 Non-Goals

- T3 6 셀 (G2-2·G2-4·G4-3/4/5·G5-3) — Spec II.5 로 이관
- 다른 46 모듈 — Spec III 이후
- 엔진 구조적 리팩토링 — 버그 감지 시 Spec II.1 분기
- Staging 환경 구축 — Spec II.5

## 3. 핵심 원칙 (불변)

1. **`/commercial-engine wave` 실전 사용** — subagent 직접 dispatch 금지
2. **ce-planner 병렬 dispatch** — 독립 도메인 셀은 동시 처리
3. **기존 v1 자산 보강 우선** — 전면 재작성 전 Read 후 확장 시도
4. **T3 건드림 금지** — T3 증거 생성 시도 시 즉시 중단
5. **사용자 승인 게이트 2 회** — wave 시작 시 + L0→L1 전환 시

## 4. 스코프 (14 게이트)

| 영역 | 게이트 | Tier | 레이어 |
|---|---|---|---|
| G1 | G1-2 OpenAPI | T1+T2 | L0 |
| G1 | G1-3 통합 테스트 | T1+T2 | L0 |
| G1 | G1-5 UI | T1+T2 | **L1** (G1-2 의존) |
| G2 | G2-1 SLO | T2 | L0 |
| G2 | G2-3 perf 회귀 | T1 | L0 |
| G2 | G2-5 i18n | T1 | L0 |
| G3 | G3-1 authN | T1+T2 | L0 |
| G3 | G3-2 시크릿 | T2 | **L1** (G3-1 의존) |
| G3 | G3-3 RBAC | T1 | **L1** (G3-1 의존) |
| G3 | G3-4 감사 | T1 | L0 |
| G3 | G3-5 dep audit | T1 | L0 |
| G4 | G4-1 모니터링 | T2 | L0 |
| G5 | G5-1 매뉴얼 | T1+T2 | L0 |
| G5 | G5-2 튜토리얼 | T1+T2 | L0 |

## 5. 의존 그래프

```
             G1-2 OpenAPI ──┐
                            ├─> G1-5 UI (API 호출 의존)
             G3-1 authN ────┤
                ├─> G3-2 시크릿 (OIDC 라우트 의존)
                └─> G3-3 RBAC (auth context 의존)

             G3-4 감사 ──── 독립
             G3-5 dep ───── 독립
             G2-5 i18n ──── 독립
             G2-3 perf ──── 독립
             G1-3 통합 ──── 독립
             G4-1 모니터링 ─ 독립
             G2-1 SLO ───── 독립
             G5-1 매뉴얼 ── 독립
             G5-2 튜토리얼 ─ 독립
```

### 레이어 분할
- **L0 (11 셀)**: 의존 없음. Wave 시작 즉시 병렬 dispatch.
- **L1 (3 셀)**: L0 의 G1-2·G3-1 완료 후 dispatch.

## 6. 자원 배분 (5 Role 에이전트)

### ce-planner (싱글톤)
- Wave 시작 preflight (11 블로커)
- `wave_planner.plan_wave(status, max_cells=14, modules=["gateway"], dependencies={...})` 호출
- L0 dispatch · 완료 확인 · L1 dispatch
- 각 배치 직전 AskUserQuestion

### ce-artisan (실코드) — 병렬 최대 5
- G1-2 OpenAPI (FastAPI `app.openapi()` → yaml)
- G1-3 통합 테스트 (TDD 3 파일)
- G1-5 UI Playwright (L1)
- G3-1 authN 7 테스트 (TDD)
- G3-3 RBAC rego (L1)
- G3-4 감사 route 주입

### ce-scribe (문서) — artisan+scribe 합계 ≤ 5
- G2-1 SLO 문서
- G2-5 i18n (번역 · 커버리지 측정)
- G4-1 Grafana alerts yaml
- G5-1 매뉴얼 보강 (기존 v1 → ≥250 라인)
- G5-2 튜토리얼 보강 (≥300 라인)

### ce-executor (실행·증거) — 최대 8
- schemathesis · pytest integration/security · Playwright · opa test · pip-audit/pnpm audit · i18n coverage · regression.py · ExternalSecrets rotation

### ce-reviewer (싱글톤)
- L0 완료 후 1 차 · L1 완료 후 2 차
- trivial 테스트 차단 · 얕은 문서 차단 · 20% replay · 회귀 감지

## 7. 게이트별 산출물

### G1-2 OpenAPI
- **보강**: 없음 (신규)
- `services/platform/gateway/openapi.yaml` (FastAPI `app.openapi()`)
- `docs/api/gateway/examples/` 하위 request/response ≥ 3 쌍
- T1: `artifacts/T1/G1-2/gateway/<ts>.log` (schemathesis exit 0)
- T2: CI workflow run

### G1-3 통합 테스트
- **보강**: 없음 (신규)
- `tests/integration/gateway/test_auth_flow.py` · `test_tenant_routing.py` · `test_rate_limit.py`
- `conftest.py` (FastAPI TestClient + fake DB)
- T1: coverage ≥ 60%
- T2: CI 재실행

### G1-5 UI (L1)
- **보강**: `web/` 아래 gateway 관련 페이지 존재 여부 확인 후 판단
- `tests/playwright/ui/gateway/test_login_smoke.py` (Spec I skip → 활성화) · `test_tenant_switch.py` · `test_admin_console.py`
- a11y `@axe-core/playwright` 0 violations
- T1: `artifacts/playwright/gateway/report-<ts>.html`
- T2: CI headless

### G2-1 SLO
- **보강**: `docs/infra/ops/slo.md` 에 `## gateway` 섹션 추가
- availability_target: 99.9% · latency_p95_target: 200ms · error_budget: 43.2min/month
- Prometheus 쿼리 링크 ≥ 2
- T2: `artifacts/slo/gateway-30d.json` (staging Prometheus 없으면 시뮬레이션 명시)

### G2-3 perf 회귀
- **보강**: `scripts/perf/regression.py` 기존 (iter 12)
- T1: `artifacts/T1/G2-3/gateway/<ts>.log` exit 0

### G2-5 i18n
- **보강**: `web/locales/gateway/` 존재 여부
- ko.json · en.json · ja.json ≥ 95% 커버리지
- 하드코딩 grep 0
- T1: verification `{locale_coverage: 0.95}`

### G3-1 authN
- **보강**: 기존 `auth.py` 라우트
- `tests/security/gateway/test_auth_*.py` 7 종 (valid/expired/revoked/malformed/missing/replay/scope-violation)
- T1+T2

### G3-2 시크릿 (L1)
- **보강**: 없음
- `deploy/secrets/gateway/externalsecret.yaml`
- `scripts/secrets/rotate-gateway.sh`
- 평문 grep 0
- T2: `artifacts/secrets/gateway-rotation-<ts>.log` (ESO 부재 시 Spec II.5 이관)

### G3-3 RBAC (L1)
- **보강**: 없음
- `policies/gateway/routes.rego` · `admin.rego`
- `routes_test.rego` ≥ 5 케이스
- T1: `opa test` exit 0

### G3-4 감사
- **보강**: `audit_hooks.py` 존재 확인
- mutation route 당 최소 1 건 `emit_audit_event` 호출
- `docs/security/audit-retention-gateway.md` (3 개월)
- T1: verification route 호출 수

### G3-5 dep audit
- **보강**: `scripts/ci/dep_audit.sh` 기존 (iter 12)
- `--module gateway` 실행 · 7 일 이내 로그
- high/critical CVE 0
- `.github/workflows/dep-audit.yml` 주간 자동화

### G4-1 모니터링
- **보강**: `deploy/monitoring/dashboards/oneerp-gateway.json` 기존 → `deploy/monitoring/grafana/gateway-overview.json` 이동·확장
- `deploy/monitoring/alerts/gateway.yaml` ≥ 5 rule
- T2: `artifacts/alerts/gateway-fired.log` (staging 부재 시 이관)

### G5-1 매뉴얼
- **보강**: `docs/user-manual/gateway.md` (iter 11, 얕은 예상)
- ≥ 250 라인 · 8 H2 섹션 · 스크린샷 ≥ 5
- Playwright 자동 생성 스크립트
- T1+T2

### G5-2 튜토리얼
- **보강**: `docs/tutorials/gateway.md` (iter 11)
- ≥ 300 라인 · fenced code block ≥ 10
- "신규 테넌트 온보딩" 시나리오

## 8. 실전 워크플로

### 준비
1. `git checkout -b feat/commercial-grade-v2-spec2-gateway`
2. 사전 smoke: `uv run pytest tests/unit/engine/ -q` → 24/24 · `commercial_readiness --module gateway` → score 3

### 실행 (`/commercial-engine wave`)
3. 호출: `/commercial-engine wave --module gateway --max 14`
4. ce-planner preflight (11 블로커)
5. `wave_planner.plan_wave(dependencies={"G1-5": ["G1-2"], "G3-2": ["G3-1"], "G3-3": ["G3-1"]})`
6. **사용자 승인 게이트 1**: "14 셀 2 레이어 dispatch 승인?"
7. L0 Batch 1 dispatch (자원 한도 내 최대)
8. Batch 1 완료 → Batch 2 dispatch
9. L0 전체 완료 → ce-reviewer 1 차 (20% replay)
10. **사용자 승인 게이트 2**: "L0 N/11 PASS · L1 3 셀 진행?"
11. L1 dispatch (G1-5 + G3-2 + G3-3)
12. L1 완료 → ce-reviewer 2 차
13. 감사 재실행 + 2 커밋 (feature + progress)

### 사후
14. `commercial_readiness --verify-evidence` 20% 전수 replay
15. PROGRESS.md v2 Wave Log 1 행 추가
16. gateway 라벨 beta/pre-commercial 확인
17. PR 생성

## 9. 실패 복구

| 실패 | 대응 |
|---|---|
| 11 블로커 감지 | wave 즉시 중단 · 블로커 보고 |
| 사용자 승인 거부 | wave 취소 · 작업 0 |
| 개별 셀 artisan 실패 | not_implemented 유지 · 나머지 계속 |
| T2 증거 불가 (staging) | partial/fail · 유연 완료 허용 |
| ce-reviewer BLOCKED | 커밋 보류 · 수정 · 재실행 |
| 엔진 자체 버그 | Spec II.1 분기 · 수정 후 재시작 |
| 회귀 감지 | 블로커 #9 · 롤백 제안 |
| commit 훅 실패 | 분석 · 새 커밋 |

## 10. 리스크 매트릭스

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| 엔진 버그 노출 | 높음 | 중 | Spec II.1 분기 체계 |
| 14 셀 투입 토큰 폭발 | 중 | 중 | 자원 한도 준수 · 배치 분할 |
| staging 필요 셀 T2 불가 | 높음 | 낮음 | 유연 완료 · Spec II.5 이관 |
| plan_wave 선행조건 미지원 | 중 | 낮음 | T2 에서 dependencies 매개변수 추가 |
| v1 자산 보강 실패 | 중 | 낮음 | 재작성 폴백 허용 |
| 20% replay 오탐 | 낮음 | 낮음 | verification 필드 우선 |
| gateway UI 페이지 부재 | 중 | 중 | G1-5 not_implemented 유지 · Spec III 이관 |
| G3-4 route 주입 회귀 | 중 | 높음 | TDD 강제 · 기존 단위 테스트 재실행 |
| reviewer 회귀 놓침 | 낮음 | 높음 | 감사 재실행 평면 diff |
| PR 충돌 (submodule) | 중 | 낮음 | feature branch 격리 |

## 11. Spec II.1 분기 조건

엔진 버그 발견 시:
- **소규모** (single function 버그 · lint 수준): Spec II 범위에서 즉시 수정
- **구조적** (에이전트 상호작용·dispatch·validator 규약): Spec II.1 필수
- **감사 기준 부적절** (v2 기준 현실 괴리): ADR-0016 amendment

판별: "이 수정이 `commercial_readiness.py` 또는 `scripts/engine/` 구조 변경인가?" yes → Spec II.1.

## 12. 구현 순서 (5 Task)

| Task | 내용 | 커밋 |
|---|---|---|
| T1. 준비 | 브랜치 · 사전 점검 · 엔진 smoke | 0 |
| T2. `wave_planner` 보강 | `plan_wave(dependencies=...)` 매개변수 + 단위 테스트 | 1 |
| T3. Wave 실전 실행 | `/commercial-engine wave --module gateway --max 14` | 2 (feature + progress) |
| T4. 엔진 검증 체크 | §13 9 항목 · ADR-0016 amendment | 1 |
| T5. 마무리 · PR | PROGRESS 갱신 · PR 생성 | 1 (progress) |

## 13. 엔진 실전 검증 체크 (T4)

- [ ] ce-planner 가 11 블로커 정확히 판정
- [ ] `plan_wave()` 가 14 셀을 선행조건 충족 순서로 선정
- [ ] artisan/scribe/executor 병렬 dispatch 실제로 동시 실행
- [ ] ce-reviewer 20% replay 가 실제로 수행되고 결과 보고
- [ ] AskUserQuestion 2 회 발동
- [ ] 감사 재실행 델타 정확 (수동 계산 대비)
- [ ] 회귀 감지가 파일럿 3 셀 보호
- [ ] feature + progress 2 커밋 규약 준수
- [ ] Evidence-SHA · Wave-ID 필드 커밋 메시지 포함

## 14. 종료 조건 (2 겹)

### 겹 1 — 셀 결과 (C2 유연)
- [ ] gateway 최소 12/14 PASS (14 셀 중)
- [ ] 회귀 0
- [ ] gateway 라벨 beta 이상

### 겹 2 — 엔진 검증
- [ ] §13 9 항목 전부 체크
- [ ] 엔진 버그 0 건 (발견 시 Spec II.1 분기)

## 15. 결과물 (기대)

| 항목 | Spec II 전 | Spec II 후 |
|---|---|---|
| gateway score | 3/23 | 15~17/23 |
| gateway 라벨 | none | beta ~ pre-commercial |
| 전체 baseline | 3/1081 (0.28%) | ~17/1081 (1.6%) |
| 검증된 엔진 기능 | 파일럿 3 셀 | 14 셀 · 병렬 dispatch · replay · 회귀 |
| 이관된 T3 셀 | 0 | 6 (Spec II.5) |

## 16. 후속 스펙

- **Spec II.5** — staging 환경 구축 + T3 6 셀
- **Spec III** — accounting + hr 수직 완성 (Spec II 템플릿 재사용)
- **Spec IV** — Wave1 나머지 10 모듈 확산
- **Spec V** — Wave2~4 33 모듈 · 최종 `--verify --strict` exit 0

## 17. 참고

- ADR-0016: `docs/governance/adr/0016-commercial-grade-v2-evidence.md`
- gateway 승격 ADR: `docs/governance/adr/gateway-commercial-v2.md`
- Spec I: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
- Spec I Plan: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`
- 전역 규약: `/Users/phil/.claude/CLAUDE.md` · `.claude/CLAUDE.md` · `AGENTS.md`
