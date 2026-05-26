# Spec II · gateway 14 셀 Commercial Grade v2 실전 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spec I 에서 만든 `/commercial-engine wave` 를 **첫 실전 적용** 하여 gateway 14 셀(T1+T2) 을 commercial-ready 수준까지 PASS 시키고 동시에 엔진의 실전 작동을 검증한다.

**Architecture:** ce-planner 싱글톤이 14 셀을 L0(11 독립) + L1(3 의존) 레이어로 나눠 artisan/scribe/executor 를 병렬 dispatch. ce-reviewer 가 교차 검증·20% replay. 기존 v1 자산 보강 우선. T3 6 셀은 Spec II.5 이관.

**Tech Stack:**
- Python 3.14 · uv workspace · pytest · pytest-playwright · pytest-bdd · ruff · ty
- FastAPI `app.openapi()` → yaml · schemathesis · OPA Rego · mutmut
- ExternalSecrets Operator (ESO) · Grafana JSON · Prometheus
- Claude Code: `/commercial-engine wave` · Task tool

**Spec Reference:** `docs/superpowers/specs/2026-04-22-commercial-grade-v2-spec2-gateway-design.md`

---

## 사전 조건

- main 브랜치에 Spec I 완전 반영 (commit `2edd775b` 이후)
- Spec II 스펙 문서(`16ba1e2f`) 머지 확인
- Working tree: core/web submodule 변경 + `.graphify_*` 는 pre-existing (무시)
- gateway 현재 score: 3/23 (G1-1 · G1-4 · G4-2 PASS)

```bash
git status --short
uv run pytest tests/unit/engine/ -q                     # 24/24 pass 필수
uv run python3 -m scripts.audit.commercial_readiness \
    --module gateway --format text                      # score 3 확인
```

---

## Task 1 — 준비 (브랜치 · 사전 점검)

**Files:**
- (없음 — 환경 검증만)

- [ ] **Step 1.1: 브랜치 생성**

```bash
git checkout main
git pull --ff-only origin main 2>/dev/null || git pull origin main
git checkout -b feat/commercial-grade-v2-spec2-gateway
git branch --show-current
```
Expected: `feat/commercial-grade-v2-spec2-gateway`

- [ ] **Step 1.2: 엔진 smoke 테스트**

```bash
uv run pytest tests/unit/engine/ -q
uv run ruff check scripts/engine/ scripts/audit/gates/ scripts/audit/commercial_readiness.py
uv run python3 -c "from scripts.audit.commercial_readiness import evaluate_module; r = evaluate_module('gateway'); print(f'score={r[\"score\"]} label={r[\"label\"]}')"
```
Expected:
- 24/24 passed
- All checks passed!
- `score=3 label=none`

- [ ] **Step 1.3: Staging 미가용 확인 · 경계 재확인**

```bash
# staging 네임스페이스 접근 실패 예상 (로컬 kubeconfig 에 staging context 없음)
kubectl config get-contexts 2>/dev/null | grep -i staging || echo "staging context 없음 (예상대로)"
# Prometheus 접근 불가 예상
curl -sf http://prometheus.internal/-/ready 2>&1 | head -3 || echo "Prometheus 없음 (예상대로)"
```
Expected: 둘 다 부재 — T3 6 셀은 Spec II.5, staging 의존 T2 셀(G2-1 30일 데이터, G3-2 rotation, G4-1 fired 이력) 은 partial/fail 예상.

---

## Task 2 — `wave_planner` 에 선행조건 지원 추가

**Files:**
- Modify: `scripts/engine/wave_planner.py`
- Modify: `tests/unit/engine/test_wave_planner.py`

- [ ] **Step 2.1: 실패 테스트 작성**

`tests/unit/engine/test_wave_planner.py` 파일 맨 아래에 추가:

