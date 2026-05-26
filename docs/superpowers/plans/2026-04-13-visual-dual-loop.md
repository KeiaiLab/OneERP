# 시각 이중 루프 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사용자(UX/톤)와 Claude(DOM/콘솔/a11y)가 각자 다른 시각 채널로 화면을 보는 하이브리드 루프를 스킬·문서·증거 저장소로 정착시키고, `app/login` 웜업 1 사이클로 작동을 검증한다.

**Architecture:** 기본 독립 모드(`chrome-devtools-mcp` Claude 전용 Chromium) + 예외 공유 모드(`claude-in-chrome` 사용자 탭 관찰) 하이브리드. 규약은 `.claude/skills/visual-dual-loop.md`로 기계 판독 형태 고정, 증거는 `docs/superpowers/visual-log/YYYY-MM-DD/<topic>/`에 append.

**Tech Stack:** Next.js 16 (`pnpm --filter @oneerp/web dev --turbopack`), chrome-devtools-mcp, claude-in-chrome, Playwright (본게임부터 사용 — 본 플랜 범위 밖).

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md`

**Scope:** 본 플랜은 워크플로 정착 + 웜업까지만 다룬다. 본게임(`(modules)/[entity]` 4상태×4시나리오, Playwright visual regression)은 **별도 플랜**으로 분리한다.

---

## 파일 구조

- **Create** `.claude/skills/visual-dual-loop.md` — 매 세션 Claude가 따를 루프 규약 (기계 판독 형식)
- **Create** `docs/superpowers/visual-log/README.md` — 증거 저장소 사용법
- **Create** `docs/superpowers/visual-log/.gitkeep` — 빈 디렉토리 유지
- **Create** `docs/superpowers/visual-log/2026-04-13/login/before.png` — 웜업 baseline 스크린샷
- **Create** `docs/superpowers/visual-log/2026-04-13/login/after.png` — 웜업 사후 스크린샷
- **Create** `docs/superpowers/visual-log/2026-04-13/login/NOTES.md` — 웜업 사이클 1줄 메모 + 콘솔 덤프
- **Modify** `AGENTS.md` — "FE 작업 시 visual-dual-loop 스킬 준수" 한 줄 규칙 추가
- **Modify** `web/app/login/page.tsx` — 웜업용 사소한 변경 (여백 또는 문구 1곳)

각 파일은 **단일 책임**: 스킬 파일=루프 규약, README=저장소 규약, NOTES.md=사이클 증거, page.tsx=파일럿 대상.

---

## Task 1: 스킬 파일 작성 (루프 규약 고정)

**Files:**
- Create: `.claude/skills/visual-dual-loop.md`

- [ ] **Step 1: 스킬 파일 작성**

내용:

````markdown
---
name: visual-dual-loop
description: OneERP web/ FE 작업 시 사용자(UX)와 Claude(DOM/콘솔/a11y)가 각자 시각 채널로 화면을 관찰하며 역할 분리된 이중 루프로 개발한다. 모든 FE 변경 이터레이션마다 적용.
---

# 시각 이중 루프 (Visual Dual Loop)

## 언제 쓰는가
OneERP `web/` 내 FE 코드를 변경할 때마다 1 사이클 전체를 적용한다.

## 역할 분리
- **사용자**: 톤/흐름/의도/감성 — Claude는 심미 판단 출력 금지
- **Claude**: DOM/콘솔/네트워크/a11y/반응형 — 사용자에게 콘솔 수동 점검 요청 금지

## 브라우저 모드
- **기본 독립 모드**: `chrome-devtools-mcp` 로 Claude 전용 Chromium 사용
- **예외 공유 모드**: `claude-in-chrome` 으로 사용자 탭 직접 관찰. 아래 3 트리거 중 하나일 때만 전환:
  1. 사용자가 "같이 봐줘"(또는 동의어) 명시
  2. 상호작용 버그 (클릭 순서/포커스/모달)
  3. Claude 검증 통과이나 사용자 화면은 달라 보일 때
  사용 종료 후 독립 모드로 복귀.

## 세션 초기화 (최초 1회)
1. dev 서버 백그라운드 기동: `pnpm --filter @oneerp/web dev` (run_in_background)
2. Claude 검증 브라우저: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__new_page` → `http://localhost:3000/<경로>`
3. 사용자에게 동일 URL을 본인 Chrome에서 열어달라고 고지

