---
title: Commercial Grade v2 — Spec III · Spec II.5 · 품질 게이트 통합 설계
date: 2026-04-22
status: approved
spec_version: 1.0
tracks:
  - spec-iii-accounting-hr
  - spec-ii-half-staging-t3
  - quality-gate-baseline
predecessors:
  - 2026-04-22-commercial-grade-v2-triple-resource-design.md
  - 2026-04-22-commercial-grade-v2-spec2-gateway-design.md
---

# Commercial Grade v2 — Spec III · Spec II.5 · 품질 게이트 통합 설계

## 0. 개요

본 설계는 Commercial Grade v2 증거 엔진의 현재 상태(score 13/23, gateway 14셀 중 10 PASS)에서 출발하여, 완료조건 23/23 도달까지 남은 3 트랙을 하나의 계획 단위로 조율한다. 세 트랙은 서로 다른 축(모듈 수평 · tier 수직 · 횡단 규율)에서 움직이며, 단일 본문 + 3 부록 구조로 관리된다.

### 0.1 3 트랙 요약

| 트랙 | 축 | 범위 | 완료 지표 |
|------|----|------|----------|
| **Spec III** (부록 A) | 모듈 수평 확장 | accounting + hr 수직 완성 (23게이트 × 2모듈) | accounting 14/14 T1+T2 · hr 12+/14 T1+T2 · 종합 score ≥ 17/23 |
| **Spec II.5** (부록 B) | tier 수직 확장 | gateway T3 6셀 + staging 인프라 | gateway T3 6/6 PASS · staging up/green · 종합 score ≥ 19/23 |
| **품질 게이트** (부록 C) | 횡단 규율 | ruff 73 → floor, ratchet 가드 설치 | CI ratchet 3 PR 연속 pass · Wave A ≤ 30 · Wave D ≤ 5(option F) 또는 0(option 0) |

### 0.2 실행 순서 — 순서 B (품질 게이트 선행 + Spec II.5/III 병렬)

```
Wave A (1주)
  └─ 품질 게이트 1차 정리: 설정 완화(+12) → unsafe-fix(+32) → baseline ≤ 30
     + ratchet CI 도입

Wave B (2주, 병렬 2 worktree)
  ├─ Spec II.5 Phase 1: staging k8s NS / ExternalSecret / 관측성 정합
  └─ Spec III Phase 1: accounting L0 11셀 (gateway 템플릿 재사용)

Wave C (2주, 병렬 2 worktree)
  ├─ Spec II.5 Phase 2: T3 6셀 gateway (G2-2/G2-4/G4-3/G4-4/G4-5/G5-3)
  └─ Spec III Phase 2: hr 선행 아키텍처 정합 (events/config) → hr L0 11셀

Wave D (1주)
  └─ Spec III Phase 3: accounting + hr L1 3셀 (G1-5 Playwright / G3-2 ES / G3-3 OPA)
     + 품질 게이트 최종 정리 (baseline 0 또는 합의된 floor)
```

총 기간 **6주**. Wave 당 **ce-planner** 병렬 dispatch, 최대 동시 실행 셀 수 **6** (리뷰 대역폭 상한).

### 0.3 본 설계가 보증하는 것 · 보증하지 않는 것

**보증한다**:
- 3 트랙이 서로의 산출물을 갈등 없이 흡수하도록 의존그래프 명시
- 각 트랙의 최소 실행 가능 정의(MVD)와 완료 판정 공식
- Spec II에서 드러난 회귀(T2 artifact 수집 미구현)의 재발 차단
- 비가역·과금·시크릿 작업에 대한 사전 확인 게이트

**보증하지 않는다**:
- 프로덕션 배포 · prod 이미지 태깅 (Spec II.5 범위에서 명시적으로 제외)
- 46개 나머지 모듈의 23게이트 이행 (Spec IV 이후)
- 외부 서비스 실사(감사·SOC2) — 증거 엔진이 기계적 체크만 수행

## 1. 현재 상태 · 출발선

### 1.1 엔진·산출물 (2026-04-22 기준)

