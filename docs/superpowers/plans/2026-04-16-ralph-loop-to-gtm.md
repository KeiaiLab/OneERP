# Ralph-Loop to GTM (M7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OneERP 저장소를 Pre-Loop Cleanup 후 Ralph-Loop Full Autopilot 모드로 기동해, Wave 1 × 23 게이트 매트릭스(276 셀)를 M7(v1.0 파일럿 출시 기준선)까지 자율 반복 구현한다.

**Architecture:** 설계 문서 `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md` 의 Gate-Walker 접근. Pre-Loop Cleanup 6 단계 → 제어 파일 2종(RALPH-LOOP-PROMPT.md, PROGRESS.md) 작성 → Baseline audit → HANDOFF.md 대기 상태 갱신 → `/ralph-loop:ralph-loop` 단일 호출로 기동. 루프 자체의 276 셀 공략은 본 계획 범위 밖 — `RALPH-LOOP-PROMPT.md` 가 루프 내부 행동을 직접 통제한다.

**Tech Stack:** Python 3.14 (uv workspace), Node.js 22 (pnpm workspace), FastAPI, Next.js 16, Docker Compose, NATS JetStream, FerretDB, chrome-devtools-mcp (Task 5 시 사용자 확인 1회), `/ralph-loop:ralph-loop` 플러그인 + OneERP `.claude/skills/ralph-loop/SKILL.md`.

---

## Task 구조 (12 Task)

| # | Task | 예상 소요 | 커밋 수 |
|---|---|---|---|
| 1 | 워킹트리 · submodule 상태 전수 분석 | 15 min | 0 |
| 2 | 워킹트리 수정 사항 분할 커밋 | 30 min | 1~3 |
| 3 | web/ detached HEAD 해소 — feature branch 복귀 | 5 min | 0 |
| 4 | web/ 10 modified + 9 untracked 주제별 분할 커밋 | 60 min | 5~8 (web) |
| 5 | web submodule pointer 갱신 + 부모 레포 커밋 | 10 min | 1 |
| 6 | Push origin/main + web submodule feature branch | 10 min | 0 |
| 7 | RALPH-LOOP-PROMPT.md 작성 | 30 min | 1 |
| 8 | PROGRESS.md 초기화 | 10 min | 1 |
| 9 | Baseline audit (commercial-status.json 생성) | 10 min | 1 |
| 10 | HANDOFF.md "Ralph-Loop 대기 중" 상태로 갱신 | 15 min | 1 |
| 11 | Kickoff 사전 상태 검증 | 10 min | 0 |
| 12 | Ralph-Loop 기동 | 5 min | (루프가 이후 커밋 담당) |

**합계**: 약 3 시간 (사용자 개입 0회 — 2026-04-16 실측에서 시각 이중 루프는 이미 완주된 상태로 확인됨) + Ralph-Loop 가동 (≈ 414 h 무인).

---

## Task 1: 워킹트리 · submodule 상태 전수 분석

**목적**: Task 2 분할 커밋을 설계하기 위해 9 modified + 1 untracked 각각이 무엇을 수정하는지 파악. core/ 서브모듈 상태도 확인.

**Files:**
- Read: `README.md`, `docs/ARCHITECTURE-MAP.md`, `docs/INDEX.md`, `docs/infra/inventory/cicd.md`, `docs/infra/inventory/repo.md`, `docs/infra/ops/rollback.md`, `docs/ops/runbook-service-deploy.md`, `scripts/ci/run.sh`, `tests/e2e/conftest.py`, `docs/engineering/architecture/repo-structure-rules.md`
- Inspect: `.playwright-mcp/` (untracked 디렉토리)
- Inspect: `core/` submodule

- [ ] **Step 1: 워킹트리 diff 전수 파악**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git diff --stat
git diff  # 모든 modified 파일 내용
```

Expected: 9 modified 파일 각각의 diff 내용 확인. 변경 규모와 주제 도메인 파악.

- [ ] **Step 2: untracked 파일 내용 파악**

Run:
```bash
cat docs/engineering/architecture/repo-structure-rules.md
ls -la .playwright-mcp/
```

Expected: `repo-structure-rules.md` 내용 확인. `.playwright-mcp/` 는 `.gitignore` 대상인지 확인.

- [ ] **Step 3: core/ 서브모듈 상태 파악**

Run:
```bash
git -C core status
git -C core diff --stat
git -C core log --oneline -5
```

Expected: core/ 의 미커밋 변경(사용자 작업)이 본 루프와 무관함을 확인.

- [ ] **Step 4: web/ 서브모듈 상태 파악**

Run:
```bash
git -C web status
git -C web branch --show-current
git -C web log --oneline -10
```

Expected: `feature/visual-dual-loop-customers-list` 브랜치에 7 커밋 존재 확인.

- [ ] **Step 5: 분할 커밋 설계 메모**

다음 질문에 텍스트로 답을 정리한다 (Task 2 의 커밋 메시지로 활용):
- 워킹트리 9 modified 가 몇 개 주제로 묶이는가? (예: 문서 정합 / CI 게이트 / E2E conftest / 아키텍처 문서)
- `.playwright-mcp/` 는 커밋 대상인가 gitignore 대상인가?
- `repo-structure-rules.md` 는 어떤 커밋에 포함되는가?

커밋 단위 분할 결과를 Task 2 의 실행 기준으로 사용한다.

---

## Task 2: 워킹트리 수정 사항 분할 커밋

**목적**: Task 1 의 분석 결과를 주제 단위 1~3 커밋으로 분할. atomic commit 규율.

**Files:**
- Modify: Task 1 Step 1 에서 식별된 9 modified 파일
- Create: `docs/engineering/architecture/repo-structure-rules.md` (staging 필요)
- Handle: `.playwright-mcp/` (gitignore 추가 또는 커밋)

- [ ] **Step 1: `.playwright-mcp/` 처리 판단**

Run:
```bash
grep -l "playwright-mcp" .gitignore
```

의사결정:
- 만약 `.gitignore` 에 이미 있다면 Step 3 에서 커밋 대상 제외
- 없고 세션별 산출물이라면 `.gitignore` 에 `.playwright-mcp/` 한 줄 추가하고 Step 3 에 포함

실행:
```bash
# 만약 gitignore 갱신이 필요한 경우:
echo '.playwright-mcp/' >> .gitignore
```

- [ ] **Step 2: 주제별 staging (Task 1 Step 5 의 분할 결과에 따라)**

예상 분할 (실제 분할은 Task 1 결과에 따라 조정):

```bash
# 커밋 A: 로드맵/문서 정합 — README, ARCHITECTURE-MAP, INDEX, repo-structure-rules
git add README.md docs/ARCHITECTURE-MAP.md docs/INDEX.md \
        docs/engineering/architecture/repo-structure-rules.md

# 커밋 B: 인프라 인벤토리 · 운영 런북 정비 — infra/inventory, infra/ops, ops
git add docs/infra/inventory/cicd.md docs/infra/inventory/repo.md \
        docs/infra/ops/rollback.md docs/ops/runbook-service-deploy.md

# 커밋 C: CI · E2E 정비 — scripts/ci/run.sh, tests/e2e/conftest.py
git add scripts/ci/run.sh tests/e2e/conftest.py

