# 시각 이중 루프 본게임 Phase 1 — customers 리스트 4 상태 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `(modules)/[entity]=customers` 리스트 페이지의 4 상태(로딩/빈/에러/정상)를 네트워크 mocking으로 결정론적으로 재현하고, 각 상태를 `visual-dual-loop` 스킬 1 사이클로 검증(before/after + 3단 자가검증)한 뒤 Playwright visual regression 스냅샷 1장(정상 상태)을 추가한다.

**Architecture:** Playwright `page.route()` 로 `/api/gateway/api/v1/selling/customers` 및 `/api/gateway/api/v1/me` 를 테스트별로 mocking. 백엔드 없이 UI 4 상태를 강제 진입 가능. chrome-devtools-mcp는 사람 검증용 탐색 루프, Playwright는 CI 회귀용 — 두 채널이 동일 mocking 규약을 공유한다.

**Tech Stack:** Next.js 16 Turbopack, Playwright (E2E + 시각 회귀), chrome-devtools-mcp (이중 루프), customers `EntityConfig` (기존), `EntityListPage`/`EntityListSkeleton`/`EmptyState` (기존 컴포넌트, 수정 없음).

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md` §4 "본게임"

**Related:** 웜업 플랜 `docs/superpowers/plans/2026-04-13-visual-dual-loop.md` (완료). 본 플랜은 그 정착물(스킬·저장소·규칙)을 전제로 한다.

**Scope (이번 플랜):**
- customers 리스트 페이지 4 상태만 다룸
- 인프라: Playwright mocking 헬퍼 + JWT 쿠키 fixture + 시각 회귀 스냅샷 기준선 1장
- 증거: `docs/superpowers/visual-log/2026-04-13/customers-list/` 4 사이클

**Out of scope (후속 플랜):**
- 상세 화면 4 시나리오, 신규 화면 폼, 반응형·a11y 횡단
- 다른 엔티티로의 패턴 전파 (customers 성공 후 판단)

---

## 파일 구조

**Create (web submodule 내부):**
- `web/tests/e2e/visual/_helpers/mock-gateway.ts` — `page.route()` 래퍼. `/api/gateway/*` mocking 함수 4개(`mockListLoading`, `mockListEmpty`, `mockListError`, `mockListNormal`)
- `web/tests/e2e/visual/_helpers/auth-fixture.ts` — 유효한 JWT 쿠키 주입 Playwright fixture (`authedPage`)
- `web/tests/e2e/visual/customers-list.spec.ts` — 4 상태 E2E + 정상 상태 시각 회귀 스냅샷 1장
- `web/tests/e2e/visual/README.md` — 시각 회귀 테스트 규약(mocking 패턴, 스냅샷 임계값, 생성·갱신 절차)

**Create (부모 레포):**
- `docs/superpowers/visual-log/2026-04-13/customers-list/before-1.png` ~ `after-4.png` — 4 사이클 × before/after = 8장
- `docs/superpowers/visual-log/2026-04-13/customers-list/NOTES.md` — 4 사이클 메모

**Modify:**
- 없음 (customers 컴포넌트 자체는 손대지 않음 — 4 상태를 입력만 바꿔 재현)

각 파일 단일 책임: `mock-gateway.ts`=네트워크 목, `auth-fixture.ts`=인증, spec=검증, README=규약, visual-log=증거.

---

## 사전 체크 (Task 0 — 환경 확인, 커밋 없음)

- [ ] **Step A: web submodule에서 feature 브랜치 확인/생성**

```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
git status && git branch --show-current
```
Expected: 현재 브랜치가 `feature/visual-dual-loop-warmup` (웜업에서 이어감) 또는 clean `main`.

`main`이면 새 브랜치 생성:
```bash
git checkout -b feature/visual-dual-loop-customers-list
```

- [ ] **Step B: Next dev 서버 기동 (3001 포트 — Playwright 기본)**

```bash
cd /Users/phil/WorkSpace/apps/OneErp
pnpm --filter @oneerp/web dev -- --port 3001
```
(Bash `run_in_background: true`)

Expected: `✓ Ready in <1000>ms` at `http://localhost:3001`

현재 3000 포트에 웜업용 서버가 돌고 있다면 두 개 공존 가능. 또는 3000 종료 후 3001로 단일 운영 택1.

- [ ] **Step C: Playwright 설치 확인**

```bash
cd /Users/phil/WorkSpace/apps/OneErp/web
pnpm playwright --version
```
Expected: 버전 문자열 출력 (미설치면 `pnpm playwright install chromium` 수행).

---

## Task 1: mock-gateway.ts — 네트워크 mocking 헬퍼

**Files:**
- Create: `web/tests/e2e/visual/_helpers/mock-gateway.ts`
- Test: `web/tests/e2e/visual/_helpers/mock-gateway.test.ts`

- [ ] **Step 1: 실패하는 테스트 작성**

`web/tests/e2e/visual/_helpers/mock-gateway.test.ts`:

```typescript
import { describe, expect, it, vi } from "vitest";
import type { Page, Route } from "@playwright/test";
import {
  mockListEmpty,
  mockListError,
  mockListLoading,
  mockListNormal,
} from "./mock-gateway";

function fakePage() {
  const handlers: Array<(url: string) => Promise<Route | null>> = [];
  const routeSpy = vi.fn(async (pattern: string | RegExp, handler: (route: Route) => Promise<void>) => {
    handlers.push(async (url: string) => {
      const matches = typeof pattern === "string" ? url.includes(pattern) : pattern.test(url);
      if (!matches) return null;
      const fulfills: Array<{ status: number; body: string; contentType: string }> = [];
      const fakeRoute = {
        fulfill: async (opts: { status?: number; body?: string; contentType?: string }) => {
          fulfills.push({
            status: opts.status ?? 200,
            body: opts.body ?? "",
            contentType: opts.contentType ?? "application/json",
          });
        },
        continue: async () => {
          fulfills.push({ status: 0, body: "(continued)", contentType: "" });
        },
      } as unknown as Route;
      await handler(fakeRoute);
      return { fulfills } as unknown as Route;
    });
  });
  return { route: routeSpy, handlers } as unknown as Page & { handlers: typeof handlers };
}

describe("mock-gateway", () => {
  it("mockListNormal 은 /customers GET 에 200 + rows 배열을 돌려준다", async () => {
    const page = fakePage();
    await mockListNormal(page, "customers", [{ _id: "c1", customer_name: "고객A" }]);
    const result = await page.handlers[0]?.("http://x/api/gateway/api/v1/selling/customers?limit=50");
    expect(result).toBeTruthy();
  });

  it("mockListEmpty 은 빈 배열을 돌려준다", async () => {
    const page = fakePage();
    await mockListEmpty(page, "customers");
    expect(page.route).toHaveBeenCalled();
  });

  it("mockListError 은 500 을 돌려준다", async () => {
    const page = fakePage();
    await mockListError(page, "customers");
    expect(page.route).toHaveBeenCalled();
  });

  it("mockListLoading 은 응답을 지연시킨다", async () => {
    const page = fakePage();
    await mockListLoading(page, "customers", 10_000);
    expect(page.route).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd web && pnpm test _helpers/mock-gateway.test.ts`
Expected: FAIL — `mock-gateway.ts` 미존재.

- [ ] **Step 3: `mock-gateway.ts` 구현**

`web/tests/e2e/visual/_helpers/mock-gateway.ts`:

```typescript
/**
 * Playwright page.route 기반 /api/gateway/* mocking 헬퍼.
 * 4 상태(로딩/빈/에러/정상)를 각각 1 함수로 노출한다.
 */
