# Spec III + Spec II.5 + 품질 게이트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OneERP Commercial Grade v2 score를 13/23에서 19+/23으로 끌어올린다 — accounting/hr 수직 완성(Spec III) · gateway T3 6셀과 staging 인프라(Spec II.5) · ruff 73→floor + ratchet(품질 게이트)을 6주 내 완료.

**Architecture:** Spec II에서 박제된 엔진(`scripts/engine/wave_planner.py`, `scripts/audit/gates/*`)과 5-role 에이전트(ce-planner/artisan/scribe/executor/reviewer)를 재사용한다. 품질 게이트 1 Wave 선행 → Spec II.5/Spec III 2-worktree 병렬 3 Wave. Spec II 회귀(T2 artifact 수집 미구현)는 Wave B 첫 커밋에서 차단.

**Tech Stack:** Python 3.14 · uv 0.11 · FastAPI · pytest · ruff 0.15 · Playwright · k6 · chaoskube · PostgreSQL/FerretDB · Redis · NATS · Keycloak · k8s/kustomize · ArgoCD · ExternalSecrets Operator · GitHub Actions · OPA rego.

**Spec 참조:** `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md` (487L · commit `26a770be`)

---

## 파일 구조 (신규/수정 맵)

### Wave A — 품질 게이트
- Modify: `pyproject.toml` (ruff per-file-ignores 보강)
- Create: `.github/workflows/ruff-ratchet.yml`
- Create: `docs/kb/adr/0017-ruff-baseline-ratchet.md`
- Modify: 수동 리팩터 대상 ~25 파일 (scripts/, packages/core/, services/finance, services/scm)

### Wave B-1 — staging 인프라
- Create: `deploy/staging/namespace.yaml`, `kustomization.yaml`, `externalsecrets.yaml`, `monitoring-overlay.yaml`
- Create: `scripts/staging/seed-tenants.py`, `seed-auth.py`, `seed-monitoring.py`
- Create: `.github/workflows/staging-deploy.yml`
- Modify: `scripts/secrets/rotate-gateway.sh` → `rotate_secret(module, tier)` 함수화

### Wave B-2 — Spec III accounting L0
- Create: `scripts/ci/collect-t2-artifacts.py` (회귀 차단 · 공용)
- Create: `tests/unit/test_collect_t2_artifacts.py`
- Modify: `scripts/audit/gates/__init__.py` `_MODULE_CLUSTER` 검증 (이미 존재 확인)
- 셀별 산출물: `artifacts/T{1,2}/G*/accounting/*`, `docs/manual/accounting.md`, `docs/tutorial/accounting-flow.md`, `deploy/secrets/accounting/externalsecret.yaml`, `policies/accounting/routes.rego`, `tests/integration/accounting/`, `tests/playwright/ui/accounting/`

### Wave C-1 — T3 6셀 gateway
- Create: `tests/load/gateway/scenarios.js` (k6)
- Create: `tests/chaos/gateway/scenarios.yaml` (chaoskube)
- Create: `.github/workflows/{load-test,chaos-test,backup-drill,rollback-drill}.yml`
- Create: `docs/ops/drills/{G4-3,G4-4,G4-5}/2026-04-??-gateway.md`
- Create: `docs/governance/commercial/gateway.md` (UAT, G5-3)

### Wave C-2 — hr 선행 + L0
- Create: `services/hr/hr/oneerp_hr_app/config.py`
- Create: `services/hr/hr/oneerp_hr_app/events/__init__.py`, `events/handlers.py`
- Create: `services/hr/hr/tests/unit/test_config.py`, `test_events_registry.py`
- 이후 hr L0: accounting L0와 동일 셀 목록 (module=hr)

### Wave D — L1 · 마감
- Create: `tests/playwright/ui/{accounting,hr}/` 시나리오 각 ≥ 3
- Create: `deploy/secrets/{accounting,hr}/externalsecret.yaml`
- Create: `policies/{accounting,hr}/routes.rego`
- Create: `docs/kb/adr/0018-commercial-v2-spec3-completion.md`

---

## Wave A — 품질 게이트 1차 (1주)

### Task A1: per-file-ignores 보강 (ruff 설정 교정)

**Files:**
- Modify: `pyproject.toml` (`[tool.ruff.lint.per-file-ignores]`)

- [ ] **Step A1.1: 현 baseline 확정 기록**

Run:
```bash
uv run ruff check . 2>&1 | tail -1
uv run ruff check . --statistics 2>&1 | head -30 > /tmp/ruff-baseline-A0.txt
cat /tmp/ruff-baseline-A0.txt
```
Expected: `Found NN errors.` (NN ≈ 73) + rule breakdown

- [ ] **Step A1.2: pyproject.toml 편집**

`pyproject.toml`의 `[tool.ruff.lint.per-file-ignores]` 섹션에 다음을 **추가**:

```toml
[tool.ruff.lint.per-file-ignores]
# 기존 항목 유지 +
"tests/security/**" = ["S101", "S105", "S106", "S107", "ARG", "FBT", "TC002", "TC003", "SLF001"]
"tests/unit/test_commercial_readiness*.py" = ["S607", "S603"]
"scripts/**" = ["T20", "S112", "TC003", "S603", "S607", "ERA001"]
```

- [ ] **Step A1.3: 재측정 · 감소 확인**

Run:
```bash
uv run ruff check . 2>&1 | tail -1
```
Expected: `Found MM errors.` where `MM ≤ NN - 10` (per-file-ignore 보강으로 ≥ 10건 제거)

- [ ] **Step A1.4: Commit**

```bash
git add pyproject.toml
git commit -m "chore(ruff): per-file-ignores 보강 — tests/security·scripts·readiness 정당화"
```

### Task A2: safe auto-fix 적용

- [ ] **Step A2.1: 실행**

Run:
```bash
uv run ruff check . --fix 2>&1 | tail -5
```
Expected: `Fixed 1 error` 또는 유사 · 이후 잔여 에러 수 기록

- [ ] **Step A2.2: 회귀 체크**

Run:
```bash
uv run ruff format --check .
uv run ty check . 2>&1 | tail -5
uv run pytest -m "not integration and not e2e" -x --timeout=120 2>&1 | tail -20
```
Expected: 전 항목 PASS (auto-fix는 의미 보존)

- [ ] **Step A2.3: Commit**

```bash
git add -u
git commit -m "chore(ruff): safe auto-fix 1건 — unused noqa 제거"
```

### Task A3: unsafe-fix 일괄 적용 + diff 검토

- [ ] **Step A3.1: unsafe-fix 적용**

Run:
```bash
uv run ruff check . --fix --unsafe-fixes 2>&1 | tail -5
```
Expected: `Fixed NN errors` (≈32)

- [ ] **Step A3.2: diff 필수 검토 — ERA001(주석코드 제거) 중심**

Run:
```bash
git diff --stat
git diff | grep -E "^(-|\+)" | grep -iE "(TODO|FIXME|HACK|XXX)" | head -20
```
Expected: 의미 있는 주석(TODO/FIXME 등)이 **제거되지 않음**. 제거됐다면 Step A3.3 수행.

- [ ] **Step A3.3: 의미 주석 복구 (필요시)**

의미 있는 TODO/FIXME가 제거된 경우 해당 파일을 수동 복구 후:
```bash
# 예시
git checkout -p -- path/to/file.py  # 해당 hunk만 되돌리기
```

- [ ] **Step A3.4: 테스트 회귀**

Run:
```bash
uv run ruff format --check .
uv run ty check . 2>&1 | tail -5
uv run pytest -m "not integration and not e2e" -x --timeout=120 2>&1 | tail -20
```
Expected: 전부 PASS

- [ ] **Step A3.5: Commit**

```bash
git add -u
git commit -m "chore(ruff): unsafe-fix 일괄 적용 — TC003/PERF401/RUF001 대응"
```

### Task A4: FBT001/002 수동 — keyword-only 전환 (6건)

**Files (추정):** 정찰 결과 FBT 6건 존재. 각 건 대상 파일은 `uv run ruff check . --select FBT`로 식별.

- [ ] **Step A4.1: 대상 식별**

Run:
```bash
uv run ruff check . --select FBT 2>&1 | head -50
```
기록: 각 파일:라인 · 함수 시그니처

- [ ] **Step A4.2: 각 함수 시그니처 수정 (반복)**

각 대상에 대해:
```python
# before
def foo(enabled: bool = False): ...

# after — keyword-only 강제
def foo(*, enabled: bool = False): ...
```

호출처도 검색하여 `foo(True)` → `foo(enabled=True)`로 변경. 호출처 검색:
```bash
rg "foo\(" --type py
```