```python
def test_plan_wave_excludes_cells_with_unmet_dependencies() -> None:
    """의존 대상이 pass 가 아니면 해당 셀은 제외."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-2", "status": "not_implemented"},
                    {"id": "G1-5", "status": "not_implemented"},
                    {"id": "G3-1", "status": "not_implemented"},
                    {"id": "G3-2", "status": "not_implemented"},
                ],
            }
        ]
    }
    plan = plan_wave(
        status,
        max_cells=10,
        modules=["gateway"],
        dependencies={"G1-5": ["G1-2"], "G3-2": ["G3-1"]},
    )
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ("gateway", "G1-5") not in ids  # G1-2 미충족
    assert ("gateway", "G3-2") not in ids  # G3-1 미충족
    assert ("gateway", "G1-2") in ids       # 의존 없음
    assert ("gateway", "G3-1") in ids       # 의존 없음


def test_plan_wave_includes_cell_when_dependency_passed() -> None:
    """의존 대상이 pass 면 해당 셀 포함."""
    status = {
        "reports": [
            {
                "module": "gateway",
                "gates": [
                    {"id": "G1-2", "status": "pass"},
                    {"id": "G1-5", "status": "not_implemented"},
                ],
            }
        ]
    }
    plan = plan_wave(
        status,
        max_cells=10,
        modules=["gateway"],
        dependencies={"G1-5": ["G1-2"]},
    )
    ids = {(c["module"], c["gate"]) for c in plan["targets"]}
    assert ("gateway", "G1-5") in ids
```

- [ ] **Step 2.2: 테스트 실행 · 실패 확인**

```bash
uv run pytest tests/unit/engine/test_wave_planner.py -v 2>&1 | tail -10
```
Expected: 2 failures (`TypeError: unexpected keyword 'dependencies'` 또는 유사).

- [ ] **Step 2.3: `plan_wave` 함수 확장**

`scripts/engine/wave_planner.py` 의 `plan_wave` 시그니처와 본문을 다음으로 교체:

```python
def plan_wave(
    status: dict,
    *,
    max_cells: int = 10,
    modules: list[str] | None = None,
    dependencies: dict[str, list[str]] | None = None,
) -> dict:
    """상태 JSON 에서 FAIL/NOT_IMPLEMENTED 셀을 영역·번호·모듈 순으로 정렬해 선택.

    영역 순위: G1 < G3 < G4 < G5 < G2 (스펙 §9 규약).
    dependencies: 특정 gate 가 다른 gate 의 PASS 를 선행 요구. 미충족 시 제외.
    """
    deps = dependencies or {}

    # 모듈별 PASS 셀 집합 구축 (의존 체크용)
    passed: dict[str, set[str]] = {}
    for report in status.get("reports", []):
        module = report["module"]
        passed[module] = {g["id"] for g in report["gates"] if g["status"] == "pass"}

    candidates: list[dict[str, str]] = []
    for report in status.get("reports", []):
        module = report["module"]
        if modules and module not in modules:
            continue
        for gate in report["gates"]:
            if gate["status"] not in ("not_implemented", "fail"):
                continue
            required = deps.get(gate["id"], [])
            if required and not all(r in passed.get(module, set()) for r in required):
                continue
            candidates.append({"module": module, "gate": gate["id"]})

    candidates.sort(key=lambda c: (_gate_key(c["gate"]), c["module"]))
    targets = candidates[:max_cells]

    return {
        "wave_id": datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ-w001"),
        "targets": targets,
        "preflight": "green",
        "requires_user_approval": bool(targets),
    }
```

- [ ] **Step 2.4: 테스트 통과 확인**

```bash
uv run pytest tests/unit/engine/test_wave_planner.py -v 2>&1 | tail -10
```
Expected: 6/6 passed (기존 4 + 신규 2).

- [ ] **Step 2.5: 린트·커밋**

```bash
uv run ruff format scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py
uv run ruff check scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py
```