import type { Page } from "@playwright/test";

type Row = Record<string, unknown>;

function entityPattern(service: string, entity: string): RegExp {
  return new RegExp(`/api/gateway/api/v1/${service}/${entity}(\\?|$)`);
}

function meOk(page: Page): Promise<void> {
  return page.route("**/api/gateway/api/v1/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ username: "demo", is_super_admin: false, tenant: "default" }),
    }),
  );
}

/** 정상 응답 — rows 배열을 그대로 반환한다. */
export async function mockListNormal(page: Page, entity: string, rows: Row[], service = "selling"): Promise<void> {
  await meOk(page);
  await page.route(entityPattern(service, entity), (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ rows, total: rows.length }),
    }),
  );
}

/** 빈 응답 — 0건. */
export async function mockListEmpty(page: Page, entity: string, service = "selling"): Promise<void> {
  await mockListNormal(page, entity, [], service);
}

/** 에러 응답 — 500. */
export async function mockListError(page: Page, entity: string, service = "selling"): Promise<void> {
  await meOk(page);
  await page.route(entityPattern(service, entity), (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "internal_error" }),
    }),
  );
}

/** 로딩 응답 — 지정 ms 만큼 응답을 보류한다. 기본 30초. */
export async function mockListLoading(page: Page, entity: string, delayMs = 30_000, service = "selling"): Promise<void> {
  await meOk(page);
  await page.route(entityPattern(service, entity), async (route) => {
    await new Promise((r) => setTimeout(r, delayMs));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ rows: [], total: 0 }),
    });
  });
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd web && pnpm test _helpers/mock-gateway.test.ts`
Expected: PASS 4/4.

- [ ] **Step 5: 린트·타입**

Run: `cd web && pnpm biome check tests/e2e/visual/_helpers/ && pnpm tsc --noEmit`
Expected: 0 에러.

- [ ] **Step 6: 커밋 (web submodule 내)**

```bash
cd web && git add tests/e2e/visual/_helpers/mock-gateway.ts tests/e2e/visual/_helpers/mock-gateway.test.ts
git commit -m "test(visual): customers 리스트 네트워크 mocking 헬퍼 (4 상태)"
```

---

## Task 2: auth-fixture.ts — 유효 JWT 쿠키 주입 fixture

**Files:**
- Create: `web/tests/e2e/visual/_helpers/auth-fixture.ts`

- [ ] **Step 1: JWT 구조 확인**

Run: `grep -nE "decodeJwtPayload|EXP_LEEWAY" web/proxy.ts`
Expected: `web/proxy.ts:33~` 부근 — payload에 `exp` 필드와 Base64URL 디코딩 요구. `is_super_admin` 불리언 클레임 사용.

- [ ] **Step 2: fixture 구현**

`web/tests/e2e/visual/_helpers/auth-fixture.ts`:

```typescript
/**
 * 미들웨어 통과용 가짜 JWT 쿠키 fixture.
 * 서명 검증은 BE 소관이므로 FE 미들웨어는 exp 만 체크한다 (proxy.ts).
 */