# 커밋 D: gitignore (Step 1 에서 필요 판정된 경우만)
git add .gitignore
```

- [ ] **Step 3: 각 커밋 작성**

```bash
# 커밋 A
git commit -m "$(cat <<'EOF'
docs(roadmap): 진입 정본 3종 + repo-structure-rules 정합 정리

README · ARCHITECTURE-MAP · INDEX 의 상용화 로드맵 진입 경로와
repo-structure-rules.md 초안을 본 세션 기준으로 맞춘다.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 B
git commit -m "$(cat <<'EOF'
docs(ops): 인프라 인벤토리 · 롤백 · 배포 런북 최신화

Phase 5 Pilot Ops Infra 실행 계획 기준으로 infra/inventory 와
ops 런북을 현행 코드 상태와 일치시킨다.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 C
git commit -m "$(cat <<'EOF'
ci(core): run.sh 게이트 정비 + e2e conftest 보완

루트 품질 게이트 스크립트와 E2E conftest 를 Ralph-Loop 기동 전
clean 상태로 정비한다. 기능 변경 없음.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 D (필요 시)
git commit -m "$(cat <<'EOF'
chore(gitignore): .playwright-mcp 제외

chrome-devtools-mcp 세션별 산출물 디렉토리를 gitignore 에 추가.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: clean main 확인**

Run:
```bash
git status
```

Expected:
```
On branch main
nothing to commit, working tree clean
```

단 `m web` (submodule pointer modified) 는 Task 3~4 에서 처리되므로 이 시점에 남아 있을 수 있음.

---

## Task 3: web/ detached HEAD 해소 — feature branch 복귀

**목적**: 2026-04-16 실측에서 web/ 서브모듈이 `bb81100` (detached HEAD) 에 있으며, `feature/visual-dual-loop-customers-list` 브랜치가 그보다 1 커밋 앞(`66c7ace ci(web): release smoke gate + playwright 필수 라우트 명시`)에 위치함을 확인했다. Task 4 의 주제별 분할 커밋이 이 브랜치 위에 누적되도록 HEAD 를 이동한다.

**Files:** (브랜치 이동만, 파일 수정 없음)

- [ ] **Step 1: detached HEAD 상태 최종 확인**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git branch --show-current
git rev-parse HEAD
git log feature/visual-dual-loop-customers-list..HEAD --oneline
git log HEAD..feature/visual-dual-loop-customers-list --oneline
```

Expected:
- `git branch --show-current` 공백 출력 (detached)
- HEAD = `bb81100...`
- `feature..HEAD` = 0 커밋 (HEAD 가 feature 의 ancestor)
- `HEAD..feature` = 1 커밋 (`66c7ace ci(web): release smoke gate ...`)

- [ ] **Step 2: feature branch 체크아웃**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git checkout feature/visual-dual-loop-customers-list
```

Expected:
```
Previous HEAD position was bb81100 test(visual): 375 엔티티 ...
Switched to branch 'feature/visual-dual-loop-customers-list'
```

워킹트리의 modified + untracked 파일은 branch 전환 후에도 그대로 유지됨 (git 기본 동작).

- [ ] **Step 3: 상태 재검증**

Run:
```bash
git branch --show-current
git status --short | head -25
```

Expected:
- `feature/visual-dual-loop-customers-list`
- 기존 10 modified + 다수 untracked 가 그대로 있음

- [ ] **Step 4: 판정 기록**

Task 3 는 브랜치 이동만 수행하므로 커밋 없음. Task 4 에서 워킹트리 변경을 분할 커밋한다.

---

## Task 4: web/ 10 modified + untracked 주제별 분할 커밋

**목적**: web/ 서브모듈의 `feature/visual-dual-loop-customers-list` 위에 누적된 10 modified 파일과 untracked 파일(6 generated types + `app/login/login-form.tsx` + `lib/capabilities/` + `__tests__/lib/capabilities/`) 를 주제별로 5~8 개의 atomic commit 으로 분할한다.

**Files:**
- Modify (web/): `.gitea/workflows/ci.yml`, `README.md`, `app/(admin)/admin/tenants/[id]/page.tsx`, `app/(admin)/admin/tenants/new/page.tsx`, `app/login/page.tsx`, `components/admin/permission-matrix-grid.tsx`, `components/approval/ApprovalPanel.tsx`, `lib/types/generated/gateway.ts`, `lib/types/generated/index.ts`, `next-env.d.ts`
- Create (web/): `__tests__/lib/capabilities/**`, `app/login/login-form.tsx`, `lib/capabilities/**`, `lib/types/generated/{accounting,buying,expenses,payroll,selling,stock}.ts`

- [ ] **Step 1: 각 modified 파일 diff 내용 파악**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git diff --stat
git diff .gitea/workflows/ci.yml README.md next-env.d.ts
git diff "app/(admin)/admin/tenants/[id]/page.tsx" "app/(admin)/admin/tenants/new/page.tsx" app/login/page.tsx
git diff components/admin/permission-matrix-grid.tsx components/approval/ApprovalPanel.tsx
git diff lib/types/generated/gateway.ts lib/types/generated/index.ts
```

Expected: 각 파일의 실제 변경 내용 파악. 변경이 정말로 주제별로 독립인지 확인.

- [ ] **Step 2: untracked 파일 / 디렉토리 내용 파악**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
ls -la __tests__/lib/capabilities/
ls -la lib/capabilities/
cat app/login/login-form.tsx | head -30
head -20 lib/types/generated/accounting.ts
```

Expected: 각 신규 파일의 성격 확인. generated types 는 OpenAPI codegen 산출물일 가능성 높음 (동일 포맷). `lib/capabilities/` · `__tests__/lib/capabilities/` 는 Wave 1 capability wrapper 분리 작업의 산출물일 가능성.

- [ ] **Step 3: 분할 커밋 계획 고정**

Step 1/2 의 실제 내용을 보고 다음 분류 중 적합한 것을 고른다 (예시, 실측에 따라 조정):

**제안 분할** (실측 diff 확인 후 확정):
- **커밋 A**: `feat(generated): 6 모듈 OpenAPI 타입 생성 + 기존 2 갱신` — `lib/types/generated/{accounting,buying,expenses,payroll,selling,stock,gateway,index}.ts` (8 파일)
- **커밋 B**: `feat(capabilities): Wave 1 capability wrapper + 유닛 테스트 신설` — `lib/capabilities/**`, `__tests__/lib/capabilities/**`
- **커밋 C**: `refactor(login): login-form 컴포넌트 분리` — `app/login/page.tsx` + `app/login/login-form.tsx`
- **커밋 D**: `feat(admin): tenants admin 페이지 정비` — `app/(admin)/admin/tenants/[id]/page.tsx`, `app/(admin)/admin/tenants/new/page.tsx`
- **커밋 E**: `fix(components): permission-matrix + ApprovalPanel 경계 정비` — `components/admin/permission-matrix-grid.tsx`, `components/approval/ApprovalPanel.tsx`
- **커밋 F**: `ci: .gitea/workflows/ci.yml 정비` — 단독
- **커밋 G**: `docs: web README 업데이트` — 단독
- **커밋 H**: `chore(types): next-env.d.ts 자동 갱신` — 단독