## 이터레이션 프로토콜 (1 사이클)
1. **Baseline 캡처**
   - `take_screenshot` → `docs/superpowers/visual-log/<YYYY-MM-DD>/<topic>/before-<n>.png`
   - `list_console_messages` 결과를 NOTES.md에 기록
2. **코드 Edit** (단일 목적, 최소 범위)
3. **HMR 대기 + 사후 캡처**
   - `wait_for` (적절한 signal)
   - `take_screenshot` → `after-<n>.png`
   - `list_console_messages`, `list_network_requests`
4. **3단 자가검증**
   - ① 의도한 DOM 변화 실제 발생? (`take_snapshot` → 요소/텍스트 확인)
   - ② 회귀 신호 없나? (콘솔 에러 0, 네트워크 4xx/5xx 0)
   - ③ a11y 기본선? (주요 인터랙티브 요소 role/label/focus 샘플링)
5. **사용자 보고** (한 단락):
   > "변경 완료. DOM/콘솔/a11y 자가검증 통과. 스크린샷: `<경로>`. 육안 확인 부탁."
6. **사용자 판단 수용** → OK / 수정 / "같이 봐줘" 트리거
7. **사이클 마감**: NOTES.md에 `- <n>: <1줄 메모>` append

## 충돌 규칙
Claude 검증과 사용자 판단이 충돌하면 **사용자 판단이 최종**. Claude는 가설을 바꾸고 재검증.

## 증거 저장소 규약
- 경로: `docs/superpowers/visual-log/<YYYY-MM-DD>/<topic>/`
- 필수 산출물: `before-<n>.png`, `after-<n>.png`, `NOTES.md`
- `<topic>`는 작업 대상(예: `login`, `customers-list`)

## 범위 밖
Storybook, Lighthouse CI, 피그마 동기화는 본 스킬 범위 아님.
````

- [ ] **Step 2: 파일 존재 확인**

Run: `ls -la .claude/skills/visual-dual-loop.md`
Expected: 파일 존재, 크기 > 0

- [ ] **Step 3: 커밋**

```bash
git add .claude/skills/visual-dual-loop.md
git commit -m "feat(skill): 시각 이중 루프 스킬 규약 추가

사용자(UX)와 Claude(DOM/콘솔/a11y) 역할 분리 1 사이클 프로토콜,
독립/공유 모드 전환 트리거 3종, 증거 저장소 규약 고정."
```

---

## Task 2: 증거 저장소 초기화

**Files:**
- Create: `docs/superpowers/visual-log/README.md`
- Create: `docs/superpowers/visual-log/.gitkeep`

- [ ] **Step 1: README 작성**

내용:

````markdown
# visual-log — 시각 이중 루프 증거 저장소

`visual-dual-loop` 스킬이 남기는 before/after 스크린샷과 NOTES를 보관한다.

## 디렉토리 규약

```
visual-log/
└── <YYYY-MM-DD>/
    └── <topic>/
        ├── before-1.png
        ├── after-1.png
        ├── before-2.png
        ├── after-2.png
        └── NOTES.md
```

## NOTES.md 형식

```markdown
# <topic> — <YYYY-MM-DD>

## 사이클

- 1: <한 줄 메모. 무엇을 왜 바꿨는지>
- 2: ...

## 콘솔/네트워크 샘플

(필요 시 인용)
```

## 수명

90일 경과한 날짜 디렉토리는 아카이브 대상. 수동 또는 별도 스크립트로 처리.

## 범위