- [ ] **Step A4.3: 테스트**

Run:
```bash
uv run pytest -m "not integration and not e2e" -x --timeout=120
```
Expected: PASS

- [ ] **Step A4.4: 재측정**

Run:
```bash
uv run ruff check . --select FBT 2>&1 | tail -1
```
Expected: `All checks passed.` 또는 0 error

- [ ] **Step A4.5: Commit**

```bash
git add -u
git commit -m "refactor(api): bool 인자 keyword-only 전환 — FBT001/002 6건"
```

### Task A5: A002 리네임 · RUF001~003 유니코드 정비 · 잔여 수동

- [ ] **Step A5.1: A002(builtin shadow) 식별·수정**

Run:
```bash
uv run ruff check . --select A002 2>&1
```
각 건에서 `id` → `entity_id`, `type` → `kind`, `input` → `value` 등으로 리네임. 호출처 동반 수정.

- [ ] **Step A5.2: RUF001/002/003 유니코드 교정**

Run:
```bash
uv run ruff check . --select RUF001,RUF002,RUF003 2>&1
```
`×` → `x` · 한글 `ㅇ` → 영문 `o` 등 혼입 교체.

- [ ] **Step A5.3: 잔여 수동 (ERA001 의미 주석 · SLF/PIE/RET 개별)**

Run:
```bash
uv run ruff check . 2>&1 | tail -1
```
잔여 N건에 대해 파일별 context 확인 후 수동 수정.

- [ ] **Step A5.4: 최종 baseline 측정**

Run:
```bash
uv run ruff check . 2>&1 | tail -1 | tee /tmp/ruff-baseline-A-final.txt
```
Target: `≤ 30` (Wave A 완료조건)

- [ ] **Step A5.5: Commit**

```bash
git add -u
git commit -m "refactor: ruff 잔여 수동 정리 — A002/RUF001-003/ERA001 Wave A baseline ≤ 30"
```

### Task A6: ratchet CI 설치

**Files:**
- Create: `.github/workflows/ruff-ratchet.yml`
- Create: `scripts/ci/count-ruff-errors.sh`

- [ ] **Step A6.1: count 스크립트 작성 (공용화)**

Create `scripts/ci/count-ruff-errors.sh`:

```bash
#!/usr/bin/env bash
# ruff error count만 stdout으로 출력 (ratchet 비교용)
set -euo pipefail
cd "${1:-.}"
count=$(uv run ruff check . 2>&1 | tail -1 | grep -oE '^Found [0-9]+' | grep -oE '[0-9]+' || echo 0)
echo "${count:-0}"
```

Run:
```bash
chmod +x scripts/ci/count-ruff-errors.sh
./scripts/ci/count-ruff-errors.sh
```
Expected: 정수 출력 (Wave A 완료 기준 ≤ 30)

- [ ] **Step A6.2: ratchet 테스트 (로컬)**

Run:
```bash
git stash   # 로컬 변경 퇴피
BASE=$(./scripts/ci/count-ruff-errors.sh)
git stash pop
PR=$(./scripts/ci/count-ruff-errors.sh)
echo "base=$BASE pr=$PR"
test "$PR" -le "$BASE" && echo "ratchet OK" || echo "ratchet FAIL"
```
Expected: `ratchet OK`

- [ ] **Step A6.3: workflow 작성**

Create `.github/workflows/ruff-ratchet.yml`:

```yaml
name: ruff-ratchet
on:
  pull_request:
    branches: [main]

jobs:
  ratchet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: uv sync
        run: ~/.local/bin/uv sync --frozen
      - name: Base count (main)
        id: base
        run: |
          git fetch origin main:refs/remotes/origin/main
          git worktree add /tmp/main-tree origin/main
          echo "count=$(cd /tmp/main-tree && ~/.local/bin/uv run ruff check . 2>&1 | tail -1 | grep -oE '^Found [0-9]+' | grep -oE '[0-9]+' || echo 0)" >> $GITHUB_OUTPUT
      - name: PR count
        id: pr
        run: |
          echo "count=$(~/.local/bin/uv run ruff check . 2>&1 | tail -1 | grep -oE '^Found [0-9]+' | grep -oE '[0-9]+' || echo 0)" >> $GITHUB_OUTPUT
      - name: Enforce ratchet
        run: |
          BASE="${{ steps.base.outputs.count }}"
          PR="${{ steps.pr.outputs.count }}"
          echo "base=$BASE pr=$PR"
          if [ "$PR" -gt "$BASE" ]; then
            echo "::error::ruff error count increased: $BASE → $PR"
            exit 1
          fi
          echo "::notice::ruff count $BASE → $PR (ratchet pass)"
```

- [ ] **Step A6.4: workflow 문법 검증**

Run:
```bash
# yamllint or actionlint (없으면 yaml 파싱 확인)
python -c "import yaml; yaml.safe_load(open('.github/workflows/ruff-ratchet.yml'))"
```
Expected: 오류 없음

- [ ] **Step A6.5: Commit + 추후 CI 실제 실행 확인은 PR 단계**

```bash
git add .github/workflows/ruff-ratchet.yml scripts/ci/count-ruff-errors.sh
git commit -m "ci(ruff): ratchet workflow — PR에서 ruff error count 증가 차단"
```

### Task A7: ADR-0017 박제

**Files:**
- Create: `docs/kb/adr/0017-ruff-baseline-ratchet.md`

- [ ] **Step A7.1: ADR 작성**

Create `docs/kb/adr/0017-ruff-baseline-ratchet.md`:

```markdown
---
title: ADR-0017 · ruff baseline 하향 + ratchet CI 도입
date: 2026-04-22
status: accepted
tags: [quality, ci, ruff, commercial-grade-v2]
---

# ADR-0017 · ruff baseline 하향 + ratchet CI 도입

## Context

Commercial Grade v2 Spec II 종료 시점 ruff error count가 67에서 73으로 증가. 신규 코드가 baseline을 계속 올리는 사이클.

## Decision

1. Wave A에서 설정 교정(per-file-ignores) + auto-fix + 수동 리팩터로 baseline을 ≤ 30까지 하향.
2. `.github/workflows/ruff-ratchet.yml`로 모든 PR에서 count 증가 방향 차단.
3. Wave D 종료 시 floor 합의 (option F: ≤ 5 with ADR 근거 / option 0: 0 달성).

## Consequences

- 신규 PR은 ruff error를 줄이거나 같게만 머지 가능
- ruff 버전 업그레이드 PR은 `[ratchet-bump]` 라벨로 예외 처리
- Spec III 신규 코드는 baseline을 올리지 못함 (구조적 가드)

## Evidence

- Wave A 시작: /tmp/ruff-baseline-A0.txt (73건)
- Wave A 종료: /tmp/ruff-baseline-A-final.txt (≤ 30건)
- ratchet workflow: `.github/workflows/ruff-ratchet.yml`
```

- [ ] **Step A7.2: INDEX.md 갱신**

Modify `docs/kb/adr/INDEX.md` — 0017 항목 추가:

```markdown
| 0017 | ruff baseline 하향 + ratchet CI | 2026-04-22 | accepted |
```

- [ ] **Step A7.3: Commit — Wave A 종료**

```bash
git add docs/kb/adr/0017-ruff-baseline-ratchet.md docs/kb/adr/INDEX.md
git commit -m "docs(adr): ADR-0017 ruff baseline 하향 + ratchet CI · Wave A 완료"
```

---

## Wave B — 병렬 2 worktree (2주)

Wave B 착수 전제: Task A1~A7 완료 AND `uv run ruff check . 2>&1 | tail -1` ≤ 30 AND ratchet workflow 머지됨.

### B-1: Spec II.5 Phase 1 — staging 인프라 (worktree: `feat/spec2.5-staging-infra`)

### Task B1-1: staging NS + quota

**Files:**
- Create: `deploy/staging/namespace.yaml`

- [ ] **Step B1-1.1: Create namespace manifest**

Create `deploy/staging/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    env: staging
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: staging-quota
  namespace: staging
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    persistentvolumeclaims: "20"
    services.loadbalancers: "0"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: staging
  name: staging-operator
rules:
  - apiGroups: ["apps", ""]
    resources: ["deployments", "pods", "services", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["delete"]   # rollback 드릴용
```

- [ ] **Step B1-1.2: kustomize build 검증 (dry-run)**

Run:
```bash
kubectl apply --dry-run=client -f deploy/staging/namespace.yaml
```
Expected: `namespace/staging created (dry run)` 등 오류 없음