만약 Step 1 diff 에서 파일들이 서로 커플드(예: login 수정이 component 변경을 부른 것) 로 드러나면 해당 커밋을 합친다.

- [ ] **Step 4: 커밋 실행 (제안 분할 기준, 실측 조정 가능)**

각 커밋마다 `git add <files> && git commit -m "<message>"` 를 반복. 예:

```bash
# 커밋 A: generated types
git add lib/types/generated/accounting.ts lib/types/generated/buying.ts \
        lib/types/generated/expenses.ts lib/types/generated/payroll.ts \
        lib/types/generated/selling.ts lib/types/generated/stock.ts \
        lib/types/generated/gateway.ts lib/types/generated/index.ts
git commit -m "$(cat <<'EOF'
feat(generated): 6 모듈 OpenAPI 타입 생성 + 기존 2 갱신

accounting/buying/expenses/payroll/selling/stock 모듈의 openapi-typescript
산출물 추가. gateway·index 갱신. Wave 1 FE-BE 계약 동기화의 전제.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 B: capabilities
git add lib/capabilities/ __tests__/lib/capabilities/
git commit -m "$(cat <<'EOF'
feat(capabilities): Wave 1 capability wrapper + 유닛 테스트 신설

repo-structure-rules.md 의 web/lib/capabilities 규약에 따른 신규
capability 모듈과 대응 vitest 유닛 테스트.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 C: login 분리
git add app/login/page.tsx app/login/login-form.tsx
git commit -m "$(cat <<'EOF'
refactor(login): login-form 컴포넌트 분리

페이지 컴포넌트에 섞여 있던 폼 로직을 login-form.tsx 로 추출해
단위 테스트 가능한 경계로 재정렬.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 D: admin tenants
git add "app/(admin)/admin/tenants/[id]/page.tsx" \
        "app/(admin)/admin/tenants/new/page.tsx"
git commit -m "$(cat <<'EOF'
feat(admin): tenants admin 페이지 정비

멀티테넌시 관리자 UI 의 상세·신규 페이지를 Wave 1 권한 체계
반영으로 갱신.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 E: components
git add components/admin/permission-matrix-grid.tsx components/approval/ApprovalPanel.tsx
git commit -m "$(cat <<'EOF'
fix(components): permission-matrix + ApprovalPanel 경계 정비

두 컴포넌트의 prop 인터페이스와 상태 전이를 현행 capabilities 계약에
맞춘다. 기능 변경 없음.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 F: CI
git add .gitea/workflows/ci.yml
git commit -m "$(cat <<'EOF'
ci(web): .gitea/workflows/ci.yml 정비

Wave 1 FE 품질 게이트(lint · typecheck · build · playwright smoke)
실행 스텝과 캐시 구성을 현행 규약으로 정렬.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 G: README
git add README.md
git commit -m "$(cat <<'EOF'
docs(web): README 갱신

최신 개발 환경 · 테스트 실행 · 시각 이중 루프 진입점 반영.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"

# 커밋 H: next-env
git add next-env.d.ts
git commit -m "$(cat <<'EOF'
chore(types): next-env.d.ts 자동 갱신

Next.js 16 버전의 타입 재생성 산출물.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: clean 상태 검증**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git status
git log --oneline origin/main..HEAD | head -20
```

Expected:
- `nothing to commit, working tree clean`
- feature branch 위에 커밋 A~H 가 누적됨 (실행 분할에 따라 5~8 개)

---

## Task 5: web submodule pointer 갱신 + 부모 레포 커밋

**목적**: Task 3/4 를 통해 web/ 의 HEAD 가 이동하면서 부모 레포의 web submodule pointer 가 modified 상태가 된다. 이를 단일 커밋으로 반영해 clean state 확보.

**Files:**
- Modify (parent): `web` (submodule pointer)

- [ ] **Step 1: 현재 pointer 상태 확인**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git status --short | grep '^ m\|^ M web$'
git diff web
```

Expected: `m web` (submodule pointer 수정됨) · diff 에 이전 SHA → 새 SHA 이동 명시.

- [ ] **Step 2: 부모 레포 커밋**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git add web
git commit -m "$(cat <<'EOF'
chore(submodule): web 포인터 갱신 — Wave 1 FE 정리 반영

feature/visual-dual-loop-customers-list 위에 누적된 시각 이중 루프
Phase 1~4 + 전파 커밋 + 2026-04-16 세션의 주제별 분할 커밋을 부모
레포 포인터로 고정. Ralph-Loop 기동 전 clean state 확보.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 부모 레포 clean 확인**

Run:
```bash
git status
```

Expected: `nothing to commit, working tree clean`. 단 `??` 로 남아 있는 untracked (`.playwright-mcp/`) 가 Task 2 의 gitignore 처리로 사라졌는지 재확인.

**Files:**
- Create: `docs/superpowers/visual-log/2026-04-13/customers-list/before.png`
- Create: `docs/superpowers/visual-log/2026-04-13/customers-list/after.png`
- Create: `docs/superpowers/visual-log/2026-04-13/customers-list/NOTES.md`
- Modify: `web` (submodule pointer)

- [ ] **Step 1: Dev 서버 기동 상태 확인**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
pnpm --filter @oneerp/web dev &
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
```

Expected: `200` 또는 `307` (로그인 리다이렉트). 이미 기동 중이라면 그대로 사용.

- [ ] **Step 2: chrome-devtools-mcp 로 customers 리스트 접속**

ToolSearch 로 chrome-devtools-mcp 도구 로드:
- `mcp__plugin_chrome-devtools-mcp_chrome-devtools__new_page`
- `mcp__plugin_chrome-devtools-mcp_chrome-devtools__navigate_page`
- `mcp__plugin_chrome-devtools-mcp_chrome-devtools__take_screenshot`
- `mcp__plugin_chrome-devtools-mcp_chrome-devtools__list_console_messages`

접근:
```
1. new_page → URL http://localhost:3000/sales/customers
2. 로그인 리다이렉트 발생 시 demo/demo1234 입력 (UI 상 form fill)
3. customers 리스트 로드 대기
```

- [ ] **Step 3: 스크린샷 캡처 + 콘솔 점검 + 사용자 확인**

```
1. take_screenshot → 저장 경로 `docs/superpowers/visual-log/2026-04-13/customers-list/after.png`
2. list_console_messages → 에러 없음 확인
3. 사용자에게 "customers 리스트가 올바르게 렌더되는지 확인 요청" — 이 지점이 Full Autopilot 전 유일한 사용자 개입
```

사용자 confirm 수령 후 다음 Step.

- [ ] **Step 4: NOTES.md 작성**

Create `docs/superpowers/visual-log/2026-04-13/customers-list/NOTES.md`:

```markdown
# 시각 이중 루프 — customers 리스트 정상 상태

수집일: 2026-04-16
작성 세션: Ralph-Loop to GTM (M7) Pre-Loop Cleanup

## 관찰

- URL: http://localhost:3000/sales/customers
- 계정: demo / demo1234
- 상태: 정상 렌더, 콘솔 에러 없음

## 증거

- `after.png` — 정상 상태 스크린샷
- 콘솔 로그: 에러 0 건, 경고 N 건 (비차단)

## 회귀 테스트 커버리지

본 스크린샷의 회귀 방지는 `web/tests/e2e/visual/customers-list.spec.ts` 의
"customers 리스트 정상" 시나리오가 담당한다. 향후 FE 변경 시
`pnpm playwright test tests/e2e/visual/` 로 자동 재현 가능.

## 참조

- 계획: `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-list.md`
- 설계: `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md`
```