본 저장소는 **증거**만 담는다. 회귀 테스트(Playwright visual regression)는 `web/tests/e2e/visual/` 에 별도 보관한다.
````

- [ ] **Step 2: .gitkeep 생성**

```bash
touch docs/superpowers/visual-log/.gitkeep
```

- [ ] **Step 3: 커밋**

```bash
git add docs/superpowers/visual-log/README.md docs/superpowers/visual-log/.gitkeep
git commit -m "feat(visual-log): 시각 이중 루프 증거 저장소 초기화"
```

---

## Task 3: AGENTS.md에 규칙 1줄 추가

**Files:**
- Modify: `AGENTS.md` (상단 운영 규칙 목록에 추가)

- [ ] **Step 1: 추가 위치 확인**

Run: `head -30 AGENTS.md`
Expected: "단일 소스 오브 트루스(SoT)" 섹션 또는 운영 규칙이 보임. 적절한 기존 규칙 섹션 하단을 수정 지점으로 선택.

- [ ] **Step 2: 규칙 라인 추가**

`AGENTS.md`의 "단일 소스 오브 트루스(SoT)" 섹션 직후 또는 최상위 규칙 블록 끝에 다음 문단 삽입:

```markdown
## FE 작업 규칙

- `web/` 내 FE 코드 변경 시 `.claude/skills/visual-dual-loop.md` 스킬을 준수한다. 모든 이터레이션은 before/after 스크린샷과 콘솔 점검 증거를 `docs/superpowers/visual-log/`에 남긴다.
```

- [ ] **Step 3: 커밋**

```bash
git add AGENTS.md
git commit -m "docs(agents): FE 작업 시 visual-dual-loop 준수 규칙 추가"
```

---

## Task 4: 웜업 — dev 서버 기동 및 baseline 캡처

**Files:**
- Create: `docs/superpowers/visual-log/2026-04-13/login/NOTES.md`
- Create: `docs/superpowers/visual-log/2026-04-13/login/before-1.png`

- [ ] **Step 1: dev 서버 백그라운드 기동**

```bash
cd /Users/phil/WorkSpace/apps/OneErp && pnpm --filter @oneerp/web dev
```
(Bash `run_in_background: true`로 실행)

- [ ] **Step 2: 서버 준비 확인**

Run: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login`
Expected: `200` (또는 Next.js dev의 HTML 렌더 상태)

- [ ] **Step 3: Claude 검증 브라우저 오픈**

Use: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__new_page` with `url: "http://localhost:3000/login"`
(스키마가 아직 로드되지 않았다면 먼저 `ToolSearch`로 select)
Expected: 새 페이지 생성됨, 에러 없음

- [ ] **Step 4: 사용자 동기화 안내**

사용자에게 1줄 메시지:
> "본인 Chrome에서 `http://localhost:3000/login` 열어주세요. baseline 캡처합니다."

- [ ] **Step 5: Baseline 스크린샷 저장**

Use: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__take_screenshot`
저장: `docs/superpowers/visual-log/2026-04-13/login/before-1.png`

- [ ] **Step 6: 콘솔 baseline 캡처 + NOTES.md 초기화**

Use: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__list_console_messages`

`NOTES.md` 내용:

```markdown
# login — 2026-04-13

## 사이클

- 1: baseline 캡처 (코드 변경 전)

## 콘솔/네트워크 샘플

### Baseline (before-1)
<list_console_messages 결과 요약 — 에러/경고 건수 기록>
```

- [ ] **Step 7: 커밋**

```bash
git add docs/superpowers/visual-log/2026-04-13/login/
git commit -m "chore(visual-log): login 웜업 baseline 캡처"
```

---

## Task 5: 웜업 — 사소한 변경 + 사후 검증 + 보고

**Files:**
- Modify: `web/app/login/page.tsx` (여백 또는 문구 1곳)
- Create: `docs/superpowers/visual-log/2026-04-13/login/after-1.png`
- Modify: `docs/superpowers/visual-log/2026-04-13/login/NOTES.md`