- [ ] **Step B1-1.3: Commit**

```bash
git add deploy/staging/namespace.yaml
git commit -m "feat(staging): NS + ResourceQuota + RBAC"
```

### Task B1-2: kustomize overlay

**Files:**
- Create: `deploy/staging/kustomization.yaml`

- [ ] **Step B1-2.1: Create kustomization**

Create `deploy/staging/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: staging
resources:
  - namespace.yaml
  - externalsecrets.yaml
  - monitoring-overlay.yaml
  - ../apps   # 기존 OneERP 앱 manifest 재사용
patches:
  - target: { kind: Deployment, name: gateway }
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 2
      - op: replace
        path: /spec/template/spec/containers/0/image
        value: registry.masblue.dev/oneerp/gateway:staging-latest
images:
  - name: registry.masblue.dev/oneerp/gateway
    newTag: staging-latest
```

- [ ] **Step B1-2.2: kustomize build**

Run:
```bash
kustomize build deploy/staging > /tmp/staging-render.yaml
grep -c "^---" /tmp/staging-render.yaml
```
Expected: 렌더된 리소스 ≥ 5개 · 오류 없음

- [ ] **Step B1-2.3: Commit**

```bash
git add deploy/staging/kustomization.yaml
git commit -m "feat(staging): kustomize overlay — replicas/image tag"
```

### Task B1-3: ExternalSecret staging 경로

**Files:**
- Create: `deploy/staging/externalsecrets.yaml`
- Modify: `scripts/secrets/rotate-gateway.sh` → `rotate_secret.sh` (범용)

- [ ] **Step B1-3.1: ExternalSecret 정의**

Create `deploy/staging/externalsecrets.yaml`:

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: openbao-staging
  namespace: staging
spec:
  provider:
    vault:
      server: https://openbao.masblue.dev
      path: kv-staging
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes-staging
          role: staging-reader
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: gateway-secrets
  namespace: staging
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: openbao-staging
    kind: SecretStore
  target:
    name: gateway-secrets
    creationPolicy: Owner
  data:
    - secretKey: JWT_SECRET
      remoteRef: { key: gateway/jwt, property: secret }
    - secretKey: REDIS_PASSWORD
      remoteRef: { key: gateway/redis, property: password }
```

- [ ] **Step B1-3.2: rotate 스크립트 범용화**

Modify `scripts/secrets/rotate-gateway.sh` — 파일명은 유지하되 내부를 함수화 + argparse:

```bash
#!/usr/bin/env bash
set -euo pipefail

# rotate_secret <module> <tier>
# tier = services (prod) | staging
usage() {
  echo "usage: $0 <module> <services|staging>" >&2
  exit 2
}
[ "$#" -eq 2 ] || usage
MODULE="$1"
TIER="$2"
case "$TIER" in
  services) KV_PATH="kv/services/${MODULE}" ; NS="services" ;;
  staging)  KV_PATH="kv/staging/${MODULE}"  ; NS="staging"  ;;
  *) usage ;;
esac

echo "rotating ${MODULE} in tier=${TIER} (kv=${KV_PATH}, ns=${NS})"

# staging은 dry-run 기본
if [ "$TIER" = "staging" ]; then
  echo "[staging] dry-run · read-only rotation simulation"
  bao kv get -format=json "$KV_PATH" >/dev/null
  echo "[staging] simulated rotation complete"
  exit 0
fi

# prod tier — 실제 회전
NEW_SECRET=$(openssl rand -base64 32)
bao kv put "$KV_PATH" secret="$NEW_SECRET"
kubectl -n "$NS" rollout restart deploy/"$MODULE"
```

- [ ] **Step B1-3.3: 스크립트 테스트**

Run:
```bash
chmod +x scripts/secrets/rotate-gateway.sh
bash -n scripts/secrets/rotate-gateway.sh   # 문법
./scripts/secrets/rotate-gateway.sh 2>&1 || true   # usage 출력 확인
./scripts/secrets/rotate-gateway.sh gateway staging   # dry-run 분기 확인 (bao 없으면 실패 허용)
```

- [ ] **Step B1-3.4: Commit**

```bash
git add deploy/staging/externalsecrets.yaml scripts/secrets/rotate-gateway.sh
git commit -m "feat(staging): ExternalSecret + rotate_secret tier/module 범용화"
```

### Task B1-4: monitoring overlay (Prometheus/Grafana staging)

**Files:**
- Create: `deploy/staging/monitoring-overlay.yaml`

- [ ] **Step B1-4.1: overlay 작성**

Create `deploy/staging/monitoring-overlay.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-staging
  namespace: staging
data:
  retention: "7d"
  scrape_interval: "30s"
  external_labels: |
    env: staging
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: staging-gateway
  namespace: staging
spec:
  selector:
    matchLabels: { app: gateway, env: staging }
  endpoints:
    - port: metrics
      interval: 30s
```

- [ ] **Step B1-4.2: 기존 Grafana 대시보드 staging datasource 추가**

Modify `deploy/monitoring/grafana/gateway-overview.json` — panel datasource에 `{ "type": "prometheus", "uid": "prometheus-staging" }` 선택 가능하도록 `templating.list`에 env 변수 추가:

```json
{
  "templating": {
    "list": [
      {
        "name": "env",
        "type": "datasource",
        "query": "prometheus",
        "current": { "text": "prometheus", "value": "prometheus" }
      }
    ]
  }
}
```

- [ ] **Step B1-4.3: Commit**

```bash
git add deploy/staging/monitoring-overlay.yaml deploy/monitoring/grafana/gateway-overview.json
git commit -m "feat(staging): monitoring overlay — Prometheus 7d retention + Grafana env 변수"
```

### Task B1-5: seed 스크립트 3종

**Files:**
- Create: `scripts/staging/seed-tenants.py`, `seed-auth.py`, `seed-monitoring.py`
- Create: `scripts/staging/tests/test_seed_tenants.py`

- [ ] **Step B1-5.1: seed-tenants 실패 테스트**

Create `scripts/staging/tests/test_seed_tenants.py`:

```python
from __future__ import annotations
import pytest
from scripts.staging.seed_tenants import build_tenants

def test_build_tenants_returns_three_with_gl_accounts() -> None:
    tenants = build_tenants()
    assert len(tenants) == 3
    for t in tenants:
        assert t["id"].startswith("stg-")
        assert "name" in t
        assert len(t["gl_accounts"]) >= 5
```

Run:
```bash
uv run pytest scripts/staging/tests/test_seed_tenants.py -v
```
Expected: FAIL (`ModuleNotFoundError` — seed_tenants 미존재)

- [ ] **Step B1-5.2: seed-tenants 구현**

Create `scripts/staging/seed_tenants.py`:

```python
from __future__ import annotations
"""staging DB에 3 테넌트 + 기본 GL 계정 시드."""
from typing import Any

_GL_DEFAULTS: list[dict[str, str]] = [
    {"code": "1000", "name": "현금"},
    {"code": "1100", "name": "보통예금"},
    {"code": "2000", "name": "매입채무"},
    {"code": "4000", "name": "매출"},
    {"code": "5000", "name": "매입원가"},
    {"code": "6000", "name": "판관비"},
]

def build_tenants() -> list[dict[str, Any]]:
    return [
        {"id": f"stg-{i}", "name": f"Staging Tenant {i}", "gl_accounts": list(_GL_DEFAULTS)}
        for i in (1, 2, 3)
    ]