- [ ] **Step 5: 부모 레포에 증거 커밋**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git add docs/superpowers/visual-log/2026-04-13/customers-list/
git commit -m "$(cat <<'EOF'
chore(visual-log): customers 리스트 정상 상태 증거 수집

시각 이중 루프 본게임 Phase 1 Task 5 완수. chrome-devtools-mcp 로
정상 렌더 확인, 스크린샷 + NOTES 저장. 콘솔 에러 0건.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: web submodule 포인터 갱신 커밋**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git add web
git commit -m "$(cat <<'EOF'
chore(submodule): web 포인터 갱신 — visual E2E README 반영

feature/visual-dual-loop-customers-list 의 최신 HEAD 로 web 포인터 이동.
tests/e2e/visual/README.md 신규 반영 포함.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: clean 상태 재확인**

Run:
```bash
git status
```

Expected: `nothing to commit, working tree clean`.

---

## Task 5: 시각 이중 루프 Task 6 — DoD 전수 검증

**목적**: `2026-04-13-visual-dual-loop-customers-list.md` 플랜의 Definition of Done 항목을 전수 확인. HANDOFF.md 의 "다음 세션 할 일" 절 해소 선언.

**Files:** (검증만, 수정 없음)

- [ ] **Step 1: Playwright 회귀 재실행**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
PLAYWRIGHT_BASE_URL=http://localhost:3000 pnpm playwright test tests/e2e/visual/
```

Expected: `4 passed (Xs)` 또는 `5 passed` (customers-list 4 상태 + login 웜업 1).

- [ ] **Step 2: 파일 존재 검증**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
ls docs/superpowers/visual-log/2026-04-13/login/
ls docs/superpowers/visual-log/2026-04-13/customers-list/
ls web/tests/e2e/visual/README.md
ls web/tests/e2e/visual/helpers/
ls web/tests/e2e/visual/customers-list.spec.ts
```

Expected: 모든 경로 존재.

- [ ] **Step 3: 커밋 이력 검증**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git log origin/main..HEAD --oneline | head -30
cd web && git log origin/main..HEAD --oneline | head -10
```

Expected: 본 레포에 Task 3/4/5 커밋 포함 · web submodule 에 Task 3 커밋 포함.

- [ ] **Step 4: Dev 서버 종료 (선택)**

Run:
```bash
pkill -f "next dev" 2>/dev/null
```

- [ ] **Step 5: 판정 기록**

Task 5 는 검증만 수행하므로 커밋 없음. Task 6 (push) 로 직접 이동.

---

## Task 6: Push origin/main + web submodule feature branch

**목적**: 누적된 모든 커밋을 원격에 push. clean main + 원격 동기 확보.

**Files:** (push 만, 수정 없음)

- [ ] **Step 1: Dry-run 선행**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
git push --dry-run origin main
```

Expected: 거부 메시지 없음. push 대상 커밋 = 기존 26 + 설계 커밋 + 계획 커밋 + Wave 정정 커밋 + Task 2 정리 커밋들 + Task 5 pointer 커밋.

- [ ] **Step 2: main push 실행**

Run:
```bash
git push origin main
```

Expected: `To origin/main ... <old-sha>..<new-sha>  main -> main`.

- [ ] **Step 3: web submodule feature branch push**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git push --dry-run origin feature/visual-dual-loop-customers-list
git push origin feature/visual-dual-loop-customers-list
cd ..
```

Expected: `To origin/feature/visual-dual-loop-customers-list ... new branch`.

- [ ] **Step 4: 동기 상태 확인**

Run:
```bash
git rev-list --count HEAD..origin/main
git rev-list --count origin/main..HEAD
```

Expected: 둘 다 `0` (완전 동기).

- [ ] **Step 5: 판정 기록**

Task 6 는 push 만 수행하므로 커밋 없음. 다음 Task 는 제어 파일 작성.

---

## Task 7: RALPH-LOOP-PROMPT.md 작성

**목적**: 루프의 "OS 커널" 작성. 매 iteration 동일 프롬프트로 feed back 될 파일. 설계 문서의 § 3 알고리즘을 실행 가능한 자연어 + 코드로 변환.

**Files:**
- Create: `RALPH-LOOP-PROMPT.md` (레포 루트)

- [ ] **Step 1: RALPH-LOOP-PROMPT.md 작성**

Create `RALPH-LOOP-PROMPT.md`:

```markdown
# OneERP Ralph-Loop — Gate-Walker v1

> 이 파일은 `/ralph-loop:ralph-loop` 에 의해 매 이터레이션 동일하게 프롬프트로 feed back 된다.
> 설계 원본: `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md`.
> 완료 조건: `ONEERP_COMPLETE` 문자열을 출력하는 것. 이 문자열은 § 6 의 4중 체크가 **모두 true** 인 이터레이션에서만 출력 허용.

## § 0. 매 이터레이션 고정 절차 (10 단계)

순서대로 실행하라. 건너뛰기 금지.

### 1) 상태 로드

실행:
```
python3 scripts/audit/commercial_readiness.py --wave 1 --format json --write
```

산출물 `docs/generated/commercial-status.json` 을 읽는다. 이 JSON 이 276 셀(12 모듈 × 23 게이트) 의 단일 진실 공급원(SoT).

또한 `PROGRESS.md` 의 최근 5 행을 읽어 이전 iteration 기록을 파악한다.

### 2) 안전 경계 체크 (11 블로커)

다음 중 **하나라도** 감지되면 즉시 HANDOFF.md 를 § 7 포맷으로 작성하고 이터레이션을 중단한 뒤 루프를 종료한다. `ONEERP_COMPLETE` 를 출력하지 말 것.

1. **시크릿/키/토큰/인증서 생성·회전·폐기**: 이번 iter 의 작업 계획에 `SECRET_KEY`, `TOKEN`, `PRIVATE_KEY`, `.pem`, `.key`, `.crt` 등의 생성/수정이 포함되는가 → YES 면 정지.
2. **운영 리소스 삭제**: `kubectl delete`, `helm uninstall`, `docker volume rm`, `docker image rm`, 네임스페이스 제거가 필요한가 → YES 면 정지.
3. **외부 과금 액션**: `boto3`, `gcloud compute`, `terraform apply` 등이 작업 계획에 포함되는가 → YES 면 정지.
4. **라이선스/법적 변경**: `LICENSE`, `TERMS`, `PRIVACY`, `legal/` 경로 수정이 필요한가 → YES 면 정지.
5. **메인 force push / 태그 삭제 / published amend**: `git push --force`, `git tag -d`, `git commit --amend` 시도 자체 금지.
6. **동일 verify 커맨드 3회 연속 실패**: PROGRESS.md 의 최근 3 iter 가 동일 `verify` 문자열로 모두 non-zero exit 했는가 → YES 면 정지.
7. **품질 게이트 회귀 +10**: `uv run ruff check . 2>&1 | grep -c '^'` · `uv run ty check . 2>&1 | grep -c error` · `pnpm --filter @oneerp/web biome ci 2>&1 | grep -c error` 의 합이 이전 iter 대비 10 이상 증가했는가 → YES 면 정지.
8. **커밋 5회 revert/reapply 진동**: `git log --grep=Revert --since=2h --oneline | wc -l` 이 5 초과 → 정지.
9. **모듈 라벨 하락**: commercial-status.json 에서 특정 모듈의 label 이 이번 iter 후 alpha ← beta ← pre-commercial 역방향 이동 → 정지.
10. **push 실패 / upstream 충돌**: `git push --dry-run origin main` 이 비 zero exit → 정지.
11. **compose 기동 3회 실패**: `./scripts/dev/compose-up.sh` 실패가 PROGRESS.md 최근 3 iter 연속 기록되어 있음 → 정지.