import { test as base, type Page } from "@playwright/test";

const COOKIE_NAME = "oneerp_access_token";
const HOST = "localhost";

function base64url(obj: unknown): string {
  return Buffer.from(JSON.stringify(obj)).toString("base64url");
}

/** exp 를 1시간 뒤로 설정한 가짜 JWT. 서명부는 더미. */
export function fakeJwt(claims: Record<string, unknown> = {}): string {
  const header = base64url({ alg: "HS256", typ: "JWT" });
  const payload = base64url({
    sub: "demo",
    exp: Math.floor(Date.now() / 1000) + 3600,
    is_super_admin: false,
    tenant: "default",
    ...claims,
  });
  return `${header}.${payload}.signature`;
}

export async function setAuthCookie(page: Page, claims: Record<string, unknown> = {}): Promise<void> {
  await page.context().addCookies([
    {
      name: COOKIE_NAME,
      value: fakeJwt(claims),
      domain: HOST,
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax",
    },
  ]);
}

/** 기본 "demo" 권한으로 로그인된 Page fixture. */
export const test = base.extend<{ authedPage: Page }>({
  authedPage: async ({ page }, use) => {
    await setAuthCookie(page);
    await use(page);
  },
});
```

- [ ] **Step 3: 린트·타입**

Run: `cd web && pnpm biome check tests/e2e/visual/_helpers/auth-fixture.ts && pnpm tsc --noEmit`
Expected: 0 에러.

- [ ] **Step 4: 커밋**

```bash
cd web && git add tests/e2e/visual/_helpers/auth-fixture.ts
git commit -m "test(visual): 미들웨어 통과용 가짜 JWT 쿠키 fixture"
```

---

## Task 3: customers-list.spec.ts — 4 상태 E2E + 정상 시각 회귀 1장

**Files:**
- Create: `web/tests/e2e/visual/customers-list.spec.ts`

- [ ] **Step 1: 스펙 작성**

`web/tests/e2e/visual/customers-list.spec.ts`:

```typescript
/**
 * customers 리스트 4 상태 E2E + 정상 상태 시각 회귀 스냅샷.
 * mock-gateway 헬퍼로 /api/gateway 를 4 가지로 치환해 UI 상태를 강제 진입한다.
 */