- **코드 자산**: `scripts/engine/` (wave_planner / validators), `scripts/audit/gates/` (23 게이트), `scripts/audit/commercial_readiness.py v2`, `/commercial-engine` slash 커맨드
- **에이전트 5-role**: ce-planner, ce-artisan, ce-scribe, ce-executor, ce-reviewer
- **Artifacts 스키마**: `artifacts/{T1,T2,T3}/{gate}/{module}/<evidence>`
- **베이스라인 score**: 13/23 (gateway PR#82 머지 후)

### 1.2 gateway 14셀 실전 결과

| 상태 | 수 | 셀 |
|------|----|-----|
| PASS | 10 | G1-1, G1-4, G2-1, G2-3, G2-5, G3-3, G3-4, G3-5, G4-1, G4-2, G5-1, G5-2 |
| T1 ✓ / T2 ✗ (PARTIAL) | 4 | G1-2, G1-3, G1-5, G3-1 — **CI artifact 수집 미구현** |
| Spec II.5 이관 | 6 | G2-2, G2-4, G4-3, G4-4, G4-5, G5-3 |

※ "PARTIAL 4셀"은 T1 로직은 통과했으나 T2 CI artifact(예: `artifacts/T2/G1-2/gateway/run-*.json`)가 수집되지 않음. Spec III는 이 실패 패턴을 반드시 차단한다(§4.3 참조).

### 1.3 accounting · hr 출발선

정본은 **ADR-0019 (accounting-bounds)** · **ADR-0020 (hr-bounds)** 이며, 본 표는 두 ADR 의 실측 수치를 인용한다. 수치 주석은 `rg` · `ls | wc -l` 실측 근거를 같이 표기한다.

| 지표 | Accounting (ADR-0019 정본) | HR (ADR-0020 정본) |
|------|---------------------------|--------------------|
| 모델 파일 | 56 (`ls oneerp_accounting_app/models/*.py \| wc -l = 56`) | 39 (`ls oneerp_hr_app/models/*.py` 실측) |
| `EntityMeta` 등록 엔티티 | 47 (`grep -c "EntityMeta(" entities.py = 47`) — ADR-0019 §Appendix | 39 — ADR-0020 §D1 "47 건" 주장은 모델 총수 기준이며 EntityMeta 등록은 실측 39 건으로 본 표에서는 EntityMeta 실등록만 집계 |
| 커스텀 라우터 파일 | 11 (ADR-0019: accounting_periods 등 11 개) | 8 (ADR-0020 §D2: employees/employee_transfers/attendances/departments/designations/leave_types/leave_applications/leave_balances) |
| 엔드포인트 총수 | 70 (`grep -c "^@router" routes/*.py = 70`) — ADR-0019 정본 | 참고: 실측 57 (커스텀 라우터 기준) |
| 도메인 서비스 | 22 (ADR-0019 Appendix B §Services, `__init__.py` 제외 실측 22) | 11 (ADR-0020 §D1 "15" 는 하위 util 포함, 본 표는 도메인 서비스 11 기준) |
| 단위 테스트 파일 | 44 (`ls tests/unit/test_*.py \| wc -l = 44`) | 34 (ADR-0020 §테스트 154 케이스 / 34 테스트 파일 기준) |
| 이벤트 체인 (출발선) | ✅ `events/handlers.py` (ADR-0019 §증거) | ❌ 부재 → 이후 ✅ 전환 (Wave C-2 선행 PR 후) |
| config.py (출발선) | ✅ `AccountingSettings` | ❌ 부재 → ✅ 전환 (Wave C-2 선행 PR 후) |
| 게이트 증거 | G1-2/3/5 · OPA · ExternalSecret · Playwright 없음 | 동일 누락 |

**난이도 비대칭**: accounting 는 gateway 템플릿 수평 이식만으로 대부분 완성 가능. hr 은 events/config 선행 정합(Wave C-2) 후 템플릿 이식(2단계). 본 표의 "이벤트 체인 / config.py" 열은 **출발선**이며, Spec III 종료 시점에는 hr 도 ✅ 로 전환된다.

<!-- 감사 보고 DOC-AUDIT C1 해소: 2026-04-22 — ADR-0019/0020 정본 수치 인용 + rg 실측 대조 + hr 이벤트/config ❌→✅ 전환 이력 명시 -->

### 1.4 품질 베이스라인 — ruff 73 errors

| 규칙 | 수 | 처리 |
|------|----|------|
| TC003 (typing import) | 29 | unsafe-fix 또는 TYPE_CHECKING 블록화 |
| ERA001 (commented code) | 12 | 수동 제거 (의도 확인) |
| FBT001/002 (bool positional) | 6 | keyword-only 전환 |
| A002 (builtin shadow) | 4 | 리네임 |
| PERF401, RUF001/002/003, S* | 22 | unsafe-fix 또는 per-file-ignore |

자동수정(safe+unsafe) 33 · 설정 교정 12~15 · 순수 수동 ~25.

## 2. 의존그래프 (트랙 간 · 트랙 내)

### 2.1 트랙 간 의존

```
[품질 게이트 W1]
     │  baseline ≤ 30 확정 · ratchet CI on
     ├──────────────────────────┐
     ▼                          ▼
[Spec II.5 W2: staging 인프라]   [Spec III W2: accounting L0 11셀]
     │  staging NS up            │  artifact 수집 + ce-executor T2
     ▼                          ▼
[Spec II.5 W3: T3 6셀]          [Spec III W3: hr 선행 정합 + hr L0]
     │                          │
     └──────────┬───────────────┘
                ▼
         [Spec III W4: L1 + 품질 마감]
```

### 2.2 하드 의존 (위반 시 진행 불가)

- **H1**: Spec III 착수 조건 = ruff baseline ≤ 40 **AND** ratchet CI 설치됨
- **H2**: Spec II.5 Phase 2(T3 6셀) 조건 = staging NS 배포 완료 **AND** ExternalSecret staging 경로 바인딩 확인
- **H3**: Spec III hr L0 조건 = hr events/config 정합 PR 머지됨
- **H4**: Wave D 조건 = accounting·hr L0 완료 **AND** Spec II.5 T3 6셀 중 최소 4셀 PASS

### 2.3 소프트 의존 (가속 조건)

- **S1**: 품질 게이트 unsafe-fix 적용 시 Spec III 신규 코드가 baseline 상속 — Spec III 신규 파일은 ruff 0 유지 강제
- **S2**: staging Grafana 대시보드가 gateway 외 모듈을 수용하면, Spec III의 G4-1 증거를 staging에서 수집 가능 (병렬 가속)

## 3. Wave · Phase 설계

### 3.1 Wave A (1주) — 품질 게이트 1차

| 셀 | 담당 | 산출물 | 완료 조건 |
|----|------|-------|----------|
| QA-1 | ce-artisan | ruff --fix (safe 1) | error count -1 |
| QA-2 | ce-artisan | ruff --fix --unsafe-fixes (32) | diff 리뷰 · error count -32 |
| QA-3 | ce-artisan | pyproject.toml per-file-ignores 보강 | 12~15 제거 |
| QA-4 | ce-artisan + ce-executor | ratchet CI 스텝 추가 (`.github/workflows/ruff-ratchet.yml`) | PR에서 count 증가 시 fail |
| QA-5 | ce-reviewer | baseline ≤ 30 확정 · ADR 박제 | ADR-0017 커밋 |

### 3.2 Wave B (2주, 병렬)

**B-1 (Spec II.5 Phase 1)** — ce-planner dispatch:

| 셀 | 산출물 | 완료 조건 |
|----|-------|----------|
| STG-1 | `deploy/staging/namespace.yaml` · quota · RBAC | `kubectl get ns staging` |
| STG-2 | `deploy/staging/kustomization.yaml` (overlay) | `kustomize build deploy/staging` |
| STG-3 | `deploy/staging/externalsecrets.yaml` + `kv/staging/*` 경로 | ESO sync 성공 |
| STG-4 | staging용 Grafana datasource · Prometheus retention 7d | 대시보드 로드 확인 |
| STG-5 | `scripts/staging/seed-{tenants,auth,monitoring}.py` | seed 후 smoke test |

**B-2 (Spec III Phase 1)** — accounting L0 11셀:

- gateway Spec II L0 11셀 템플릿을 `module=accounting`으로 재실행
- **추가 구현**: `scripts/ci/collect-t2-artifacts.py` — GitHub Actions artifact 다운로드 → `artifacts/T2/G*/accounting/`에 배치 (Spec II 회귀 차단)
- 셀: G1-1, G1-2, G1-3, G1-4, G2-1, G2-3, G2-5, G3-1, G3-4, G3-5, G5-1

### 3.3 Wave C (2주, 병렬)

**C-1 (Spec II.5 Phase 2)** — T3 6셀 gateway:

| Gate | 도구 | Staging 의존 |
|------|------|-------------|
| G2-2 부하 | k6 (self-hosted) | staging gateway pod |
| G2-4 카오스 | chaoskube | staging NS |
| G4-3 백업 | pg_dump + Velero | staging PostgreSQL |
| G4-4 롤백 | ArgoCD rollback | staging Deployment |
| G4-5 on-call | 알림 → PagerDuty sandbox | staging Prometheus |
| G5-3 UAT | 수동 시나리오 로그 | staging Keycloak + 테스트 사용자 |

**C-2 (Spec III Phase 2)** — hr 선행 + L0:

- 선행 PR: `services/hr/hr/oneerp_hr_app/config.py` + `events/` 추가 (gateway/accounting 패턴 이식)
- hr L0 11셀: accounting과 동일한 11셀

### 3.4 Wave D (1주)

- accounting L1: G1-5 Playwright, G3-2 ExternalSecret, G3-3 OPA rego
- hr L1: 동일 3셀
- 품질 게이트 최종: baseline → 0 (또는 합의된 floor) · 완료 ADR-0018
- 종합 score 집계: 목표 ≥ 19/23

## 4. 5-Role 에이전트 배치

| Wave | ce-planner | ce-artisan | ce-scribe | ce-executor | ce-reviewer |
|------|-----------|-----------|-----------|-------------|-------------|
| A | baseline 측정 · ratchet 계획 | ruff fix | ADR-0017 | ratchet CI | baseline 승인 |
| B-1 | staging 의존그래프 | k8s manifest | staging runbook | kubectl apply · ESO 검증 | staging smoke |
| B-2 | accounting L0 wave | 셀별 코드/테스트 | 매뉴얼·튜토리얼 확장 | **T2 artifact 수집(신규)** · 증거 저장 | 셀별 PASS/FAIL |
| C-1 | T3 6셀 wave | k6/chaos 스크립트 | 드릴 문서 (G4-3/4/5) | 드릴 실행 · artifact | MTTR/RTO 검증 |
| C-2 | hr 정합 → L0 | events/config + 셀 | hr 매뉴얼 보강 | T2 artifact | hr 셀 PASS/FAIL |
| D | L1 · 마감 wave | Playwright/OPA/ES | 완료 ADR-0018 | 최종 리포트 | 23/23 score 확인 |

## 4.3 Spec II 회귀 차단: T2 artifact 수집 의무화

Spec II의 PARTIAL 4셀은 `scripts/engine/wave_planner.py`와 각 gate 함수가 `artifacts/T2/G*/gateway/run-*.json`을 기대하지만 수집 파이프라인이 없어 발생. 본 설계는 다음을 Wave B-2 첫 커밋으로 강제한다:

- `scripts/ci/collect-t2-artifacts.py` — GitHub Actions API (`actions/runs/{id}/artifacts`) 호출, tarball 추출
- CI workflow 모든 게이트 관련 job에 `actions/upload-artifact@v4` 스텝 통일
- `scripts/audit/gates/g*_*.py`의 `artifact_glob["T2"]` 패턴과 1:1 매핑 검증
- 테스트: `tests/unit/test_collect_t2_artifacts.py` 신규

이 조치 없이 Spec III를 시작하면 Spec II와 동일한 10/14 천장에 재부딪힌다.

## 5. 완료 조건 (2겹)

### 5.1 C1 — 셀 단위

각 셀은 Spec I 정의의 `_validate_evidence()` 공용 검증을 통과해야 PASS. 공식:

```
PASS = (file exists) AND (line ≥ threshold) AND (frontmatter valid) AND (tier tag in {T1,T2,T3}) AND (timestamp ≤ 30d)
```

### 5.2 C2 — 트랙 단위

- **Spec III 완료**: accounting 14/14 (T1+T2) AND hr 12+/14 (T1+T2) AND 종합 score ≥ 17/23
- **Spec II.5 완료**: gateway T3 6/6 AND staging up/green AND 종합 score ≥ 19/23
- **품질 게이트 완료**: ruff baseline ≤ floor AND ratchet CI 3개 PR 연속 passing AND ADR-0017/0018 박제

### 5.3 최종 (본 설계의 Exit)

score **19/23 이상** AND 3 ADR 박제 AND 6주 경과 이내. 미달 시 연장 Wave E를 주 단위로 이어감.

## 6. 위험 · 완화

| ID | 위험 | 확률 | 영향 | 완화 |
|----|------|-----|------|------|
| R1 | unsafe-fix가 의미 있는 주석을 제거 | 중 | 중 | diff 리뷰 의무 · ERA001은 수동 |
| R2 | staging 시크릿이 prod 경로 오염 | 저 | 상 | `kv/staging/` vs `kv/services/` 명시 분리 · SecretStore validation |
| R3 | hr 선행 정합이 2주 초과 | 중 | 중 | Wave C를 hr 전용으로 3주 확장 허용 · accounting Wave D 1주 앞당김 |
| R4 | T3 드릴이 staging 리소스 파괴 | 저 | 상 | staging-only egress · ArgoCD prod 권한 제거 · nodeSelector 격리 |
| R5 | 6 worktree 병렬로 리뷰 병목 | 상 | 중 | 동시 셀 상한 6 · ce-reviewer 1인당 최대 3셀/일 |
| R6 | ratchet CI가 flaky (신규 규칙 업데이트) | 중 | 저 | ruff 버전 고정 · bump PR은 baseline 재측정 허용 리베이스 |

## 7. 비가역·과금·시크릿 확인 게이트

다음 액션은 사용자 확인 후에만 실행 (CLAUDE.md v2.3 하네스 자율 엔지니어링 §"여전히 사용자 확인이 필요한 영역"):

- 프로덕션 시크릿·openbao 키 회전
- prod 이미지 태그 삭제 · 네임스페이스 제거
- staging 외 클라우드 리소스 생성 (과금)
- 메인 브랜치 force push · published 커밋 amend

자가수정 허용 범위(빌드 설정 · 테스트 인프라 · staging tuning · 게이트 강화 CI)는 CLAUDE.md v2.3 §"자가수정 허용 범위"를 따른다.

---

# 부록 A — Spec III: accounting + hr 수직 완성

## A.0 범위

23게이트 × 2모듈 = 46 셀. 현실적 목표는 **28 셀 PASS**(accounting 14 + hr 12 + 여유 2). T3 6셀은 Spec II.5 gateway에서 선행 검증되면 accounting/hr T3는 Spec IV로 이관.

## A.1 모듈별 셀 매핑

| Gate | Tier | Accounting | HR | 비고 |
|------|------|-----------|-----|------|
| G1-1 ADR | T1 | 신규 ADR-0019-accounting-bounds | 신규 ADR-0020-hr-bounds | 기존 ADR 확장 가능 |
| G1-2 OpenAPI | T1+T2 | FastAPI → `openapi.yaml` 생성 + schemathesis | 동일 | T2 artifact 수집 필수 |
| G1-3 Integration | T1+T2 | `tests/integration/accounting/` 신설 ≥ 8 tests | 동일 ≥ 6 tests | coverage ≥ 60% |
| G1-4 Unit + Mutation | T1 | 기존 332 tests + mutmut ≥ 50% | 기존 154 tests + mutmut ≥ 50% | accounting 우위 |
| G1-5 Playwright | T1+T2 | UI 시나리오 ≥ 3 (회계기간·저널·예산) | 직원·부서·직위 ≥ 3 | headless CI |
| G2-1 SLO | T2 | staging Prometheus 30d 또는 시뮬 | 동일 | partial 허용 |
| G2-3 Perf regression | T1 | k6 smoke 로컬 · p95 기준선 | 동일 | |
| G2-5 i18n | T1 | ko/en 커버리지 ≥ 90% | 동일 | |
| G3-1 AuthN 7종 | T1+T2 | 기존 테스트 활용 + 신규 | 동일 | |
| G3-2 ExternalSecret | T2 | `deploy/secrets/accounting/externalsecret.yaml` + rotate | 동일 | staging 경로 |
| G3-3 OPA RBAC | T1 | `policies/accounting/routes.rego` ≥ 6 tests | 동일 | |
| G3-4 Audit emit | T1 | mutation ≥ 10 | 동일 | |
| G3-5 Dep audit | T1 | CVE 0 | 동일 | |
| G4-1 Alert rules | T2 | `deploy/monitoring/alerts/accounting.yaml` ≥ 5 | 동일 | |
| G4-2 Runbook | T1 | `docs/ops/runbooks/accounting.md` ≥ 300L | 동일 | |
| G5-1 Manual | T1+T2 | `docs/manual/accounting.md` ≥ 400L | `docs/manual/hr.md` 보강 | |
| G5-2 Tutorial | T1+T2 | `docs/tutorial/accounting-flow.md` ≥ 400L | 동일 | |

## A.2 hr 선행 정합 (Wave C-2 첫 커밋)

```
services/hr/hr/oneerp_hr_app/
├── config.py          ← 신규: HRSettings(CoreSettings) — LDAP/SCIM/급여연동 설정
├── events/
│   ├── __init__.py    ← 신규: event_registry 초기화
│   └── handlers.py    ← 신규: 직원입사/퇴사/인사이동 핸들러 7종
```

검증: `uv run --package oneerp-hr --directory services/hr/hr uvicorn app.main:app` 기동 후 `/events` 엔드포인트에 핸들러 로드 확인.

## A.3 템플릿 재사용 지점 (Spec II에서 추출)

- `scripts/audit/gates/__init__.py` `_MODULE_CLUSTER`에 `"accounting": "finance/accounting"`, `"hr": "hr/hr"` 항목 **이미 존재** (정찰 결과)
- `scripts/engine/wave_planner.py::plan_wave(modules=["accounting","hr"], exclude_tiers=["T3"])`로 즉시 호출 가능
- 각 gate 함수는 module 파라미터화되어 있어 본체 수정 불필요

## A.4 산출물 디렉토리

```
artifacts/T1/G{1-5}-{1-5}/{accounting,hr}/<evidence>
artifacts/T2/G{1-5}-{1-5}/{accounting,hr}/run-*.json
docs/ops/runbooks/{accounting,hr}.md
docs/manual/{accounting,hr}.md
docs/tutorial/{accounting,hr}-flow.md
deploy/secrets/{accounting,hr}/externalsecret.yaml
policies/{accounting,hr}/routes.rego
tests/integration/{accounting,hr}/
tests/playwright/ui/{accounting,hr}/
```

## A.5 Spec III 완료 판정

- accounting: 14/14 T1+T2 PASS, T3는 Spec IV 이관
- hr: 12/14 T1+T2 PASS (G1-5 hr UI 미성숙 가능 — floor 12)
- 종합: score **≥ 17/23**

---

# 부록 B — Spec II.5: staging 환경 + gateway T3 6셀

## B.0 범위

1. staging k8s 네임스페이스 격리 · 시크릿 체인 · 관측성
2. gateway 모듈의 T3 6셀 증거 수집
3. accounting/hr T3 준비는 Spec IV (본 설계 범위 외)

## B.1 6 T3 셀 정의

| Gate | 이름 | 도구 | 증거 파일 |
|------|------|------|----------|
| G2-2 | 부하 테스트 | k6 self-hosted | `artifacts/T3/G2-2/gateway/k6-<ts>.csv` + p95/p99 요약 |
| G2-4 | 카오스 | chaoskube | `artifacts/T3/G2-4/gateway/chaos-<ts>.log` + MTTR |
| G4-3 | 백업·복구 | pg_dump + Velero | `docs/ops/drills/G4-3/<date>-gateway.md` + `artifacts/T3/G4-3/gateway/restore-<ts>.log` |
| G4-4 | 롤백 드릴 | ArgoCD rollback | `docs/ops/drills/G4-4/<date>-gateway.md` + `artifacts/T3/G4-4/gateway/rollback-<ts>.log` |
| G4-5 | on-call 드릴 | Prometheus → PagerDuty sandbox | `docs/ops/drills/G4-5/<date>-gateway.md` + ack 타임스탬프 |
| G5-3 | UAT | 수동 시나리오 (3 페르소나) | `docs/governance/commercial/gateway.md` ≥ 200L + 승인자 frontmatter |

## B.2 staging 최소 스펙 (MVD)

1. **기반** — k8s NS `staging` · ResourceQuota · ExternalSecrets Operator
2. **앱** — OneERP 컨테이너 (docker buildx, tag `staging-<sha>`) · PostgreSQL · FerretDB · Redis · NATS · Keycloak
3. **드릴 인프라** — k6 (ephemeral pod), chaoskube, Velero, ArgoCD rollback SA
4. **증거** — `artifacts/T3/` 트리 + CI upload step

## B.3 인프라 신설 (Wave B-1)

| 파일 | 목적 |
|------|------|
| `deploy/staging/namespace.yaml` | NS + quota + RBAC |
| `deploy/staging/kustomization.yaml` | overlay (replicas/image/probes) |
| `deploy/staging/externalsecrets.yaml` | `kv/staging/*` 바인딩 |
| `deploy/staging/monitoring-overlay.yaml` | Prometheus retention 7d / Grafana staging DS |
| `scripts/staging/seed-tenants.py` | 3 테넌트 + GL 계정 |
| `scripts/staging/seed-auth.py` | Keycloak 사용자 + OAuth |
| `scripts/staging/seed-monitoring.py` | 30d 메트릭 시뮬 |
| `.github/workflows/staging-deploy.yml` | 수동 trigger + buildx |
| `.github/workflows/load-test.yml` | k6 (G2-2) |
| `.github/workflows/chaos-test.yml` | chaoskube (G2-4) |
| `.github/workflows/backup-drill.yml` | G4-3 |
| `.github/workflows/rollback-drill.yml` | G4-4 |

## B.4 시크릿 분리 규약

```
kv/services/<module>/*   ← prod (기존, 건드리지 않음)
kv/staging/<module>/*    ← staging 전용 (신규, 읽기전용 SA)
```

`scripts/secrets/rotate-gateway.sh`를 `rotate_secret(module, tier)` 함수화하여 tier=staging은 read-only 경로만 회전.

## B.5 비가역 가드

- staging NS의 `kubectl delete` 류는 Makefile target으로만 노출 (`make staging-teardown`)
- prod ArgoCD app 권한은 staging SA에서 명시적 제거 (`role: staging-reader`)
- Velero schedule은 staging NS만 대상 (label selector)

## B.6 Spec II.5 완료 판정

- staging NS up/green 30분 이상 지속 관측 (smoke)
- T3 6셀 모두 PASS (또는 G2-1 SLO는 30일 시뮬 허용)
- 종합 score ≥ 19/23

---

# 부록 C — 품질 게이트 baseline 하향 + ratchet

## C.0 목표

- 현재: ruff 73 errors (세션 메모리 67에서 +6 → **증가 중**)
- Wave A 종료: ≤ 30
- Wave D 종료: floor 합의값 (0 또는 5 이내 — §C.3)
- 영구: CI ratchet으로 count 증가 방향 차단

## C.1 처리 분류 (73건)

| 분류 | 수 | 조치 |
|------|----|------|
| safe auto-fix | 1 | `uv run ruff check . --fix` |
| unsafe auto-fix | 32 | `uv run ruff check . --fix --unsafe-fixes` + diff 리뷰 |
| 설정 교정 (per-file-ignores) | 12~15 | tests/security에 `S105,S607`, tests/unit에 `ERA001` 등 |
| 수동 리팩터 | ~25 | FBT001/002(6), A002(4), RUF001~003(7), ERA001 의미 있는 주석, S/SLF/PIE 등 |

## C.2 처리 순서 (Wave A)

1. `pyproject.toml` per-file-ignores 보강 (30분) → 12~15 감소
2. `ruff check --fix` (safe) → 1 감소
3. `ruff check --fix --unsafe-fixes` → 32 감소 (diff 검토 1~2시간)
4. 수동 리팩터 ~25개: FBT는 keyword-only, A002는 리네임, RUF001~003은 문자 교체
5. baseline 확정 → ADR-0017 박제

## C.3 ratchet CI

`.github/workflows/ruff-ratchet.yml`:

```yaml
name: ruff-ratchet
on: [pull_request]
jobs:
  ratchet:
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Base count
        id: base
        run: |
          git fetch origin main
          git checkout origin/main -- .
          echo "count=$(uv run ruff check . 2>&1 | tail -1 | grep -oE '[0-9]+' | head -1)" >> $GITHUB_OUTPUT
      - name: PR count
        id: pr
        run: |
          git checkout -
          echo "count=$(uv run ruff check . 2>&1 | tail -1 | grep -oE '[0-9]+' | head -1)" >> $GITHUB_OUTPUT
      - name: Enforce
        run: |
          if [ "${{ steps.pr.outputs.count }}" -gt "${{ steps.base.outputs.count }}" ]; then
            echo "ruff error count increased: ${{ steps.base.outputs.count }} → ${{ steps.pr.outputs.count }}"
            exit 1
          fi
```

예외: ruff 버전 업그레이드 PR은 `[ratchet-bump]` 라벨로 스킵 허용.

## C.4 floor 합의

Wave D 마감 시 순수 수동 케이스가 남아 있으면 다음 중 선택:

- **option 0**: 전수 수정 — 시간 소요 크나 baseline 0 달성
- **option F (floor)**: 합리화 된 수동 케이스 N개는 `noqa` 주석으로 고정 · ADR-0018에 근거 박제 · ratchet은 "floor + 0" 유지

권장 **option F, N ≤ 5**. 예: `tests/unit/test_commercial_readiness_total_completion.py::S607`은 subprocess 테스트 의도이므로 정당.

## C.5 완료 판정

- baseline ≤ floor (Wave A ≤ 30, Wave D ≤ 5)
- ratchet CI 연속 3 PR passing
- ADR-0017 (Wave A), ADR-0018 (Wave D) 박제

---

## 부록 Z — 참조

- **선행**:
  - `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md` (Spec I)
  - `docs/superpowers/specs/2026-04-22-commercial-grade-v2-spec2-gateway-design.md` (Spec II)
- **구현 플랜 (Spec II)**:
  - `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md` (2857L)
  - `docs/superpowers/plans/2026-04-22-commercial-grade-v2-spec2-gateway.md` (643L)
- **엔진 모듈**: `scripts/engine/`, `scripts/audit/gates/`, `scripts/audit/commercial_readiness.py`
- **Slash 커맨드**: `/commercial-engine` (8 subcommand)
- **관련 ADR**: 0011 (코드 클러스터), 0014 (runtime plane), 0016 (Ralph-Loop 폐기 — 2026-04-22 박제)

---

<!-- v1.0 · 2026-04-22 · 통합 설계 (단일 본문 + 3 부록 / 순서 B) -->