### 3) 종료 판정 (4중 AND)

다음 4 체크 모두 exit 0 인가?

```bash
# 체크 1: 276/276 PASS
python3 scripts/audit/commercial_readiness.py --wave 1 --format json \
  | jq -e '.summary.passed == 276 and .summary.total == 276'

# 체크 2: 로드맵 게이트 GREEN
make verify-roadmap

# 체크 3: Wave 1 전원 commercial-ready
python3 scripts/audit/commercial_readiness.py --wave 1 --format json \
  | jq -e '.modules | all(.label == "commercial-ready")'

# 체크 4: 전체 품질 게이트 GREEN
uv run ruff format --check . && uv run ruff check . && uv run ty check . \
  && uv run pytest -m "not integration and not e2e" services/ packages/ tests/unit/ \
  && pnpm --filter @oneerp/web lint && pnpm --filter @oneerp/web typecheck && pnpm --filter @oneerp/web build
```

**모두 통과면 `ONEERP_COMPLETE` 한 줄을 출력하고 이터레이션 종료**. 하나라도 실패면 Step 4 로.

### 4) 타겟 셀 선택

선택 규칙 (위에서 아래로, 첫 매칭 셀이 타겟):

**A. 부트스트랩 층 체크** (우선순위 최상위):
```bash
bash scripts/ci/check_event_contract_drift.sh  # 없으면 FAIL 간주
uv run pytest tests/e2e/test_order_to_cash.py -q
uv run pytest tests/e2e/test_procure_to_pay.py -q
uv run pytest tests/e2e/test_payroll_accounting.py -q
uv run pytest tests/e2e/test_manufacturing_flow.py -q
```

이 중 FAIL 인 것이 하나라도 있으면 **그것이 이번 iter 의 타겟**. G1-3/G1-4/G2-* 게이트 선택 금지.

**B. 부트스트랩 모두 GREEN 이면**:
- 선행 조건 미충족 게이트 필터링:
  - `G1-5` UI: 해당 모듈의 `G1-2` 가 PASS 이어야 선택 가능
  - `G5-3` UAT: 해당 모듈의 `G5-1` 과 `G5-2` 가 PASS 이어야 선택 가능
  - `G2-2` load_test: 해당 모듈의 `G1-4` 가 PASS 이어야 선택 가능
  - `G2-1` SLO / `G2-4` chaos / `G2-5` i18n: 해당 모듈의 `G1-*` 전체 + `G4-1` 이 PASS 이어야 선택 가능
- 남은 FAIL/NOT_IMPLEMENTED 셀 중 다음 순서로 정렬:
  1. 영역 순위: `G1 < G3 < G4 < G5 < G2`
  2. 모듈 순위 (ADR-0012 Wave 1 실측): `gateway < directory < accounting < hr < payroll < selling < buying < stock < expenses < projects < crm < portal` (출처: `scripts/audit/commercial_readiness.py::WAVES_BY_MODULE[1]`)
  3. 게이트 번호 오름차순
- 정렬 후 첫 번째 셀이 타겟.

### 5) 산출물 역산

타겟이 `(module="accounting", gate="G1-2")` 이면:
- `scripts/audit/commercial_readiness.py` 의 `_gate_G1_2_openapi` 함수를 읽는다.
- 이 함수가 PASS 로 판정하기 위해 어떤 파일/상태가 필요한지 역산한다 (예: `docs/api/accounting/openapi.yaml` 또는 `.json` 존재).
- 최소 생성 산출물 목록을 정리한다.

타겟이 부트스트랩 층의 E2E (예: `test_order_to_cash.py`) 이면:
- 실패 원인을 pytest 출력에서 식별한다.
- `.planning/phases/01-event-chain-stabilization/01-01-PLAN.md` 또는 `02-core-ops-e2e/02-01-PLAN.md` 의 관련 Task 설명을 참조해 최소 수정 영역을 좁힌다.

### 6) TDD 루틴

원칙: "테스트 없는 기능은 존재할 수 없다" (OneERP 전역 규약).

1. 타겟 게이트가 통과되려면 어떤 assertion 이 성립해야 하는가? 그 assertion 을 검증하는 **failing test** 를 먼저 작성한다.
2. 해당 테스트를 실행해 실제로 실패하는지 확인한다 (false positive 방지).
3. 최소 구현(산출물 생성 / 함수 작성 / 문서 작성)을 수행한다.
4. 테스트를 재실행해 통과를 확인한다.
5. 관련된 기존 테스트가 회귀하지 않는지 간이 실행 (`pytest -q --lf` 또는 대상 영역만).

### 7) 로컬 품질 게이트

타겟 영역에 맞춰 다음 중 해당 명령만 실행하라.

- **BE 변경 (services/, packages/, core/, tests/e2e/)**:
  ```bash
  uv run ruff format --check .
  uv run ruff check .
  uv run ty check .
  uv run pytest -m "not integration and not e2e" services/ packages/ tests/unit/ -q
  ```
- **FE 변경 (web/)**:
  ```bash
  cd web && pnpm --filter @oneerp/web lint
  pnpm --filter @oneerp/web typecheck
  pnpm --filter @oneerp/web build
  cd ..
  ```
- **문서 변경 (docs/)**:
  ```bash
  make verify-roadmap
  ./scripts/docs/audit-all.sh
  ```
- **audit 스크립트 자체 변경 (scripts/audit/)**:
  ```bash
  uv run pytest scripts/audit/ -q  # 단위 테스트가 존재하면
  python3 scripts/audit/commercial_readiness.py --module <해당 모듈> --format table
  ```

하나라도 실패면 8) 로 가지 말고 원인 수정 후 재실행.

### 8) Atomic Commit