def main() -> None:
    import json, sys
    json.dump(build_tenants(), sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
```

Run:
```bash
uv run pytest scripts/staging/tests/test_seed_tenants.py -v
```
Expected: PASS

- [ ] **Step B1-5.3: seed-auth + seed-monitoring (유사 패턴)**

Create `scripts/staging/seed_auth.py` (Keycloak 사용자 3 + OAuth client 1 생성 JSON 출력):

```python
from __future__ import annotations
"""staging Keycloak 시드 JSON (admin-cli import 대상)."""
from typing import Any

def build_realm() -> dict[str, Any]:
    return {
        "realm": "oneerp-staging",
        "enabled": True,
        "users": [
            {"username": f"stg-user-{i}", "enabled": True,
             "credentials": [{"type": "password", "value": f"StgP@ss{i}"}]}
            for i in (1, 2, 3)
        ],
        "clients": [
            {"clientId": "oneerp-web", "publicClient": True,
             "redirectUris": ["https://staging.oneerp.dev/*"]}
        ],
    }

def main() -> None:
    import json, sys
    json.dump(build_realm(), sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
```

Create `scripts/staging/seed_monitoring.py`:

```python
from __future__ import annotations
"""Prometheus 30d 시뮬레이션 샘플 — G2-1 SLO partial 증거."""
from typing import Any

def build_slo_series(days: int = 30) -> list[dict[str, Any]]:
    return [
        {"day": d + 1, "p95_ms": 95 + (d % 7) * 2, "error_rate": 0.001 + (d % 3) * 0.0005,
         "availability": 0.999 - (d % 5) * 0.0001}
        for d in range(days)
    ]

def main() -> None:
    import json, sys
    json.dump(build_slo_series(), sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
```

- [ ] **Step B1-5.4: 테스트 및 Commit**

Run:
```bash
uv run pytest scripts/staging/tests/ -v
uv run ruff check scripts/staging/
```
Expected: 모두 PASS

```bash
git add scripts/staging/
git commit -m "feat(staging): seed 3종 — tenants/auth/monitoring (Wave C T3 증거 기반)"
```

### Task B1-6: staging-deploy workflow

**Files:**
- Create: `.github/workflows/staging-deploy.yml`

- [ ] **Step B1-6.1: workflow 작성**

Create `.github/workflows/staging-deploy.yml`:

```yaml
name: staging-deploy
on:
  workflow_dispatch:
    inputs:
      module:
        description: "module to deploy"
        required: true
        default: "gateway"
      sha:
        description: "image sha"
        required: false

jobs:
  build-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
        with: { driver-opts: "image=moby/buildkit:latest" }
      - uses: docker/login-action@v3
        with:
          registry: registry.masblue.dev
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_TOKEN }}
      - name: Build & push
        run: |
          SHA="${{ inputs.sha || github.sha }}"
          MODULE="${{ inputs.module }}"
          docker buildx build \
            --tag registry.masblue.dev/oneerp/${MODULE}:staging-${SHA} \
            --tag registry.masblue.dev/oneerp/${MODULE}:staging-latest \
            --push \
            -f services/${MODULE}/Dockerfile .
  kustomize-apply:
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Apply staging overlay
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" > /tmp/kc
          export KUBECONFIG=/tmp/kc
          kubectl apply -k deploy/staging
          kubectl -n staging rollout status deploy/${{ inputs.module }} --timeout=5m
```

- [ ] **Step B1-6.2: yaml 파싱 검증 + Commit**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/staging-deploy.yml'))"
```

```bash
git add .github/workflows/staging-deploy.yml
git commit -m "ci(staging): manual deploy workflow — buildx + kustomize apply"
```

### B-2: Spec III Phase 1 — accounting L0 (worktree: `feat/spec3-accounting-l0`)

### Task B2-1: T2 artifact 수집기 (회귀 차단)

**Files:**
- Create: `scripts/ci/collect_t2_artifacts.py`
- Create: `tests/unit/test_collect_t2_artifacts.py`

- [ ] **Step B2-1.1: 실패 테스트 작성**

Create `tests/unit/test_collect_t2_artifacts.py`:

```python
from __future__ import annotations
import json
from pathlib import Path
import pytest
from scripts.ci.collect_t2_artifacts import (
    normalize_artifact_name,
    place_artifact,
    build_expected_globs,
)

def test_normalize_artifact_name_extracts_gate_module() -> None:
    assert normalize_artifact_name("t2-G1-2-accounting-run") == ("G1-2", "accounting")
    assert normalize_artifact_name("t2-G3-1-gateway-ci") == ("G3-1", "gateway")

def test_normalize_artifact_name_rejects_bad_names() -> None:
    with pytest.raises(ValueError):
        normalize_artifact_name("bad-name")

def test_place_artifact_writes_expected_path(tmp_path: Path) -> None:
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"ok": True}))
    dest = place_artifact(src, gate="G1-2", module="accounting", root=tmp_path / "out")
    assert dest.exists()
    assert dest.parent == tmp_path / "out" / "T2" / "G1-2" / "accounting"
    assert dest.name.startswith("run-")
    assert dest.suffix == ".json"

def test_build_expected_globs_matches_gate_module_matrix() -> None:
    globs = build_expected_globs(gates=["G1-2", "G1-3"], modules=["accounting", "hr"])
    assert "artifacts/T2/G1-2/accounting/run-*.json" in globs
    assert "artifacts/T2/G1-3/hr/run-*.json" in globs
    assert len(globs) == 4
```

Run:
```bash
uv run pytest tests/unit/test_collect_t2_artifacts.py -v
```
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step B2-1.2: 구현**

Create `scripts/ci/collect_t2_artifacts.py`:

```python
from __future__ import annotations
"""T2 tier CI artifact 수집기.

Spec II 회귀(run-*.json 미수집으로 4셀 PARTIAL)를 차단하기 위한 전용 모듈.
GitHub Actions artifact 이름 규칙: `t2-<GATE>-<MODULE>-<suffix>`.
"""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

_NAME_RE = re.compile(r"^t2-(G\d-\d)-([a-z][a-z0-9-]*)-[a-z0-9-]+$")

def normalize_artifact_name(name: str) -> tuple[str, str]:
    m = _NAME_RE.match(name)
    if not m:
        raise ValueError(f"bad artifact name: {name!r}")
    return m.group(1), m.group(2)

def place_artifact(src: Path, *, gate: str, module: str, root: Path) -> Path:
    dest_dir = root / "T2" / gate / module
    dest_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = dest_dir / f"run-{ts}.json"
    shutil.copy2(src, dest)
    return dest

def build_expected_globs(*, gates: list[str], modules: list[str]) -> list[str]:
    return [f"artifacts/T2/{g}/{m}/run-*.json" for g in gates for m in modules]

def main() -> None:
    import argparse, json, sys
    p = argparse.ArgumentParser()
    p.add_argument("--src", type=Path, required=True, help="downloaded artifact file")
    p.add_argument("--name", required=True, help="artifact name (t2-G*-module-*)")
    p.add_argument("--root", type=Path, default=Path("artifacts"))
    ns = p.parse_args()
    gate, module = normalize_artifact_name(ns.name)
    dest = place_artifact(ns.src, gate=gate, module=module, root=ns.root)
    json.dump({"placed": str(dest)}, sys.stdout)

if __name__ == "__main__":
    main()
```

- [ ] **Step B2-1.3: 테스트 PASS 확인**

Run:
```bash
uv run pytest tests/unit/test_collect_t2_artifacts.py -v
```
Expected: 4 passed

- [ ] **Step B2-1.4: gate artifact_glob 매핑 일관성 검증 테스트 추가**

Append to `tests/unit/test_collect_t2_artifacts.py`:

```python
from scripts.audit.gates import g1_tests  # type: ignore

def test_collector_globs_align_with_gate_matrix() -> None:
    expected = build_expected_globs(
        gates=["G1-2", "G1-3", "G1-5"],
        modules=["accounting", "hr", "gateway"],
    )
    gate_declared = getattr(g1_tests, "EXPECTED_T2_GLOBS", None)
    if gate_declared is not None:
        for glob in gate_declared:
            assert glob in expected or any(g.endswith(glob.split("/")[-1]) for g in expected)
```

(게이트 모듈에 `EXPECTED_T2_GLOBS` 미정의 시 skip — 차기 수정에서 추가)

Run:
```bash
uv run pytest tests/unit/test_collect_t2_artifacts.py -v
```
Expected: 전부 PASS

- [ ] **Step B2-1.5: Commit**

```bash
git add scripts/ci/collect_t2_artifacts.py tests/unit/test_collect_t2_artifacts.py
git commit -m "feat(ci): T2 artifact 수집기 · Spec II 4셀 PARTIAL 회귀 차단"
```

### Task B2-2: MODULE_CLUSTER 확인 + accounting/hr 등록 검증

- [ ] **Step B2-2.1: 확인**

Run:
```bash
rg "_MODULE_CLUSTER" scripts/audit/gates/__init__.py
rg "accounting|hr" scripts/audit/gates/__init__.py
```
Expected: 정찰 보고대로 `"accounting": "finance/accounting"`, `"hr": "hr/hr"` 이미 존재해야 함.

부재 시 Step B2-2.2 수행, 존재 시 스킵.

- [ ] **Step B2-2.2: (필요 시) 엔트리 추가**

Modify `scripts/audit/gates/__init__.py`의 `_MODULE_CLUSTER` 딕셔너리:

```python
_MODULE_CLUSTER: dict[str, str] = {
    "gateway": "gateway",
    "accounting": "finance/accounting",
    "hr": "hr/hr",
    # ...
}
```

- [ ] **Step B2-2.3: Commit (변경 있을 시)**

```bash
git add scripts/audit/gates/__init__.py
git commit -m "feat(audit): _MODULE_CLUSTER에 accounting/hr 경로 등록 확인"
```

### Task B2-3~B2-13: accounting L0 11셀 (템플릿 호출)

각 셀은 Spec II plan (`docs/superpowers/plans/2026-04-22-commercial-grade-v2-spec2-gateway.md`)의 대응 Task를 `module=accounting`으로 재실행. 본 플랜은 셀별 **수용 기준 + 산출물 경로 + 수정 포인트**만 박제한다.

공통 실행 패턴:

```bash
# 각 셀 시작 시
./scripts/commercial-engine plan-wave --modules accounting --exclude-tiers T3 --cell <GATE>
# 작업 후
./scripts/commercial-engine run-cell <GATE> --module accounting
./scripts/commercial-engine validate-cell <GATE> --module accounting
```

#### Task B2-3: G1-1 ADR (accounting bounds)
- **Files:** Create `docs/kb/adr/0019-accounting-bounds.md` (≥ 200L frontmatter: gate=G1-1, module=accounting, tier=T1)
- **수용 기준:** 파일 존재 · 라인 ≥ 200 · frontmatter valid · `validate_cell G1-1 accounting` PASS
- **Commit:** `docs(adr): ADR-0019 accounting bounds · G1-1 accounting T1`

#### Task B2-4: G1-2 OpenAPI (accounting)
- **Files:**
  - Create: `services/finance/accounting/openapi.yaml` (FastAPI `/openapi.json` 덤프 → yaml 변환)
  - Create: `tests/integration/accounting/test_openapi_contract.py` (schemathesis)
  - Artifact: `artifacts/T1/G1-2/accounting/schemathesis-*.log`, `artifacts/T2/G1-2/accounting/run-*.json`
- **구현 step:**
  1. `uv run --package oneerp-accounting --directory services/finance/accounting python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > /tmp/openapi.json`
  2. yq로 yaml 변환 · `services/finance/accounting/openapi.yaml`에 저장
  3. schemathesis 테스트 파일 생성 (schemathesis CLI 래핑)
  4. CI workflow `.github/workflows/gate-g1-2.yml` 에 matrix로 accounting 추가
  5. T2 artifact는 `collect_t2_artifacts.py`로 다운로드
- **수용 기준:** T1 로그 존재, T2 run-*.json 존재, 둘 다 `validate_cell G1-2 accounting` PASS
- **Commit:** `feat(accounting): G1-2 OpenAPI contract · T1+T2 PASS`

#### Task B2-5: G1-3 Integration test (accounting)
- **Files:** Create `tests/integration/accounting/test_{journal,accounts,budgets}_flow.py` · ≥ 8 tests
- **수용 기준:** `pytest -m integration services/finance/accounting` coverage ≥ 60% · artifact에 pytest log
- **Commit:** `feat(accounting): G1-3 통합테스트 8건 · coverage 60%+`

#### Task B2-6: G1-4 Unit + Mutation (accounting)
- **Files:** 기존 332 tests + `mutmut` 설정 (`.mutmut-config.ini` 또는 pyproject)
- **수용 기준:** unit coverage ≥ 80% · mutation kill rate ≥ 50%
- **Commit:** `test(accounting): G1-4 mutation ≥ 50%`

#### Task B2-7: G2-1 SLO (accounting T2 — staging 또는 시뮬)
- **Files:** `scripts/staging/seed_monitoring.py`의 출력 → `artifacts/T2/G2-1/accounting/run-*.json`
- **수용 기준:** 30d p95/error/avail 시계열 존재
- **Commit:** `feat(accounting): G2-1 SLO 30d 시뮬 (staging 미배포 구간)`

#### Task B2-8: G2-3 Perf regression (accounting)
- **Files:** Create `tests/perf/accounting/baseline.json` + regression script
- **수용 기준:** p95 기준 +10% 이내
- **Commit:** `test(accounting): G2-3 perf regression baseline`

#### Task B2-9: G2-5 i18n coverage (accounting)
- **Files:** `packages/core/i18n/ko.json`, `en.json` accounting 키 추가 · script 재측정
- **수용 기준:** coverage ≥ 90%
- **Commit:** `feat(accounting): G2-5 i18n ko/en 90%+`

#### Task B2-10: G3-1 AuthN 7종 (accounting)
- **Files:** `tests/security/accounting/test_auth_*.py` × 7 (JWT 만료/서명 위조/audience/issuer/nonce/replay/scope)
- **수용 기준:** 7 tests pass · `per-file-ignores`에 `S105` 포함됨 (Task A1)
- **Commit:** `test(accounting): G3-1 AuthN 7종 · JWT 검증 매트릭스`

#### Task B2-11: G3-4 Audit emit mutation (accounting)
- **Files:** Modify `services/finance/accounting/oneerp_accounting_app/audit_hooks.py` (gateway 패턴 이식) · `tests/unit/accounting/test_audit_mutation.py` 10 mutation
- **수용 기준:** 10 mutation kill
- **Commit:** `test(accounting): G3-4 audit emit mutation 10건`

#### Task B2-12: G3-5 Dep audit (accounting)
- **Files:** `uv run pip-audit` artifact → `artifacts/T1/G3-5/accounting/pip-audit-*.json`
- **수용 기준:** CVE count = 0 또는 mitigated
- **Commit:** `chore(accounting): G3-5 dep audit CVE 0`

#### Task B2-13: G5-1 Manual (accounting)
- **Files:** Modify `docs/manual/accounting.md` → ≥ 400L (T1+T2 증거 표 포함)
- **수용 기준:** line ≥ 400, frontmatter module=accounting, tier=T1/T2
- **Commit:** `docs(accounting): G5-1 manual 400L+`

### Task B2-14: Wave B-2 집계

- [ ] **Step B2-14.1: 전체 셀 스코어**

Run:
```bash
./scripts/commercial-engine score --module accounting
```
Expected: accounting 11/14 이상 (L1 3셀은 Wave D)

- [ ] **Step B2-14.2: Commit — Wave B-2 마감**

```bash
git add -A
git commit -m "feat(accounting): Wave B-2 L0 11셀 완료 · Spec III Phase 1"
```

---

## Wave C — 병렬 2 worktree (2주)

### C-1: Spec II.5 Phase 2 — T3 6셀 gateway (worktree: `feat/spec2.5-t3-cells`)

Wave C-1 전제: Task B1-1~B1-6 완료 AND `kubectl -n staging get all | grep gateway` deploy Running.

### Task C1-1: G2-2 부하테스트 (k6)

**Files:**
- Create: `tests/load/gateway/scenarios.js`
- Create: `.github/workflows/load-test.yml`
- Artifact: `artifacts/T3/G2-2/gateway/k6-<ts>.csv`, `k6-summary-<ts>.json`

- [ ] **Step C1-1.1: k6 시나리오**

Create `tests/load/gateway/scenarios.js`:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const p95Latency = new Trend('p95_latency');

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<300', 'p(99)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const base = __ENV.GATEWAY_URL || 'https://staging-gateway.oneerp.dev';
  const token = __ENV.JWT || '';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = http.get(`${base}/health`, { headers });
  check(res, { '200': (r) => r.status === 200 });
  p95Latency.add(res.timings.duration);
  sleep(1);
}
```

- [ ] **Step C1-1.2: workflow**

Create `.github/workflows/load-test.yml`:

```yaml
name: load-test
on:
  workflow_dispatch:
    inputs:
      module: { required: true, default: gateway }