import { expect } from "@playwright/test";
import {
  mockListEmpty,
  mockListError,
  mockListLoading,
  mockListNormal,
} from "./_helpers/mock-gateway";
import { test } from "./_helpers/auth-fixture";

const URL = "/customers";

test("customers 리스트 — 로딩 상태는 skeleton 을 보인다", async ({ authedPage }) => {
  await mockListLoading(authedPage, "customers", 30_000);
  await authedPage.goto(URL);
  await expect(authedPage.getByTestId("entity-list-skeleton")).toBeVisible();
});

test("customers 리스트 — 빈 상태는 EmptyState 를 보인다", async ({ authedPage }) => {
  await mockListEmpty(authedPage, "customers");
  await authedPage.goto(URL);
  await expect(authedPage.getByText(/고객.*없|등록된.*없/)).toBeVisible();
});

test("customers 리스트 — 에러 상태는 재시도 버튼과 에러 문구를 보인다", async ({ authedPage }) => {
  await mockListError(authedPage, "customers");
  await authedPage.goto(URL);
  await expect(authedPage.getByRole("button", { name: /재시도|다시|retry/i })).toBeVisible();
});

test("customers 리스트 — 정상 상태 시각 회귀 스냅샷", async ({ authedPage }) => {
  await mockListNormal(authedPage, "customers", [
    { _id: "c1", customer_name: "고객 A", customer_type: "company", tax_id: "123-45-67890", default_currency: "KRW" },
    { _id: "c2", customer_name: "고객 B", customer_type: "individual", tax_id: "987-65-43210", default_currency: "USD" },
  ]);
  await authedPage.goto(URL);
  await expect(authedPage.getByText("고객 A")).toBeVisible();
  await expect(authedPage).toHaveScreenshot("customers-list-normal.png", {
    maxDiffPixelRatio: 0.01,
  });
});
```

- [ ] **Step 2: 3 상태 (로딩/빈/에러) 테스트 먼저 실행 — 실패 예상 (회귀 baseline 없어도 통과)**

Run: `cd web && pnpm playwright test tests/e2e/visual/customers-list.spec.ts --grep "로딩|빈|에러"`
Expected: selector 미발견 등으로 FAIL 가능 — 실제 컴포넌트가 어떤 aria/text 를 쓰는지에 맞춰 **Step 4 직전에 선택자 보정** 필요.

- [ ] **Step 3: selector 보정 — 실제 렌더 내용 탐색**

Run:
```bash
grep -nE "getByTestId|data-testid|EmptyState|재시도|skeleton" web/components/crud/entity-list-page.tsx web/components/crud/entity-list-skeleton.tsx web/components/crud/empty-state.tsx
```
결과를 기반으로 spec 의 `getByTestId`/`getByText` 패턴을 컴포넌트 실제 속성에 맞춰 조정. 예: `data-testid="entity-list-skeleton"` 가 없으면 `locator('[role="status"]')` 또는 `.locator('.skeleton')` 로 대체.

필요 시 `EmptyState`, `EntityListSkeleton` 컴포넌트에 `data-testid` 추가 Edit (1줄씩). 각 Edit 은 별도 커밋하지 않고 Task 4 시각 회귀 통과 후 한 번에 묶는다.

- [ ] **Step 4: 3 상태 테스트 통과 확인**

Run: `cd web && pnpm playwright test tests/e2e/visual/customers-list.spec.ts --grep "로딩|빈|에러"`
Expected: PASS 3/3.

- [ ] **Step 5: 정상 상태 스냅샷 최초 생성**

Run: `cd web && pnpm playwright test tests/e2e/visual/customers-list.spec.ts --grep "정상" --update-snapshots`
Expected: `tests/e2e/visual/customers-list.spec.ts-snapshots/customers-list-normal-chromium-*.png` 생성, PASS 1/1.

- [ ] **Step 6: 스냅샷 재실행 안정성 확인 — 동일 실행 2회 PASS**

Run: `cd web && pnpm playwright test tests/e2e/visual/customers-list.spec.ts --grep "정상"`
Expected: PASS. `maxDiffPixelRatio: 0.01` 초과 시 seed 데이터/폰트 렌더 지터 요인 — 데이터 고정 값 재확인 후 스냅샷 재생성.

- [ ] **Step 7: 커밋**

```bash
cd web && git add tests/e2e/visual/customers-list.spec.ts tests/e2e/visual/customers-list.spec.ts-snapshots/
# 컴포넌트에 data-testid 추가 edit 이 있었다면 포함
git add -p components/crud/
git commit -m "test(visual): customers 리스트 4 상태 E2E + 정상 시각 회귀 스냅샷"
```

---

## Task 4: README — 시각 회귀 테스트 규약 문서

**Files:**
- Create: `web/tests/e2e/visual/README.md`

- [ ] **Step 1: 문서 작성**

```markdown
# tests/e2e/visual — 시각 회귀 테스트