커밋 메시지 형식 (한국어):
```
<type>(<scope>): G<X>-<Y> <gate_name> PASS 달성 · <module>

<바디: 구체적 변경 내용 1~3 줄>

Refs: commercial-status.json · scripts/audit/commercial_readiness.py::_gate_G<X>_<Y>_*
Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

`<type>` 은 `feat`/`docs`/`test`/`ci`/`chore` 중 적합한 것. 한 이터레이션 = 한 커밋. 여러 파일이어도 주제가 같으면 단일 커밋.

### 9) Audit 재실행 · delta 검증

```bash
python3 scripts/audit/commercial_readiness.py --wave 1 --format json --write
```

새 JSON 을 이전 상태와 비교:
- **delta = 새 passed − 이전 passed** 가 `+1` 이어야 (타겟 셀이 PASS 로 이동).
- 만약 `< 1` 이면: 이번 iter 작업이 실제로 게이트를 통과시키지 못함. 산출물 역산 오류 → 같은 타겟을 다음 iter 에 재시도.
- 만약 `> 1` 이면: 부수 효과로 다른 셀도 PASS 됨. 기록만 하고 다음 iter.
- 회귀 (어떤 셀이 PASS → FAIL 로 이동) 발생 시 블로커 #7 또는 #9 재확인.

### 10) PROGRESS.md 갱신

PROGRESS.md 의 Iteration Log 테이블 끝에 다음 포맷으로 한 행 추가:

```markdown
| <iter_num> | <ISO8601_ts> | <module>×<gate_id> | <action 한 줄 요약> | <commit_hash_7> | +<delta>/276 | <duration_min>min |
```

또한 헤더의 "현재 진행률: <passed>/276 · <percent>%" 와 "최근 갱신: <ISO8601>" 두 라인을 갱신.

변경 직후 추가 커밋:
```bash
git add PROGRESS.md docs/generated/commercial-status.json docs/generated/commercial-status.md
git commit -m "chore(progress): iter <N> 기록 갱신 (+<delta>/276)"
```

이 커밋은 Step 8 의 기능 커밋과 **분리** (메모리 노이즈 감소).

## § 1. 불변 규칙

1. **한 이터레이션 = 한 타겟 셀** (병행 금지)
2. **테스트 없이 완료 표시 금지** (TDD 강제)
3. **모든 산출물 한국어** (코드 주석 · 커밋 메시지 · 문서)
4. **외부 라이브러리 사용 전 `context7` MCP 최신 문서 조회**
5. **배포 이미지는 `docker buildx` + `masblue-builder` · linux/amd64 단일**
6. **`deploy/catalog/` 수정 후 `uv run python -m scripts.deploy sync` 로 산출물 재생성** (직접 수정 금지)
7. **`git commit --amend`, `git reset --hard`, `git push --force` 사용 금지** (블로커 #5)
8. **`ONEERP_COMPLETE` 는 § 0.3 의 4 체크가 모두 통과한 iteration 에서만 출력 가능**

## § 2. 실패 복구 패턴

- **테스트 실패**: 실패 메시지 파싱 → 원인 식별 → 최소 수정 → 재시도. 3회 연속 실패 시 블로커 #6 으로 정지.
- **compose 기동 실패**: `docker compose logs --tail=100 <service>` 확인 → 원인(포트 충돌/볼륨 상태/Dockerfile drift) 식별 → 수정. 3회 연속 시 블로커 #11.
- **lint/format 회귀**: `uv run ruff format .` 자동 정렬 + `uv run ruff check --fix .` autofix → 남은 수동 수정.
- **ty 에러**: 타입 주석 보강. FA 규칙 (`from __future__ import annotations`) + `Annotated[T, Depends()]` 패턴 준수.
- **biome 에러**: `pnpm biome format --write` 자동 수정 + 남은 수동 수정.

## § 3. 참고 문서

- 설계: `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md`
- 구현 계획: `docs/superpowers/plans/2026-04-16-ralph-loop-to-gtm.md`
- 23 품질 기준 정본: `docs/governance/adr/0001-commercial-grade-definition.md`
- Wave 매핑: `docs/governance/adr/0012-commercialization-wave-mapping.md`
- Phase 1~7 실행 계획: `.planning/phases/0N-*/0N-01-PLAN.md`
- 자가수정 규약: `/Users/phil/.claude/CLAUDE.md` §"하네스 자율 엔지니어링"
- 전역 규약: `/Users/phil/.claude/CLAUDE.md`, `/Users/phil/WorkSpace/apps/OneErp/.claude/CLAUDE.md`, `AGENTS.md`
```

- [ ] **Step 2: 파일 존재 검증**

Run:
```bash
ls -la RALPH-LOOP-PROMPT.md
wc -l RALPH-LOOP-PROMPT.md
```

Expected: 파일 존재, 약 200~250 line.

- [ ] **Step 3: 커밋**

Run:
```bash
git add RALPH-LOOP-PROMPT.md
git commit -m "$(cat <<'EOF'
feat(ralph-loop): RALPH-LOOP-PROMPT.md 작성 — Gate-Walker v1

설계 문서(docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md)
의 § 3 이터레이션 알고리즘과 § 4 안전 경계 · 종료 판정을 실행 가능한
프롬프트로 변환. `.claude/skills/ralph-loop/SKILL.md` 가 요구하는
레포 루트 프롬프트 파일.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: PROGRESS.md 초기화

**목적**: 루프의 이터레이션 로그 파일을 비어 있는 헤더만 있는 상태로 초기화. Task 9 의 baseline audit 이후 "현재 진행률" 헤더가 채워진다.

**Files:**
- Create: `PROGRESS.md` (레포 루트)

- [ ] **Step 1: PROGRESS.md 초기 내용 작성**

Create `PROGRESS.md`:

```markdown
# OneERP Ralph-Loop PROGRESS

> 루프가 매 이터레이션 이 파일을 갱신한다. 수동 편집은 HANDOFF.md 발동 이후 복구 단계에서만 허용.
> 설계: `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md`
> 프롬프트: `RALPH-LOOP-PROMPT.md`

- 시작: <TASK_9_BASELINE_AT_KICKOFF>
- 목표: ONEERP_COMPLETE = Wave 1 × 23/23 전수 PASS (276 셀)
- 현재 진행률: <TASK_9_BASELINE_PASSED>/276 · <TASK_9_BASELINE_PERCENT>%
- 최근 갱신: <TASK_9_BASELINE_AT_KICKOFF>

## Iteration Log

| iter | ts | target | action | commit | delta | duration |
|---|---|---|---|---|---|---|

## 주의

- `delta` 컬럼 = 이 iter 에서 PASS 로 이동한 셀 수 (통상 +1).
- 헤더의 "현재 진행률" 라인은 매 iter 의 Step 10 에서 갱신된다.
- 루프가 HANDOFF.md 로 에스컬레이션하면 여기에 마지막 iter 까지의 기록이 남는다.
```

`<TASK_9_BASELINE_*>` placeholder 는 Task 9 실행 시 실제 수치로 치환.

- [ ] **Step 2: 커밋**

Run:
```bash
git add PROGRESS.md
git commit -m "$(cat <<'EOF'
feat(ralph-loop): PROGRESS.md 초기화

루프 메모리 파일의 헤더 템플릿. Baseline 수치는 Task 9 에서 채운다.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Baseline audit 실행 · commercial-status.json 생성 · PROGRESS.md baseline 치환

**목적**: 루프 시작 시점의 Wave 1 × 23 실측값을 확정. PROGRESS.md 헤더의 placeholder 를 실제 수치로 치환.

**Files:**
- Create: `docs/generated/commercial-status.json`
- Modify: `docs/generated/commercial-status.md` (자동 재생성)
- Modify: `PROGRESS.md` (placeholder 치환)

- [ ] **Step 1: Wave 1 audit 실행**