- [ ] **Step 1: 대상 라인 식별**

Run: `Read web/app/login/page.tsx`
Expected: 로그인 페이지 JSX가 보임. 사소한 변경 지점 1곳 선택 (예: 타이틀 상단 여백 클래스, 또는 헤더 문구 공백 정리).

- [ ] **Step 2: Edit 수행**

`web/app/login/page.tsx` 내에서 선택한 한 줄만 변경.
예시 (실제 파일 내용 확인 후 실제 문자열로 치환하여 Edit 호출):
- old: `className="mt-4"` → new: `className="mt-6"`
또는
- old: `<h1>로그인</h1>` → new: `<h1>로그인 </h1>`와 같이 공백 정리

**제약**: 기능 변경 금지, 시각 차이가 스크린샷으로 구분 가능한 정도만.

- [ ] **Step 3: HMR 반영 대기**

Use: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__wait_for` with appropriate text/selector signal.
대안: 1~2초 체감 후 다음 단계로 진행하되, 3단계에서 이미지가 동일해 보이면 재대기.

- [ ] **Step 4: 사후 스크린샷 + 콘솔/네트워크**

Use:
- `take_screenshot` → `docs/superpowers/visual-log/2026-04-13/login/after-1.png`
- `list_console_messages`
- `list_network_requests`

- [ ] **Step 5: 3단 자가검증**

1. `take_snapshot` 으로 변경된 요소의 텍스트/클래스 확인 — 의도대로 바뀌었는지
2. 콘솔 에러 개수 = 0 확인, 네트워크 4xx/5xx = 0 확인
3. 변경 요소 주변 인터랙티브 요소(로그인 버튼 등)가 여전히 role/label 존재하고 focusable 한지 샘플 확인

**Fail이면**: Edit 재시도 또는 rollback. Pass일 때만 다음 단계.

- [ ] **Step 6: NOTES.md 갱신**

append:

```markdown
- 2: <변경 요약 한 줄. 예: "login 타이틀 여백 mt-4→mt-6">