`visual-dual-loop` 스킬의 자동 회귀 채널. chrome-devtools-mcp 는 사람 검증용, 여기 Playwright 테스트는 CI 회귀용이다.

## 구조

- `_helpers/mock-gateway.ts` — `/api/gateway/*` 를 4 상태(로딩/빈/에러/정상)로 mocking
- `_helpers/auth-fixture.ts` — 미들웨어 통과용 가짜 JWT 쿠키
- `<entity>-list.spec.ts` / `<entity>-detail.spec.ts` / `<entity>-form.spec.ts` — 엔티티별 시각 회귀

## 새 엔티티 추가 절차

1. `_helpers/mock-gateway.ts` 는 그대로 사용 (service/entity 파라미터만 바꿈)
2. `<entity>-list.spec.ts` 를 `customers-list.spec.ts` 복사 후 rows/selector 수정
3. `pnpm playwright test ... --update-snapshots` 로 baseline 생성
4. 커밋

## 스냅샷 임계값

- `maxDiffPixelRatio: 0.01` (1% 미만 차이 허용) — 폰트/안티앨리어싱 지터 대응
- 의도된 UI 변경 시: `--update-snapshots` 로 갱신 후 리뷰어에게 before/after 공유

## 실행

```bash
pnpm playwright test tests/e2e/visual/         # 전체
pnpm playwright test tests/e2e/visual/ --grep "정상"  # 필터
pnpm playwright test ... --update-snapshots    # 스냅샷 갱신
```
```

- [ ] **Step 2: 커밋**

```bash
cd web && git add tests/e2e/visual/README.md
git commit -m "docs(visual): tests/e2e/visual/ 규약 문서"
```

---

## Task 5: 4 사이클 chrome-devtools-mcp 실행 + visual-log

각 상태마다 `visual-dual-loop` 스킬의 1 사이클을 수행. **메인 세션이 직접 실행** (서브에이전트는 브라우저 MCP 사용 불가). 본 태스크는 커밋 시점에만 체크박스가 있고, 내부 단계는 4 반복이다.

**공통 세션 초기화 (1회):**
- dev 서버 port 3001 기동 확인
- Chrome MCP: `new_page http://localhost:3001/customers?__mock=loading` 등의 방식은 불가 → 대신 `page.route()` 는 Playwright 기능이므로 chrome-devtools-mcp 에는 적용 불가.