Run:
```bash
python3 scripts/audit/commercial_readiness.py --wave 1 --format json > docs/generated/commercial-status.json
python3 scripts/audit/commercial_readiness.py --wave 1 --format table
```

Expected: JSON 이 생성되고 테이블 출력에 Wave 1 12 모듈 × 23 게이트의 현재 상태가 표시됨.

(만약 `--wave` 인자를 스크립트가 지원하지 않으면: `python3 scripts/audit/commercial_readiness.py --format json --write-json docs/generated/commercial-status.json` 또는 스크립트 CLI 확장이 필요. 이 경우 이 Task 전에 audit 스크립트의 CLI 를 확장하는 선행 task 를 추가해야 함 — 본 플랜에서는 우선 현행 CLI 범위 안에서 수행 후 부족 시 `RALPH-LOOP-PROMPT.md` 의 § 0.1 에서 루프 스스로 CLI 를 확장하도록 위임.)

- [ ] **Step 2: baseline 수치 계산**

Run:
```bash
jq '.summary.passed' docs/generated/commercial-status.json 2>/dev/null || echo "manual"
jq '.summary.total' docs/generated/commercial-status.json 2>/dev/null || echo "manual"
```

Expected: 두 값 기록. `passed` · `total=276` · `percent = passed/276*100`.

만약 `--wave 1` 필터가 없어 전체 47 모듈 합계가 나오면, Wave 1 12 모듈만의 집계를 `jq '.modules[] | select(.wave == 1) | .gates | map(select(.status == "pass")) | length' | awk '{s+=$1} END {print s}'` 로 수동 계산.

- [ ] **Step 3: PROGRESS.md placeholder 치환**

편집: `PROGRESS.md` 의 4 라인을 치환.

```bash
# 예: baseline = 120/276 = 43.5%, 시각 = 2026-04-16T16:00:00Z
sed -i '' 's|<TASK_9_BASELINE_AT_KICKOFF>|2026-04-16T16:00:00Z|g' PROGRESS.md
sed -i '' 's|<TASK_9_BASELINE_PASSED>|120|g' PROGRESS.md
sed -i '' 's|<TASK_9_BASELINE_PERCENT>|43.5|g' PROGRESS.md
```

실제 수치는 Step 2 결과 반영.

- [ ] **Step 4: 커밋**

Run:
```bash
git add docs/generated/commercial-status.json docs/generated/commercial-status.md PROGRESS.md
git commit -m "$(cat <<'EOF'
chore(ralph-loop): baseline audit 수행 · PROGRESS.md baseline 치환

Wave 1 × 23 = 276 셀 중 시작 시점 PASS 개수 기록.
루프가 이후 이 baseline 을 기준으로 delta 를 계산한다.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: HANDOFF.md "Ralph-Loop 대기 중" 상태로 갱신

**목적**: 기존 HANDOFF.md (2026-04-13 시각 이중 루프 컨텍스트) 를 현재 상태(시각 이중 루프 완결 · Ralph-Loop 기동 대기) 로 덮어쓴다. 블로커 발동 시 루프가 이 파일을 다시 덮어쓸 예정.

**Files:**
- Overwrite: `HANDOFF.md`

- [ ] **Step 1: HANDOFF.md 덮어쓰기**

Overwrite `HANDOFF.md`:

```markdown
# 세션 핸드오프 — Ralph-Loop to GTM (M7) 가동 대기

작성: 2026-04-16T16:XX:XXZ
상태: Pre-Loop Cleanup 완료 · 다음 단계는 루프 기동

## 현재 상태 요약

- **부모 레포**: `main`, origin 동기 · clean working tree
- **web submodule**: `feature/visual-dual-loop-customers-list`, origin push 완료
- **core submodule**: 사용자 작업 중(`tests/fixtures/docs/arch-sample/good.md`, `tests/unit/docs/test_audit_architecture.py`) — 루프 범위 밖
- **Baseline (Wave 1 × 23)**: <PASSED>/276 (<PERCENT>%)

## 시각 이중 루프 (2026-04-13 시작 트랙) 상태

Phase 1 본게임 Task 1~6 완료. Phase 2~4 (상세 / 신규 / 반응형 · a11y) 는 M7 이후 별도 세션에서 재개.

## Ralph-Loop 기동 준비 상태

- 설계: `docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md`
- 구현 계획: `docs/superpowers/plans/2026-04-16-ralph-loop-to-gtm.md`
- 프롬프트: `RALPH-LOOP-PROMPT.md` (완성)
- 메모리: `PROGRESS.md` (baseline 기록)
- Audit SoT: `docs/generated/commercial-status.json`
- 스킬: `.claude/skills/ralph-loop/SKILL.md`

## 기동 명령

```bash
/ralph-loop:ralph-loop "$(cat RALPH-LOOP-PROMPT.md)" \
  --max-iterations 999 \
  --completion-promise "ONEERP_COMPLETE"
```

## 에스컬레이션 시 이 파일의 처분

루프가 11 하드 블로커 중 하나를 감지하면 이 파일을 에스컬레이션 포맷으로 **덮어쓴다**. 본 "가동 대기" 내용은 소실됨. 필요 시 git history (`git log HANDOFF.md`) 로 복원.

## 다음 세션의 할 일

1. 이 HANDOFF.md 가 "가동 대기" 상태인 경우: 위 기동 명령 실행.
2. 이 HANDOFF.md 가 "Ralph-Loop 자동 정지" 에스컬레이션 상태인 경우: 지시된 사용자 조치 수행 후 동일 명령 재기동.
3. `ONEERP_COMPLETE` 달성 후 상태인 경우: Post-Completion Verification 실행 (docs/superpowers/specs/2026-04-16-ralph-loop-to-gtm-design.md § 5.3).
```

`<PASSED>` · `<PERCENT>` 는 Task 9 의 baseline 수치로 치환.

- [ ] **Step 2: 커밋**

Run:
```bash
git add HANDOFF.md
git commit -m "$(cat <<'EOF'
docs(handoff): Ralph-Loop to GTM (M7) 가동 대기 상태로 갱신

시각 이중 루프 Phase 1 완결 · Pre-Loop Cleanup 6 단계 완료.
다음 단계는 /ralph-loop:ralph-loop 기동.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Kickoff 사전 상태 검증

**목적**: 루프 기동 직전 설계 문서 § 4.2 의 상태 보증 조건을 전수 확인. 하나라도 실패면 루프 기동 금지.

**Files:** (검증만)