```bash
git add scripts/engine/wave_planner.py tests/unit/engine/test_wave_planner.py
git commit -m "$(cat <<'EOF'
feat(engine): wave_planner dependencies 매개변수 추가

plan_wave(..., dependencies={"G1-5": ["G1-2"], ...}) 형식으로
선행 PASS 조건을 받으면 미충족 셀을 자동 제외. L0/L1 레이어 분리를
엔진 내에서 자연스럽게 처리.

단위 테스트 2건 추가 — 의존 미충족 제외 · 의존 충족 포함.

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-spec2-gateway-design.md §2.5

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — Wave 실전 실행 (`/commercial-engine wave --module gateway`)

**Files:**
- 다수 (ce-planner 가 dispatch 하는 artisan/scribe/executor 가 생성·수정)
- 주요 결과 파일:
  - Create: `services/platform/gateway/openapi.yaml`
  - Create: `tests/integration/gateway/test_*.py` (≥3)
  - Create: `tests/security/gateway/test_auth_*.py` (7종)
  - Create: `tests/playwright/ui/gateway/test_*.py` (≥3)
  - Create: `policies/gateway/*.rego` (≥1 + tests)
  - Create: `deploy/secrets/gateway/externalsecret.yaml`
  - Modify: `services/platform/gateway/oneerp_gateway_app/routes/**.py` (audit_hooks 주입)
  - Modify: `docs/infra/ops/slo.md` (gateway 섹션 추가)
  - Create: `docs/api/gateway/examples/*.json` (≥3 쌍)
  - Create: `docs/security/audit-retention-gateway.md`
  - Move/expand: `deploy/monitoring/dashboards/oneerp-gateway.json` → `deploy/monitoring/grafana/gateway-overview.json`
  - Create: `deploy/monitoring/alerts/gateway.yaml`
  - Create: `web/locales/gateway/{ko,en,ja}.json`
  - Expand: `docs/user-manual/gateway.md` (52→≥250)
  - Expand: `docs/tutorials/gateway.md` (61→≥300)

### 실행 워크플로 (사용자가 이 단계를 실제로 돌림)

- [ ] **Step 3.1: `/commercial-engine wave` 호출**

Claude Code 세션에서 실제로 다음 slash command 입력:

```
/commercial-engine wave --module gateway --max 14
```

이 호출 시 ce-planner 가 자동으로:
1. Preflight 11 블로커 스캔
2. `wave_planner.plan_wave(status, max_cells=14, modules=["gateway"], dependencies={"G1-5": ["G1-2"], "G3-2": ["G3-1"], "G3-3": ["G3-1"]})` 호출
3. 14 셀 plan JSON 생성

- [ ] **Step 3.2: 사용자 승인 게이트 1**

ce-planner 가 `AskUserQuestion` 으로 plan 제시. 사용자가 승인 응답 시 L0 dispatch.

Expected plan 내용:
```
Wave ID: 2026-04-22THHMMZ-w001
Targets (L0 11 셀 + L1 3 셀):
  L0 독립 셀:
    - G1-2 OpenAPI (artisan + executor)
    - G1-3 통합 테스트 (artisan + executor)
    - G2-1 SLO (scribe + executor)
    - G2-3 perf 회귀 (executor)
    - G2-5 i18n (scribe + executor)
    - G3-1 authN (artisan + executor)
    - G3-4 감사 (artisan + executor)
    - G3-5 dep audit (executor)
    - G4-1 모니터링 (artisan + scribe)
    - G5-1 매뉴얼 (scribe + artisan + executor)
    - G5-2 튜토리얼 (scribe + executor)
  L1 의존 셀 (L0 완료 후):
    - G1-5 UI (artisan + executor)
    - G3-2 시크릿 (artisan + executor)
    - G3-3 RBAC (artisan + executor)
```

- [ ] **Step 3.3: L0 Batch 1 dispatch (자원 한도 내)**

ce-planner 가 artisan+scribe ≤5, executor ≤8 한도 내에서 병렬 Task 호출:

Batch 1 예상 조합 (7 셀 · 리소스 한계 내):
- ce-artisan × 3: G1-2 · G1-3 · G3-1
- ce-scribe × 2: G5-1 · G5-2
- ce-executor × 여러 (병렬): schemathesis · pytest integration · pytest security · dep_audit · regression · i18n coverage

각 artisan/scribe 는 §7 스펙의 산출물을 TDD 로 생성.

- [ ] **Step 3.4: L0 Batch 2 dispatch**

Batch 1 완료 후 나머지 4 셀:
- ce-artisan × 1: G3-4 (audit_hooks route 주입)
- ce-scribe × 3: G2-1 SLO · G2-5 i18n · G4-1 모니터링

- [ ] **Step 3.5: ce-reviewer 1차 (L0 11 셀)**

ce-planner 가 ce-reviewer dispatch:
- trivial 테스트 차단 확인 (`assert True` 차단)
- 얕은 문서 차단 확인 (min_lines 준수)
- broken cross-link 확인
- 20% replay (2~3 증거 재실행)
- Verdict: APPROVED / PARTIAL / BLOCKED

- [ ] **Step 3.6: 사용자 승인 게이트 2**

ce-planner 가 L0 결과 요약 제시 후 L1 진행 여부 질의:

```
L0 결과: N/11 PASS, M/11 partial, K/11 fail
  G1-2 OpenAPI: PASS (T1 ✓, T2 pending CI)
  G1-3 통합 테스트: PASS (cov XX%)
  G2-1 SLO: partial (T2 staging Prometheus 부재)
  ...

L1 3 셀 (G1-5 UI, G3-2 시크릿, G3-3 RBAC) dispatch 진행?
```

- [ ] **Step 3.7: L1 dispatch**

G1-5 선행 조건(G1-2 PASS) 충족 시만 G1-5 포함. ce-artisan × 3 + ce-executor × 3:
- G1-5 UI (Playwright + axe)
- G3-2 시크릿 (externalsecret.yaml + rotate script)
- G3-3 RBAC (rego + opa test)

- [ ] **Step 3.8: ce-reviewer 2차 (전체 14 셀)**

회귀 감지 — 파일럿 3 셀(G1-1, G1-4, G4-2) 이 PASS 유지되는지 확인. 하락 시 블로커 #9.

- [ ] **Step 3.9: 감사 재실행 · 커밋 2개**

ce-planner 자동 수행:

```bash
uv run python3 -m scripts.audit.commercial_readiness --format json > docs/generated/commercial-status.json
```

Feature 커밋 (여러 파일 통합 1 커밋):
```
feat(gateway): Spec II wave 14 셀 (+N/1081)

gateway × {G1-2, G1-3, G1-5, G2-1, G2-3, G2-5, G3-1, G3-2,
G3-3, G3-4, G3-5, G4-1, G5-1, G5-2} 배치 처리.

- G1-2: FastAPI openapi.yaml + 예시 3쌍 + schemathesis exit 0
- G1-3: tests/integration/gateway/ 3 파일 · cov XX%
- ... (각 게이트 1~2줄)

Evidence-SHA: <sha_list>
Wave-ID: 2026-04-22THHMMZ-w001

Refs: docs/superpowers/specs/2026-04-22-commercial-grade-v2-spec2-gateway-design.md
      artifacts/_meta/<sha>.json

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Progress 커밋:
```
chore(progress): Spec II wave · gateway N/23 (+N/1081)

Wave-ID: 2026-04-22THHMMZ-w001
L0 11 셀 · L1 3 셀 · reviewer verdict APPROVED/PARTIAL

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

- [ ] **Step 3.10: Wave 결과 확인**

```bash
uv run python3 -m scripts.audit.commercial_readiness --module gateway --format json \
  | jq '.reports[0] | {module, label, score, gates: [.gates[] | {id, status}] }'
```
Expected:
- score ≥ 15 (3 파일럿 + 12 이상 신규)
- label `beta` 이상
- 파일럿 3 셀 (G1-1 G1-4 G4-2) 여전히 pass

**실패 경로 분기**:
- 엔진 버그 노출 → Spec II.1 분기 (새 브랜치 `fix/engine-bug-<slug>`), 이 Task 3 pause
- 회귀 감지 → 커밋 보류, 수정 후 재실행
- PARTIAL verdict → 문제 셀만 Spec III 로 이관 허용

---

## Task 4 — 엔진 실전 검증 체크 (9 항목)

**Files:**
- Modify: `docs/governance/adr/0016-commercial-grade-v2-evidence.md` (Post-decision 섹션에 amendment append)

- [ ] **Step 4.1: 9 항목 체크 수행**

다음 9 항목 각각 증거와 함께 확인:

```bash
# 1. 11 블로커 판정
grep -i "preflight\|blocker" artifacts/_meta/index.jsonl | head

# 2. plan_wave 선행조건
cat .planning/engine/waves/*.json 2>/dev/null | jq '.targets[] | {module, gate}' | head

# 3. 병렬 dispatch
grep -c "^" artifacts/_meta/index.jsonl  # evidence 수 많으면 병렬 성공

# 4. 20% replay
# reviewer 로그 확인 (artifacts 안 또는 ce-reviewer 출력)

# 5. AskUserQuestion 2회
# Claude 세션 기록 확인 (사용자 경험)

# 6. 감사 재실행 델타 정확
# Wave 시작 전 score (3) vs 완료 후 (예: 17) 수동 계산 대비

# 7. 회귀 감지
uv run python3 -m scripts.audit.commercial_readiness --module gateway --format json \
  | jq '[.reports[0].gates[] | select(.id == "G1-1" or .id == "G1-4" or .id == "G4-2") | .status] | all(. == "pass")'
# Expected: true

# 8. feature + progress 2 커밋
git log --oneline feat/commercial-grade-v2-spec2-gateway ^main | head

# 9. Evidence-SHA / Wave-ID 필드
git log --format='%B' HEAD~2..HEAD | grep -E "Evidence-SHA|Wave-ID" | head
```

- [ ] **Step 4.2: ADR-0016 Post-decision amendment**

`docs/governance/adr/0016-commercial-grade-v2-evidence.md` 의 끝부분 `## Post-decision` 섹션 아래에 다음과 같은 amendment block 을 append:

```markdown

---

## Amendment · Spec II 실전 검증 결과 (2026-04-22)

Spec I 구현 직후 Spec II 에서 gateway 14 셀에 `/commercial-engine wave` 를 처음 실전 투입. 결과:

### 엔진 검증 결과 (9 항목)
- [x] Preflight 11 블로커 판정: (결과 서술)
- [x] plan_wave 선행조건: dependencies 매개변수 작동 확인
- [x] 병렬 dispatch: artisan+scribe+executor 동시 실행 확인
- [x] 20% replay: (실측 결과)
- [x] AskUserQuestion 2회: (발동 확인)
- [x] 감사 재실행 델타: (수동/자동 계산 대비)
- [x] 회귀 감지: 파일럿 3 셀 PASS 유지
- [x] 2 커밋 규약: feature + progress
- [x] Evidence-SHA / Wave-ID 필드

### 발견된 엔진 이슈 (있다면)
- (예: `ce-scribe 가 v1 매뉴얼 52 라인을 250 라인으로 확장 시 스크린샷 생성 로직 불안정 — 검증 수동 필요`)

### 감사 기준 조정 여부
- (예: `G2-1 SLO 의 T2 staging 요구를 "staging 부재 시 시뮬레이션 허용" 으로 완화 검토`)
- (이번에 조정 없음 — 다음 Spec II.5 에서 재검토)

### 결론
Spec II 목적(엔진 실전 검증) 달성. Spec III 이후 동일 패턴으로 확산 가능.
```

- [ ] **Step 4.3: 엔진 이슈 발견 시 분기 판단**

엔진 버그 발견 시 판별 기준 적용:
- 소규모 (single function 버그/lint) → Task 3 내에서 수정 허용
- 구조적 (dispatch/validator/reviewer 규약) → Spec II.1 필수
  - 이 경우 Task 4 중단 · 새 브랜치 `fix/engine-<slug>` · 별도 PR · 머지 후 Spec II 재개
- 감사 기준 부적절 → ADR-0016 amendment 에 기록 + Spec III 초입 논의

- [ ] **Step 4.4: 커밋**

```bash
git add docs/governance/adr/0016-commercial-grade-v2-evidence.md
git commit -m "$(cat <<'EOF'
docs(adr): ADR-0016 Post-decision · Spec II 실전 검증 결과

/commercial-engine wave 의 첫 실전 가동 결과를 ADR-0016 에 기록.
엔진 검증 9 항목 · 발견 이슈 · 감사 기준 조정 여부.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — 마무리 · PR

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 5.1: PROGRESS.md 갱신**

`PROGRESS.md` 의 `### Wave Log` 테이블에 다음 행 추가:

```markdown
| wave-001 | 2026-04-22T<ts>Z | gateway × 14 셀 (L0 11 + L1 3) | planner/artisan/scribe/executor/reviewer | <feature_sha>, <progress_sha> | +N/1081 | APPROVED/PARTIAL |
```

또한 v2 섹션 헤더의 "현재" 라인 갱신:

```markdown
- 현재: **17/1081 (1.6%)** · gateway 17/23 · label=pre-commercial (예상값, 실제 결과로 교체)
- 최근 갱신: 2026-04-22T<ts>Z (Spec II wave-001 완료)
```

- [ ] **Step 5.2: Progress 커밋**

```bash
git add PROGRESS.md
git commit -m "$(cat <<'EOF'
chore(progress): Spec II wave-001 기록 · gateway N/23 · label=beta+

Wave Log 테이블에 wave-001 행 추가. v2 헤더의 현재 상태 갱신.

Wave-ID: 2026-04-22THHMMZ-w001

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5.3: Push + PR 생성**

```bash
git push -u origin feat/commercial-grade-v2-spec2-gateway
```

```bash
gh pr create --base main \
  --title "feat: Spec II · gateway 14 셀 실전 · pre-commercial/beta 도달" \
  --body "$(cat <<'EOF'
## 요약

Spec I 의 `/commercial-engine wave` 를 첫 실전 적용하여 gateway 14 셀(T1+T2) 처리.
파일럿 3 셀(G1-1/G1-4/G4-2) + Spec II 신규 N 셀 = gateway score N+3/23.

## 배치 결과

### L0 (11 셀, 독립)
- G1-2 OpenAPI, G1-3 통합, G3-1 authN, G3-4 감사, G3-5 dep audit
- G2-1 SLO, G2-3 perf, G2-5 i18n
- G4-1 모니터링, G5-1 매뉴얼, G5-2 튜토리얼

### L1 (3 셀, L0 의존)
- G1-5 UI (← G1-2)
- G3-2 시크릿 (← G3-1)
- G3-3 RBAC (← G3-1)

### 이관된 셀 (Spec II.5)
- G2-2 부하 · G2-4 chaos · G4-3/4/5 드릴 · G5-3 UAT (T3 6 셀 · staging 필요)

## 엔진 실전 검증 (9 항목)
- Preflight 11 블로커
- plan_wave dependencies 매개변수
- 병렬 dispatch · 20% replay · AskUserQuestion 2회
- 감사 델타 · 회귀 감지 · 2 커밋 규약 · Evidence-SHA 필드

상세: `docs/governance/adr/0016-commercial-grade-v2-evidence.md` Post-decision amendment

## 테스트 계획

- [x] `uv run pytest tests/unit/engine/ -q` (26/26 pass, +2 wave_planner)
- [x] `uv run python3 -m scripts.audit.commercial_readiness --module gateway --format text` (score 확인)
- [x] `uv run python3 -m scripts.audit.commercial_readiness --verify-evidence` (20% replay)
- [x] 파일럿 3 셀(G1-1/G1-4/G4-2) 여전히 PASS
- [x] ruff clean · 엔진 버그 0

## 후속

- Spec II.5 — staging 환경 구축 + T3 6 셀
- Spec III — accounting + hr 수직 완성

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 5.4: PR 링크 사용자에게 제공**

사용자에게 PR URL 출력 · 리뷰 요청.

---

## Self-Review

### 1. Spec coverage
- §1~§2 (배경·목표/Non-Goals): 플랜 Goal + Task 1 Step 1.3 ✓
- §3 (원칙 5): 모든 Task 가 이 원칙 준수 — Task 3 가 `/commercial-engine wave` 사용, 승인 2회 ✓
- §4 (스코프 14 게이트): Task 3 Step 3.2 의 plan 에 14 셀 전수 포함 ✓
- §5 (의존 그래프 L0/L1): Task 2 의 `dependencies` 매개변수 + Task 3 Step 3.2 의 plan 구조 ✓
- §6 (자원 배분): Task 3 Step 3.3/3.4/3.7 에서 자원 한도 명시 ✓
- §7 (게이트별 산출물 14개): Task 3 Files 목록에 모든 파일 경로 ✓
- §8 (실전 워크플로): Task 3 Step 3.1~3.10 정확히 대응 ✓
- §9 (실패 복구): Task 3 각 단계의 실패 경로 분기 ✓
- §10 (리스크): Task 3/4 에 분산 반영 ✓
- §11 (Spec II.1 분기): Task 3 실패 경로 + Task 4 Step 4.3 ✓
- §12 (구현 순서 5 Task): 이 플랜 Task 1~5 정확히 ✓
- §13 (엔진 검증 9 항목): Task 4 Step 4.1/4.2 ✓
- §14 (종료 조건 2 겹): Task 3 Step 3.10 + Task 4 Step 4.1 + Task 5 PR body ✓
- §15 (결과물 기대): Task 5 PR body ✓

### 2. Placeholder 스캔
- "TBD"/"TODO" 없음 ✓
- "later"/"implement later" 없음 ✓
- Task 3 Step 3.9 의 커밋 메시지에 `<sha_list>` 플레이스홀더 있지만 **의도적** — 실제 값은 ce-planner 가 실행 시 채움
- Task 5 PR body 의 `N 셀` 표기 역시 실행 결과에 따라 채움

### 3. 타입·이름 일관성
- `plan_wave(dependencies=...)` 이름 Task 2~3 일치 ✓
- `/commercial-engine wave --module gateway --max 14` 인자 이름 일관 ✓
- L0/L1 용어 일관 ✓

### 4. 발견된 틈 (메모)
- Task 3 의 실제 실행은 **사용자가 실제 slash command 를 입력** 해야 함 — 이는 플랜의 한계가 아니라 설계 의도 (자기구동 금지)
- ce-planner 가 dispatch 실패 시 복구 로직의 구체 동작은 Spec I ce-planner 정의에 위임 — 플랜에서 재명시하지 않음
- 엔진 실전 검증 결과는 Task 4 실행 후 실제 값으로 기록 — 플랜은 템플릿만 제공

---

## 실행 선택

**플랜 작성 완료 · `docs/superpowers/plans/2026-04-22-commercial-grade-v2-spec2-gateway.md` 저장.**

### 두 가지 실행 옵션

1. **Subagent-Driven** — 각 Task 를 fresh subagent 에 dispatch, 두 단계 리뷰 (spec + code) 후 진행. Task 3 의 slash command 호출도 subagent 에 위임 가능.

2. **Inline Execution** — 현 세션에서 직접 실행. Task 3 Step 3.1 에서 실제로 `/commercial-engine wave` 호출. 사용자 승인 게이트를 현장에서 수행.

**권장 모드**: 이번 Spec II 는 **Inline Execution 권장**. 이유:
- Task 3 의 `/commercial-engine wave` 는 설계상 **현 세션의 사용자** 가 호출하고 승인해야 함 (승인 게이트 2회)
- Subagent 가 대신 slash command 를 호출하면 승인 게이트가 사용자에게 도달하지 못함 — 엔진의 사용자 개입 원칙 위배
- Task 1/2/4/5 는 인라인으로 수행해도 단순

**어느 방식으로 진행할까요?**