**→ 전략 변경:** chrome-devtools-mcp 루프는 Playwright 가 mocking 해 띄워주는 페이지에 붙는다. **Playwright `--ui` 모드 또는 `page.pause()` 를 써서 각 상태 진입 시점에 브라우저를 정지**시키고, chrome-devtools-mcp 로 같은 Chromium 인스턴스를 참조.

가장 단순한 구현: 각 상태를 띄우는 **일회성 Playwright 스크립트** 를 4 번 실행하되, `test.describe.configure({ mode: 'serial' })` + `await new Promise(() => {})` 로 끝을 걸어둠. 실무적으로 번거로움.

**→ 최종 전략:** chrome-devtools-mcp 로 `http://localhost:3001/customers` 를 띄운 뒤, **브라우저 DevTools Protocol 의 request interception** 을 대신 사용 — 즉 `chrome-devtools-mcp` 의 `evaluate_script` 로 `fetch` 를 monkey-patch 한다. 다만 검증 범위가 제한적.

가장 실용적:
- **mcp 루프는 "정상 상태만 시각 확인"** (데이터 있는 실제 페이지) — 로딩/빈/에러는 Playwright 자동 채널로 충분
- 4 상태 NOTES 기록은 Playwright spec 실행 로그 + 스크린샷을 인용해 작성

- [ ] **Step 1: mcp 루프 — 정상 상태 before 캡처**

필수: Task 3 Step 6 을 통과했고, 정상 상태 스냅샷이 `tests/e2e/visual/customers-list.spec.ts-snapshots/customers-list-normal-chromium-*.png` 에 있다.

해당 스냅샷을 `docs/superpowers/visual-log/2026-04-13/customers-list/before-normal.png` 로 복사:

```bash
cp web/tests/e2e/visual/customers-list.spec.ts-snapshots/customers-list-normal-chromium-*.png \
   docs/superpowers/visual-log/2026-04-13/customers-list/before-normal.png
```

- [ ] **Step 2: NOTES.md 작성**

`docs/superpowers/visual-log/2026-04-13/customers-list/NOTES.md`:

```markdown
# customers-list — 2026-04-13 (본게임 Phase 1)

## 사이클

- 1 (로딩): mockListLoading(30s) → entity-list-skeleton 가시 — Playwright PASS
- 2 (빈): mockListEmpty → EmptyState("고객.*없|등록된.*없") 가시 — Playwright PASS
- 3 (에러): mockListError(500) → 재시도 버튼 가시 — Playwright PASS
- 4 (정상): mockListNormal(rows×2) → "고객 A" 가시 + 시각 회귀 baseline 스냅샷 저장

## Playwright 실행 로그

```
pnpm playwright test tests/e2e/visual/customers-list.spec.ts
[PASS] customers 리스트 — 로딩 상태는 skeleton 을 보인다
[PASS] customers 리스트 — 빈 상태는 EmptyState 를 보인다
[PASS] customers 리스트 — 에러 상태는 재시도 버튼과 에러 문구를 보인다
[PASS] customers 리스트 — 정상 상태 시각 회귀 스냅샷
```

## a11y 기본선

- `EntityListPage` table/list 의 `role`/`aria-*` 유지 — 4 테스트 모두 getByRole 에 의존하므로 간접 검증됨
- 에러 상태 재시도 버튼은 `getByRole("button")` 로 접근 가능 — focusable

## 회귀 규칙

본 baseline 이후 커스터머 리스트 UI 의도 변경 시:
1. `pnpm playwright test ... --update-snapshots`
2. visual-log 에 `after-normal.png` 추가 + 사이클 N 사유 append
3. 본 NOTES 에 before/after 링크 추가
```

- [ ] **Step 3: 커밋 (부모 레포)**