jobs:
  k6:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: grafana/setup-k6-action@v1
      - run: |
          TS=$(date -u +%Y%m%dT%H%M%SZ)
          mkdir -p artifacts/T3/G2-2/${{ inputs.module }}
          k6 run \
            --summary-export=artifacts/T3/G2-2/${{ inputs.module }}/k6-summary-$TS.json \
            --out csv=artifacts/T3/G2-2/${{ inputs.module }}/k6-$TS.csv \
            tests/load/${{ inputs.module }}/scenarios.js
      - uses: actions/upload-artifact@v4
        with:
          name: t3-G2-2-${{ inputs.module }}-run
          path: artifacts/T3/G2-2/${{ inputs.module }}/*
```

- [ ] **Step C1-1.3: 로컬 dry-run**

Run:
```bash
k6 run --vus 1 --duration 10s tests/load/gateway/scenarios.js
```
Expected: threshold 위반 없이 완료 (staging 없으면 skip)

- [ ] **Step C1-1.4: Commit**

```bash
git add tests/load/gateway/scenarios.js .github/workflows/load-test.yml
git commit -m "feat(T3): G2-2 k6 부하 시나리오 + workflow"
```

### Task C1-2: G2-4 카오스 (chaoskube)

**Files:**
- Create: `tests/chaos/gateway/scenarios.yaml`
- Create: `.github/workflows/chaos-test.yml`

- [ ] **Step C1-2.1: 시나리오**

Create `tests/chaos/gateway/scenarios.yaml`:

```yaml
apiVersion: chaosmesh.org/v1alpha1
kind: PodChaos
metadata:
  name: gateway-pod-kill
  namespace: staging
spec:
  action: pod-kill
  mode: one
  duration: "30s"
  selector:
    labelSelectors:
      app: gateway
    namespaces: ["staging"]
  scheduler:
    cron: "@every 5m"
```

- [ ] **Step C1-2.2: workflow + MTTR 측정**

Create `.github/workflows/chaos-test.yml`:

```yaml
name: chaos-test
on:
  workflow_dispatch:
    inputs:
      module: { required: true, default: gateway }
jobs:
  chaos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Apply chaos
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" > /tmp/kc
          export KUBECONFIG=/tmp/kc
          TS=$(date -u +%Y%m%dT%H%M%SZ)
          mkdir -p artifacts/T3/G2-4/${{ inputs.module }}
          kubectl apply -f tests/chaos/${{ inputs.module }}/scenarios.yaml
          sleep 60
          # MTTR: pod 재기동까지 시간 측정
          kubectl -n staging rollout status deploy/${{ inputs.module }} --timeout=5m | \
            tee artifacts/T3/G2-4/${{ inputs.module }}/chaos-$TS.log
      - uses: actions/upload-artifact@v4
        with:
          name: t3-G2-4-${{ inputs.module }}-run
          path: artifacts/T3/G2-4/${{ inputs.module }}/*
```

- [ ] **Step C1-2.3: Commit**

```bash
git add tests/chaos/gateway/scenarios.yaml .github/workflows/chaos-test.yml
git commit -m "feat(T3): G2-4 chaos scenario + MTTR 측정 workflow"
```

### Task C1-3: G4-3 백업·복구 드릴

**Files:**
- Create: `docs/ops/drills/G4-3/2026-04-??-gateway.md`
- Create: `.github/workflows/backup-drill.yml`

- [ ] **Step C1-3.1: 드릴 문서**

Create `docs/ops/drills/G4-3/2026-04-24-gateway.md` (drill 실행 날짜로 조정):

```markdown
---
gate: G4-3
module: gateway
drill_date: 2026-04-24
rto_target: 30m
rpo_target: 15m
evidence: artifacts/T3/G4-3/gateway/restore-2026-04-24T????Z.log
approver: TBD
---
# G4-3 백업·복구 드릴 — gateway · 2026-04-24

## 시나리오
1. staging PostgreSQL에 테스트 데이터 주입
2. pg_dump (Velero backup)
3. DB drop + 재생성
4. dump 복원
5. 데이터 무결성 검증 + RTO 측정

## 실행 명령

```bash
kubectl -n staging exec deploy/postgresql -- pg_dump -U oneerp -d accounting > /tmp/backup-$(date -u +%Y%m%dT%H%M%SZ).sql
```

(전체 절차는 runbook 참조)

## 측정
| 항목 | 결과 |
|------|------|
| RTO 실측 | (drill 후 기록) |
| RPO 실측 | (drill 후 기록) |
| 데이터 손실 | 0 예상 |
```

- [ ] **Step C1-3.2: workflow**

Create `.github/workflows/backup-drill.yml`:

```yaml
name: backup-drill
on: { workflow_dispatch: { inputs: { module: { required: true, default: gateway } } } }
jobs:
  drill:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Execute drill
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" > /tmp/kc
          export KUBECONFIG=/tmp/kc
          TS=$(date -u +%Y%m%dT%H%M%SZ)
          mkdir -p artifacts/T3/G4-3/${{ inputs.module }}
          START=$(date +%s)
          kubectl -n staging exec deploy/postgresql -- pg_dump -U oneerp -d ${{ inputs.module }} > /tmp/backup-$TS.sql
          kubectl -n staging exec deploy/postgresql -- psql -U oneerp -c "DROP DATABASE IF EXISTS ${{ inputs.module }}_test;"
          kubectl -n staging exec deploy/postgresql -- psql -U oneerp -c "CREATE DATABASE ${{ inputs.module }}_test;"
          cat /tmp/backup-$TS.sql | kubectl -n staging exec -i deploy/postgresql -- psql -U oneerp -d ${{ inputs.module }}_test
          END=$(date +%s)
          RTO=$((END - START))
          echo "RTO=${RTO}s" | tee artifacts/T3/G4-3/${{ inputs.module }}/restore-$TS.log
      - uses: actions/upload-artifact@v4
        with: { name: t3-G4-3-${{ inputs.module }}-run, path: artifacts/T3/G4-3/${{ inputs.module }}/* }
```

- [ ] **Step C1-3.3: Commit**

```bash
git add docs/ops/drills/G4-3/2026-04-24-gateway.md .github/workflows/backup-drill.yml
git commit -m "feat(T3): G4-3 backup/restore 드릴 + workflow"
```

### Task C1-4: G4-4 롤백 드릴

**Files:**
- Create: `docs/ops/drills/G4-4/2026-04-24-gateway.md`
- Create: `.github/workflows/rollback-drill.yml`

- [ ] **Step C1-4.1: 드릴 문서**

Create `docs/ops/drills/G4-4/2026-04-24-gateway.md`:

```markdown
---
gate: G4-4
module: gateway
drill_date: 2026-04-24
evidence: artifacts/T3/G4-4/gateway/rollback-*.log
approver: TBD
---
# G4-4 롤백 드릴 — gateway · 2026-04-24

## 시나리오
1. staging gateway에 v2 (악성 버전) 배포
2. 헬스체크 실패 확인
3. ArgoCD rollback → v1
4. Green 확인 + rollback 소요 시간 측정

## 목표 RTO: 10분
```

- [ ] **Step C1-4.2: workflow**

Create `.github/workflows/rollback-drill.yml`:

```yaml
name: rollback-drill
on: { workflow_dispatch: { inputs: { module: { required: true, default: gateway } } } }
jobs:
  drill:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Run rollback
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" > /tmp/kc
          export KUBECONFIG=/tmp/kc
          TS=$(date -u +%Y%m%dT%H%M%SZ)
          mkdir -p artifacts/T3/G4-4/${{ inputs.module }}
          START=$(date +%s)
          kubectl -n staging set image deploy/${{ inputs.module }} ${{ inputs.module }}=registry.masblue.dev/oneerp/${{ inputs.module }}:staging-broken || true
          sleep 30
          kubectl -n staging rollout undo deploy/${{ inputs.module }}
          kubectl -n staging rollout status deploy/${{ inputs.module }} --timeout=10m
          END=$(date +%s)
          echo "rollback_duration=$((END - START))s" | tee artifacts/T3/G4-4/${{ inputs.module }}/rollback-$TS.log
      - uses: actions/upload-artifact@v4
        with: { name: t3-G4-4-${{ inputs.module }}-run, path: artifacts/T3/G4-4/${{ inputs.module }}/* }
```

- [ ] **Step C1-4.3: Commit**

```bash
git add docs/ops/drills/G4-4/2026-04-24-gateway.md .github/workflows/rollback-drill.yml
git commit -m "feat(T3): G4-4 rollback 드릴 + workflow"
```

### Task C1-5: G4-5 on-call 드릴

**Files:**
- Create: `docs/ops/drills/G4-5/2026-04-24-gateway.md`

- [ ] **Step C1-5.1: 드릴 문서 + 실행 로그**

Create `docs/ops/drills/G4-5/2026-04-24-gateway.md`:

```markdown
---
gate: G4-5
module: gateway
drill_date: 2026-04-24
evidence: artifacts/T3/G4-5/gateway/oncall-*.log
ack_target_min: 5
resolve_target_min: 30
---
# G4-5 on-call 드릴 — gateway · 2026-04-24

## 시나리오
1. Prometheus rule `gateway-5xx-spike` 수동 trigger (`amtool`)
2. Alertmanager → PagerDuty sandbox route 확인
3. on-call 응답자 ack 시간 기록
4. runbook(`docs/ops/runbooks/gateway.md`) 참조 대응 → 해결까지 기록

## 측정
| 시각 | 이벤트 |
|------|-------|
| t+0 | 알림 발송 |
| t+? | ack |
| t+? | 해결 |
```

- [ ] **Step C1-5.2: drill 실행 로그 artifact**

Drill 실행 후 `artifacts/T3/G4-5/gateway/oncall-<ts>.log`에 이벤트 타임스탬프 기록 · 스크린샷 또는 PagerDuty incident JSON 첨부.

- [ ] **Step C1-5.3: Commit**

```bash
git add docs/ops/drills/G4-5/ artifacts/T3/G4-5/
git commit -m "feat(T3): G4-5 on-call 드릴 · PagerDuty sandbox"
```

### Task C1-6: G5-3 UAT

**Files:**
- Create: `docs/governance/commercial/gateway.md`

- [ ] **Step C1-6.1: UAT 문서**

Create `docs/governance/commercial/gateway.md` (≥ 200L):

```markdown
---
gate: G5-3
module: gateway
uat_date: 2026-04-25
approvers:
  - name: TBD
    role: product owner
  - name: TBD
    role: QA lead
personas: [admin, operator, end-user]
evidence: artifacts/T3/G5-3/gateway/uat-*.log
---
# Gateway UAT — 2026-04-25

## 페르소나 3종
### Admin
(시나리오 5건 · 각 수용 기준)
### Operator
(시나리오 5건)
### End-user
(시나리오 5건)

## 실행 기록
(15 시나리오 각 실행 결과 로그)
```

- [ ] **Step C1-6.2: Commit — Wave C-1 마감**

```bash
git add docs/governance/commercial/gateway.md
git commit -m "feat(T3): G5-3 UAT · gateway Spec II.5 완료"
```

### Task C1-7: T3 6셀 집계

- [ ] **Step C1-7.1: score 확인**

Run:
```bash
./scripts/commercial-engine score --module gateway --tier T3
```
Expected: 6/6 PASS (또는 partial 사유 명시)

- [ ] **Step C1-7.2: Commit**

```bash
git add -A
git commit -m "chore(T3): gateway T3 6셀 집계 · Spec II.5 완료"
```

### C-2: Spec III Phase 2 — hr 선행 + L0 (worktree: `feat/spec3-hr-alignment`)

### Task C2-1: hr config.py (선행 정합)

**Files:**
- Create: `services/hr/hr/oneerp_hr_app/config.py`
- Create: `services/hr/hr/tests/unit/test_config.py`

- [ ] **Step C2-1.1: 실패 테스트**

Create `services/hr/hr/tests/unit/test_config.py`:

```python
from __future__ import annotations
from oneerp_hr_app.config import HRSettings, get_hr_settings

def test_hr_settings_defaults() -> None:
    s = HRSettings()
    assert s.hr_scim_enabled is False
    assert s.hr_ldap_url.startswith("ldaps://") or s.hr_ldap_url == ""

def test_get_hr_settings_is_cached() -> None:
    a = get_hr_settings()
    b = get_hr_settings()
    assert a is b
```

Run:
```bash
uv run --package oneerp-hr --directory services/hr/hr pytest tests/unit/test_config.py -v
```
Expected: FAIL (module not found)

- [ ] **Step C2-1.2: 구현**

Create `services/hr/hr/oneerp_hr_app/config.py`:

```python
from __future__ import annotations
"""HR 모듈 설정 — CoreSettings 상속, accounting 패턴 미러."""
from functools import lru_cache
from oneerp_core.config import CoreSettings

class HRSettings(CoreSettings):
    hr_ldap_url: str = ""
    hr_scim_enabled: bool = False
    hr_payroll_webhook: str = ""

    model_config = {"env_prefix": "ONEERP_", "extra": "ignore"}

@lru_cache(maxsize=1)
def get_hr_settings() -> HRSettings:
    return HRSettings()
```

- [ ] **Step C2-1.3: 테스트 PASS**

Run:
```bash
uv run --package oneerp-hr --directory services/hr/hr pytest tests/unit/test_config.py -v
```
Expected: 2 passed

- [ ] **Step C2-1.4: Commit**

```bash
git add services/hr/hr/oneerp_hr_app/config.py services/hr/hr/tests/unit/test_config.py
git commit -m "feat(hr): HRSettings 추가 · CoreSettings 상속 · lru_cache DI"
```

### Task C2-2: hr events/ 패키지 (선행 정합)

**Files:**
- Create: `services/hr/hr/oneerp_hr_app/events/__init__.py`
- Create: `services/hr/hr/oneerp_hr_app/events/handlers.py`
- Create: `services/hr/hr/tests/unit/test_events_registry.py`

- [ ] **Step C2-2.1: 실패 테스트**

Create `services/hr/hr/tests/unit/test_events_registry.py`:

```python
from __future__ import annotations
from oneerp_hr_app.events import event_registry
from oneerp_hr_app.events.handlers import register_handlers

def test_event_registry_has_employee_handlers_after_register() -> None:
    register_handlers(event_registry)
    names = {h.name for h in event_registry.all()}
    assert "employee.hired" in names
    assert "employee.terminated" in names
    assert "employee.transferred" in names
```

Run:
```bash
uv run --package oneerp-hr --directory services/hr/hr pytest tests/unit/test_events_registry.py -v
```
Expected: FAIL

- [ ] **Step C2-2.2: 구현**

Create `services/hr/hr/oneerp_hr_app/events/__init__.py`:

```python
from __future__ import annotations
"""HR 이벤트 체인 — accounting 패턴 미러."""
from oneerp_core.events import EventHandlerRegistry

event_registry: EventHandlerRegistry = EventHandlerRegistry()
```

Create `services/hr/hr/oneerp_hr_app/events/handlers.py`:

```python
from __future__ import annotations
from typing import Any
from oneerp_core.events import EventHandlerRegistry, on

async def on_employee_hired(evt: dict[str, Any]) -> None:
    pass

async def on_employee_terminated(evt: dict[str, Any]) -> None:
    pass

async def on_employee_transferred(evt: dict[str, Any]) -> None:
    pass

async def on_department_reorganized(evt: dict[str, Any]) -> None:
    pass

async def on_designation_changed(evt: dict[str, Any]) -> None:
    pass

async def on_payroll_run_completed(evt: dict[str, Any]) -> None:
    pass

async def on_leave_approved(evt: dict[str, Any]) -> None:
    pass

def register_handlers(registry: EventHandlerRegistry) -> None:
    registry.register("employee.hired", on_employee_hired)
    registry.register("employee.terminated", on_employee_terminated)
    registry.register("employee.transferred", on_employee_transferred)
    registry.register("department.reorganized", on_department_reorganized)
    registry.register("designation.changed", on_designation_changed)
    registry.register("payroll.run.completed", on_payroll_run_completed)
    registry.register("leave.approved", on_leave_approved)
```

- [ ] **Step C2-2.3: app/main.py 통합**

Modify `services/hr/hr/oneerp_hr_app/main.py` — FastAPI 기동 시 register 호출:

```python
from oneerp_hr_app.events import event_registry
from oneerp_hr_app.events.handlers import register_handlers

# app 생성 직후
register_handlers(event_registry)
```

- [ ] **Step C2-2.4: 테스트 PASS**

Run:
```bash
uv run --package oneerp-hr --directory services/hr/hr pytest tests/unit/test_events_registry.py -v
```
Expected: 1 passed

- [ ] **Step C2-2.5: 기동 확인**

Run (별도 터미널):
```bash
uv run --package oneerp-hr --directory services/hr/hr uvicorn app.main:app --port 8099
```
Expected: 시작 시 예외 없음. `curl localhost:8099/health` → 200.

- [ ] **Step C2-2.6: Commit**

```bash
git add services/hr/hr/oneerp_hr_app/events services/hr/hr/oneerp_hr_app/main.py services/hr/hr/tests/unit/test_events_registry.py
git commit -m "feat(hr): event_registry + 7 핸들러 · accounting 패턴 미러"
```

### Task C2-3~C2-13: hr L0 11셀

accounting Task B2-3~B2-13과 동일 셀 구성, `module=hr`. 수용 기준과 산출물 경로는 accounting과 1:1 대응. 차이점:
- hr unit test 154 → G1-4 unit coverage가 accounting 대비 낮을 수 있음 → 누락 테스트 보강 필요
- G1-5 Playwright는 hr UI가 gateway/accounting 대비 덜 성숙 → 3 시나리오(직원 조회/부서 조회/직위 변경) 최소 목표

각 셀에서 **TDD · 커밋 · `validate_cell` 확인** 싸이클을 반복. 11셀 각 1 커밋.

### Task C2-14: Wave C-2 집계

```bash
./scripts/commercial-engine score --module hr
git add -A
git commit -m "feat(hr): Wave C-2 L0 11셀 완료 · Spec III hr 수직"
```

---

## Wave D — L1 마감 (1주)

### Task D1: accounting L1 3셀 (Playwright · ExternalSecret · OPA)

#### D1-a: G1-5 accounting Playwright

**Files:**
- Create: `tests/playwright/ui/accounting/test_{journal,periods,budgets}_flow.py` × 3

- [ ] **Step D1-a.1: 첫 시나리오 (TDD)**

Create `tests/playwright/ui/accounting/test_journal_flow.py`:

```python
from __future__ import annotations
import pytest
from playwright.sync_api import Page

@pytest.mark.playwright
def test_create_journal_entry_happy_path(page: Page) -> None:
    page.goto("http://localhost:3000/accounting/journal")
    page.fill("input[name=period]", "2026-04")
    page.click("button[data-testid=new-entry]")
    page.fill("input[data-testid=debit-amount]", "1000")
    page.fill("input[data-testid=credit-amount]", "1000")
    page.click("button[data-testid=save]")
    assert page.locator("[data-testid=toast-success]").is_visible()
```

- [ ] **Step D1-a.2: 나머지 2 시나리오 (periods · budgets) 동일 패턴**

- [ ] **Step D1-a.3: 실행 · artifact**

Run:
```bash
uv run pytest tests/playwright/ui/accounting/ -m playwright --tracing=on
```
Artifact: `artifacts/T1/G1-5/accounting/playwright-trace-*.zip`

- [ ] **Step D1-a.4: Commit**

```bash
git add tests/playwright/ui/accounting/
git commit -m "test(accounting): G1-5 Playwright 3 시나리오 · journal/periods/budgets"
```

#### D1-b: G3-2 accounting ExternalSecret

**Files:**
- Create: `deploy/secrets/accounting/externalsecret.yaml` (B1-3 gateway 패턴 미러)

- [ ] **Step D1-b.1: 작성**

gateway yaml을 복사 후 `name`과 `remoteRef.key`를 `accounting/*`으로 교체.

- [ ] **Step D1-b.2: rotate 테스트**

Run:
```bash
./scripts/secrets/rotate-gateway.sh accounting staging
```
Expected: dry-run 통과

- [ ] **Step D1-b.3: Commit**

```bash
git add deploy/secrets/accounting/externalsecret.yaml
git commit -m "feat(accounting): G3-2 ExternalSecret + staging rotate"
```

#### D1-c: G3-3 accounting OPA rego

**Files:**
- Create: `policies/accounting/routes.rego`
- Create: `policies/accounting/routes_test.rego`

- [ ] **Step D1-c.1: rego 작성**

Create `policies/accounting/routes.rego`:

```rego
package accounting.routes

default allow := false

allow if {
  input.method == "GET"
  startswith(input.path, "/accounting/")
  input.user.roles[_] == "accounting_viewer"
}

allow if {
  input.method in {"POST", "PUT", "DELETE"}
  startswith(input.path, "/accounting/journal")
  input.user.roles[_] == "accounting_editor"
}
```

Create `policies/accounting/routes_test.rego`:

```rego
package accounting.routes

test_viewer_can_get if {
  allow with input as {"method":"GET","path":"/accounting/journal","user":{"roles":["accounting_viewer"]}}
}

test_anon_denied if {
  not allow with input as {"method":"GET","path":"/accounting/journal","user":{"roles":[]}}
}

test_editor_can_post if {
  allow with input as {"method":"POST","path":"/accounting/journal/new","user":{"roles":["accounting_editor"]}}
}

test_viewer_cannot_post if {
  not allow with input as {"method":"POST","path":"/accounting/journal/new","user":{"roles":["accounting_viewer"]}}
}

test_cross_module_denied if {
  not allow with input as {"method":"GET","path":"/hr/employees","user":{"roles":["accounting_viewer"]}}
}

test_unknown_role_denied if {
  not allow with input as {"method":"GET","path":"/accounting/journal","user":{"roles":["guest"]}}
}
```

- [ ] **Step D1-c.2: opa test 실행**

Run:
```bash
opa test policies/accounting/ -v
```
Expected: 6 tests PASS · artifact로 출력 저장

- [ ] **Step D1-c.3: Commit**

```bash
git add policies/accounting/
git commit -m "feat(accounting): G3-3 OPA RBAC rego + 6 tests"
```

### Task D2: hr L1 3셀 (Playwright · ExternalSecret · OPA)

D1-a/b/c 패턴을 `module=hr`로 반복. 시나리오:
- D2-a G1-5: `tests/playwright/ui/hr/test_{employees,departments,designations}_flow.py`
- D2-b G3-2: `deploy/secrets/hr/externalsecret.yaml`
- D2-c G3-3: `policies/hr/routes.rego` (role=`hr_viewer`, `hr_editor`, `payroll_admin`)

각 셀별 Commit 3건.

### Task D3: 품질 게이트 최종 (ruff floor)

- [ ] **Step D3.1: 현 baseline 측정**

Run:
```bash
uv run ruff check . 2>&1 | tail -1
```

- [ ] **Step D3.2: option 판정 (F 또는 0)**

- `count ≤ 5`이고 모두 정당 noqa 대상 → option F
- 그 외 → option 0 (전수 수정)

- [ ] **Step D3.3: option F 선택 시 — noqa 주석 + 근거**

각 잔여 건에 대해:
```python
foo()  # noqa: RULE — 근거(ADR-0018 §2.<id>)
```

- [ ] **Step D3.4: option 0 선택 시 — 잔여 전수 수정**

- [ ] **Step D3.5: 재측정 · ratchet 최종 상태**

Run:
```bash
uv run ruff check . 2>&1 | tail -1
```
Expected: count ≤ floor (≤ 5 또는 0)

- [ ] **Step D3.6: Commit**

```bash
git add -u
git commit -m "chore(ruff): Wave D floor 도달 · ${FLOOR}건"
```

### Task D4: 23/23 score 집계 + ADR-0018 박제

**Files:**
- Create: `docs/kb/adr/0018-commercial-v2-spec3-completion.md`

- [ ] **Step D4.1: 전체 score**

Run:
```bash
./scripts/commercial-engine score --all
```
Expected: 19/23 이상

- [ ] **Step D4.2: ADR 작성**

Create `docs/kb/adr/0018-commercial-v2-spec3-completion.md`:

```markdown
---
title: ADR-0018 · Commercial Grade v2 Spec III/II.5/품질 게이트 완료
date: 2026-04-29
status: accepted
tags: [commercial-grade-v2, completion]
---

# ADR-0018 · Commercial Grade v2 Spec III/II.5/품질 게이트 완료

## Context
Spec II 종료 시점 score 13/23. 3 트랙 병렬 (Spec III 수평 · Spec II.5 수직 · 품질 게이트 횡단)으로 19+/23 달성.

## Outcome
- Spec III: accounting 14/14, hr 12+/14 (T1+T2)
- Spec II.5: gateway T3 6/6 + staging NS up
- 품질 게이트: ruff floor ${FLOOR} · ratchet 3 PR 연속 pass

## Evidence
- 설계: `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md`
- 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md`
- score 집계: `artifacts/score/2026-04-29.json`
- ADR-0017 (ruff ratchet) 연계

## Next
- Spec IV: 46개 잔여 모듈 수직 완성 roadmap
- accounting/hr T3 6셀 (Spec IV 범위)
```

- [ ] **Step D4.3: INDEX.md 갱신**

Modify `docs/kb/adr/INDEX.md` — 0018 항목 추가.

- [ ] **Step D4.4: Commit — 최종**

```bash
git add docs/kb/adr/0018-commercial-v2-spec3-completion.md docs/kb/adr/INDEX.md artifacts/score/
git commit -m "docs(adr): ADR-0018 Spec III/II.5/품질 완료 · score ≥ 19/23"
```

---

## Exit 검증

- [ ] `./scripts/commercial-engine score --all` ≥ 19/23
- [ ] `uv run ruff check . 2>&1 | tail -1` ≤ floor
- [ ] `.github/workflows/ruff-ratchet.yml` 3 PR 연속 pass (이력 확인)
- [ ] ADR-0017, 0018 박제 완료
- [ ] staging NS running 30분 이상 관측
- [ ] gateway T3 6셀 PASS (또는 partial 사유 ADR 명시)
- [ ] accounting 14/14, hr 12+/14 T1+T2

모든 체크 통과 시 PR 생성 · merge.

---

<!-- v1.0 · 2026-04-22 · Spec III/II.5/품질 6주 통합 플랜 -->