### After (after-1)
- DOM 검증: 의도 변화 확인 (<요소> <클래스/텍스트>)
- 콘솔: 에러 0 / 경고 <n>
- 네트워크: 4xx/5xx 0
- a11y: 로그인 버튼 role="button", focus 가능 확인
```

- [ ] **Step 7: 사용자 보고**

한 단락:
> "변경 완료: `web/app/login/page.tsx` 의 `<변경 요약>`. DOM/콘솔/a11y 자가검증 통과. 스크린샷: `docs/superpowers/visual-log/2026-04-13/login/after-1.png`. 본인 Chrome 리로드 후 육안 확인 부탁합니다."

- [ ] **Step 8: 커밋**

```bash
git add web/app/login/page.tsx docs/superpowers/visual-log/2026-04-13/login/
git commit -m "chore(web/login): 웜업 사이클 1 — 사소한 시각 변경 + 증거"
```

---

## Task 6: 웜업 — 공유 모드 왕복 1회 연습

**Files:**
- Modify: `docs/superpowers/visual-log/2026-04-13/login/NOTES.md`

- [ ] **Step 1: 사용자에게 트리거 연습 고지**

> "공유 모드 왕복 연습입니다. '같이 봐줘' 라고 말씀해주세요. 이후 Claude가 사용자 탭을 직접 관찰한 뒤 독립 모드로 복귀합니다."

- [ ] **Step 2: 사용자 '같이 봐줘' 수신 대기**

사용자 발화 수신 후 진행. (자동화 아님 — 사용자 명시 트리거)

- [ ] **Step 3: 공유 모드 전환**

Use: `mcp__claude-in-chrome__tabs_context_mcp` (스키마 미로드 시 ToolSearch 선행) 으로 사용자 탭 목록 확보
→ `localhost:3000/login` 탭 식별
→ `mcp__claude-in-chrome__read_page` 또는 동등 도구로 사용자 화면 상태 1회 관찰

- [ ] **Step 4: 관찰 결과 사용자에게 1줄 요약**

> "사용자 탭에서 `<관찰된 상태 한 줄>` 확인. 독립 모드로 복귀합니다."

- [ ] **Step 5: NOTES.md 갱신**

append:

```markdown
- 3: 공유 모드 왕복 연습 — 사용자 '같이 봐줘' 트리거 → claude-in-chrome 관찰 → 복귀. 성공.
```

- [ ] **Step 6: 커밋**

```bash
git add docs/superpowers/visual-log/2026-04-13/login/NOTES.md
git commit -m "chore(visual-log): login 웜업 공유 모드 왕복 1회 기록"
```

---

## Task 7: 웜업 DoD 검증 + 본게임 플랜 예고

**Files:** (수정 없음 — 검증만)

- [ ] **Step 1: DoD 체크**

Run:
```bash
ls docs/superpowers/visual-log/2026-04-13/login/
```
Expected: `before-1.png`, `after-1.png`, `NOTES.md` 3개 모두 존재.

Run:
```bash
grep -c "^- [0-9]:" docs/superpowers/visual-log/2026-04-13/login/NOTES.md
```
Expected: `>= 3` (baseline, after, 공유모드)

Run:
```bash
git log --oneline -n 6
```
Expected: Task 1~6 커밋 6개 모두 존재.

- [ ] **Step 2: 사용자 보고 + 본게임 예고**

한 단락:
> "웜업 DoD 충족: before/after 스크린샷 쌍 + NOTES 3 사이클 기록 + 공유 모드 왕복 완료. 이어서 본게임 (`app/(modules)/[entity]` 4상태×4시나리오) 플랜을 별도로 작성하겠습니다. 진행할까요?"

- [ ] **Step 3 (선택): 사용자 승인 시** — 본 플랜 종료, 본게임 플랜을 `docs/superpowers/plans/2026-04-XX-visual-dual-loop-entity.md` 로 신규 작성 (본 플랜 범위 밖)

---

## 자가검토 (플랜 작성 후)

**Spec coverage:**
- ✅ §2 아키텍처 → Task 4 (dev 서버, 독립/공유 브라우저 모드)
- ✅ §3 이터레이션 프로토콜 → Task 1 스킬 파일에 기계 판독 형태로 고정 + Task 5가 실행 예시
- ✅ §4 파일럿 웜업 → Task 4~7
- ✅ §4 본게임 → 명시적 범위 밖, Task 7에서 후속 플랜 예고
- ✅ §5 산출물 → 스킬(Task 1), visual-log(Task 2), AGENTS.md(Task 3), 웜업 증거(Task 4~6)
- ✅ §6 성공 기준 워크플로 수준 → Task 1 스킬 파일 작성으로 재현 가능
- ✅ §6 성공 기준 파일럿 수준 → Task 7 DoD 체크
- ✅ §7 열린 이슈 3건 → 웜업 실행 중 결정되도록 남겨둠 (플랜에 강제 결정 넣지 않음)

**Placeholder scan:** TBD/TODO 없음. "사소한 변경"은 Task 5 Step 1~2에서 **실제 파일을 읽고 구체 문자열로 치환**하라는 지시가 명시됨.

**Type consistency:** 파일 경로, 날짜(2026-04-13), topic 이름(login)이 Task 2~7 전체에서 일관.

---

## 실행 인계

플랜이 `docs/superpowers/plans/2026-04-13-visual-dual-loop.md`에 저장되었습니다. 실행 방식을 골라주세요:

1. **Subagent-Driven (권장)** — 태스크마다 새 서브에이전트 디스패치, 태스크 간 리뷰, 빠른 반복
2. **Inline Execution** — 현재 세션에서 `executing-plans` 스킬로 체크포인트 배치 실행

어느 쪽으로 가시겠어요?