- [ ] **Step 1: Clean main · origin 동기 확인**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
[[ -z "$(git status --porcelain)" ]] && echo "clean OK" || echo "FAIL: working tree not clean"
[[ "$(git rev-list --count HEAD..origin/main)" == "0" ]] && echo "no behind OK" || echo "FAIL: behind origin"
[[ "$(git rev-list --count origin/main..HEAD)" == "0" ]] && echo "no ahead OK" || echo "FAIL: ahead origin (push 누락)"
```

단 `m web` submodule pointer 는 Task 3~4 에서 갱신 후 Task 6 에서 push 했으므로 clean 이어야 함. 여전히 `m web` 이 남아 있다면 Task 4 Step 6 미수행 — 이 경우 Task 4 로 되돌아가 재실행.

- [ ] **Step 2: 제어 파일 존재 확인**

Run:
```bash
[[ -f RALPH-LOOP-PROMPT.md ]] && echo "prompt OK" || echo "FAIL: RALPH-LOOP-PROMPT.md 없음"
[[ -f PROGRESS.md ]] && echo "progress OK" || echo "FAIL: PROGRESS.md 없음"
[[ -f HANDOFF.md ]] && echo "handoff OK" || echo "FAIL: HANDOFF.md 없음"
[[ -f docs/generated/commercial-status.json ]] && echo "audit-json OK" || echo "FAIL: commercial-status.json 없음"
```

- [ ] **Step 3: 로드맵 게이트 GREEN 확인**

Run:
```bash
make verify-roadmap
```

Expected: exit 0, 4 게이트(status_render · link_check · forbidden_terms · stale_check) 모두 pass.

- [ ] **Step 4: 품질 게이트 BE 확인**

Run:
```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check .
```

Expected: 3개 모두 exit 0. 실패 시 원인 수정 후 단일 `ci(pre-loop): 품질 게이트 정비` 커밋 추가.

- [ ] **Step 5: 품질 게이트 FE 확인**

Run:
```bash
pnpm --filter @oneerp/web lint
pnpm --filter @oneerp/web typecheck
```

Expected: 둘 다 exit 0. 실패 시 위와 동일하게 정비 커밋 추가.

- [ ] **Step 6: 판정 기록**

6 단계 모두 OK → 다음 Task 로. 하나라도 FAIL → 해당 영역 수정 후 이 Task 재실행.

---

## Task 12: Ralph-Loop 기동

**목적**: 드디어 `/ralph-loop:ralph-loop` 를 호출해 276 셀 매트릭스 공략 루프를 기동. 이 Task 이후 모든 커밋은 루프가 담당.

**Files:** (루프가 관리)

- [ ] **Step 1: Kickoff 명령 실행**

Run:
```bash
cd /Users/phil/WorkSpace/apps/OneErp
# 플러그인 명령이 현 세션의 Claude 를 반복 주도하게 됨
# 이 명령은 브레인스토밍 → writing-plans → 본 계획의 최종 산출물
/ralph-loop:ralph-loop "$(cat RALPH-LOOP-PROMPT.md)" \
  --max-iterations 999 \
  --completion-promise "ONEERP_COMPLETE"
```

Expected: 플러그인이 setup-ralph-loop.sh 를 실행하고 세션이 루프 상태로 진입. 첫 이터레이션이 RALPH-LOOP-PROMPT.md § 0 의 10 단계 절차를 실행하기 시작.

- [ ] **Step 2: 첫 이터레이션 결과 관측**

첫 이터레이션 종료 후:
```bash
cat PROGRESS.md | tail -5
ls -la .claude/ralph-loop.local.md 2>/dev/null
```

Expected:
- PROGRESS.md 에 iteration 1 행 추가
- `.claude/ralph-loop.local.md` 에 `iteration: 1`, `started_at: <ts>`, `status: running`

만약 첫 이터레이션에서 부트스트랩 층이 FAIL (이벤트 체인 불안정) 이면 루프가 해당 영역을 공략하기 시작한다. 이것이 정상 진행.

- [ ] **Step 3: 후속 관측 프로토콜 (사용자 안내)**

이후 사용자는 다음을 주기적으로 확인:
- `cat PROGRESS.md` → 진행률 라인
- `cat .claude/ralph-loop.local.md` → iteration 번호
- 루프 정지 시 `cat HANDOFF.md` → 에스컬레이션 내용 확인

수동 중단이 필요하면:
```bash
/cancel-ralph
```

- [ ] **Step 4: 완료 대기**

`ONEERP_COMPLETE` 가 출력될 때까지 대기. 예상 소요 ≈ 414 h (17일 풀가동) · 최악 834 h.

완료 후 검증은 설계 문서 § 5.3 Post-Completion Verification 참조.

---

## 자체 리뷰 (계획 작성 후 즉시)

### 1. Spec 커버리지 체크

설계 문서 § 별로 task 매핑:

| Spec 섹션 | Task 매핑 |
|---|---|
| § 0 (왜 존재하나) | N/A (컨텍스트) |
| § 1 (6 결정) | 모든 Task 에 반영 (Full Autopilot · Gate-Walker · 정리후시작 · Claude 전담 등) |
| § 2 (아키텍처 · 제어 파일 5종) | Task 7 (PROMPT), Task 8 (PROGRESS), Task 9 (audit-json), Task 10 (HANDOFF) |
| § 3 (이터레이션 알고리즘 · 게이트 선택) | Task 7 (루프 내부 로직 전부 주입) |
| § 4 (종료 판정 · 안전 경계) | Task 7 (프롬프트 § 0.2 · 0.3) |
| § 5 (Pre-Loop Cleanup 6 단계) | Task 1~6, 10 |
| § 6 (Out of Scope) | 본 계획이 범위 침범 안 함을 Task 목록으로 확인 가능 |
| § 7 (외부 의존성) | Task 11 Step 3~5 에서 일부 사전 점검 |
| § 8 (다음 단계) | Task 12 로 종료 |

**커버리지**: 설계의 모든 실행 가능 항목이 1 개 이상의 Task 에 매핑됨. Gap 없음.

### 2. Placeholder 스캔

- `TASK_9_BASELINE_*` 는 의도적 placeholder (Task 9 에서 치환) — OK.
- `<PASSED>`, `<PERCENT>` 는 Task 10 에서 치환 — OK.
- `<iter_num>`, `<ISO8601_ts>`, `<module>×<gate_id>` 는 RALPH-LOOP-PROMPT.md 안에서 루프가 매 iter 치환할 플레이스홀더 — OK.
- `TBD`/`TODO`/`FIXME` 검색 결과 없음.

### 3. 타입 · 시그니처 일관성

- `commercial_readiness.py --wave 1 --format json` CLI 는 Task 9 Step 1 에서 "CLI 확장이 필요할 수 있음" 각주 포함 — OK.
- RALPH-LOOP-PROMPT.md 안의 함수명 (`_gate_G1_2_openapi` 등) 은 commercial_readiness.py 의 실제 함수명 (Grep 결과 기준) 과 일치 — OK.
- `ONEERP_COMPLETE` 문자열은 `.claude/skills/ralph-loop/SKILL.md` 와 RALPH-LOOP-PROMPT.md 양쪽에서 동일 — OK.

---

## 실행 핸드오프 (사용자 선택)

**Plan complete and saved to `docs/superpowers/plans/2026-04-16-ralph-loop-to-gtm.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 각 Task 마다 신선한 subagent dispatch, Task 간 review 가능, 빠른 iteration. 단 본 계획은 chrome-devtools-mcp(Task 4) 가 들어 있어 sub-agent 제약(도구 가용성)이 있을 수 있음.

**2. Inline Execution** — 본 세션에서 직접 실행, checkpoint 기반 batch 실행. chrome-devtools-mcp 사용자 확인이 단일 세션 맥락에서 일어나므로 자연스럽다.

**Task 12 이후는 실행 주체가 Ralph-Loop 플러그인으로 완전 이관됨** (본 Plan 의 범위 종료).

**어느 접근으로 진행할까요?**