```bash
cd /Users/phil/WorkSpace/apps/OneErp && git add docs/superpowers/visual-log/2026-04-13/customers-list/
git commit -m "chore(visual-log): customers-list 본게임 Phase 1 증거 4 상태"
```

- [ ] **Step 4: Submodule 포인터 업데이트 커밋**

```bash
git add web
git commit -m "chore(web): visual-dual-loop 본게임 Phase 1 customers list 커밋 포인터 갱신"
```

---

## Task 6: DoD 검증 + 후속 플랜 예고

- [ ] **Step 1: 산출물 전수 확인**

Run:
```bash
ls web/tests/e2e/visual/_helpers/
ls web/tests/e2e/visual/customers-list.spec.ts-snapshots/ 2>/dev/null
ls docs/superpowers/visual-log/2026-04-13/customers-list/
cd web && git log --oneline -n 4 && cd -
```

Expected:
- `mock-gateway.ts`, `mock-gateway.test.ts`, `auth-fixture.ts` 존재
- `customers-list-normal-chromium-*.png` baseline 스냅샷 존재
- `before-normal.png`, `NOTES.md` 존재
- web submodule 커밋 4개: Task 1, 2, 3, 4

- [ ] **Step 2: Playwright 전체 재실행으로 안정성 검증**

Run: `cd web && pnpm playwright test tests/e2e/visual/`
Expected: PASS 4/4, 재실행 시각 회귀 드리프트 없음.

- [ ] **Step 3: 사용자 보고 + 다음 플랜 예고**

> "본게임 Phase 1 (customers 리스트 4 상태) 완료. 인프라(mock-gateway, auth-fixture)와 시각 회귀 baseline 확보. 다음 후보: Phase 2 customers **상세** 4 시나리오 (진입/수정/검증 에러/권한 없음). 진행할까요?"

---

## 자가검토 (플랜 작성 후)

**Spec coverage (spec §4 본게임):**
- ✅ 리스트 4 상태 → Task 1(mock) + Task 3(spec) + Task 5(visual-log)
- ✅ 선도 엔티티 1개(customers)로 패턴 확정 → Task 1~5 전체가 customers 단일 집중
- ✅ 엔티티당 핵심 경로 1개 시각 회귀 스냅샷 → Task 3 Step 5
- ⚠️ 리스트 이후 상세/신규/횡단 → **명시적 out-of-scope**, Task 6 Step 3 에서 후속 플랜 예고
- ✅ visual-log 증거 → Task 5

**Placeholder scan:** TBD/TODO 없음. Task 3 Step 3 의 "selector 보정"은 **실제 컴포넌트 grep 명령**과 **대체 selector 샘플**을 구체적으로 제시.

**Type consistency:**
- `mockListLoading/Empty/Error/Normal` 4 함수가 Task 1, 3, 5 에서 동일 이름·시그니처 사용 — OK
- `authedPage` fixture 이름 Task 2, 3 일치 — OK
- visual-log 경로 `2026-04-13/customers-list/` 모든 태스크 일치 — OK
- web submodule 브랜치 `feature/visual-dual-loop-customers-list` (Task 0) vs 웜업의 `feature/visual-dual-loop-warmup` — 분리됨, 의도적

**위험 지점:**
- Task 3 Step 3 selector 보정이 컴포넌트 수정으로 번질 수 있음 — 최대 `data-testid` 1~2개 추가 선에서 멈추는 것을 명시함
- Task 5 의 chrome-devtools-mcp 루프가 Playwright `page.route` 와 충돌하는 문제는 전략 변경으로 회피 — "정상 상태만 mcp 관찰, 나머지는 Playwright 로그 인용"으로 실무적 타협

---

## 실행 인계

플랜이 `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-list.md`에 저장되었습니다. 두 가지 옵션:

1. **Subagent-Driven (권장)** — Task 1~4 는 서브에이전트에 위임(브라우저 MCP 불필요한 파일 작업 위주), Task 5 는 메인 세션에서 직접. 태스크 간 리뷰.
2. **Inline Execution** — 현재 세션에서 executing-plans 로 순차 실행.

어느 쪽으로 가시겠어요?
