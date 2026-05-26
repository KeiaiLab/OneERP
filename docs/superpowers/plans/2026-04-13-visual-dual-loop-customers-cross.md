# 시각 이중 루프 본게임 Phase 4 — 반응형 + a11y 횡단 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans`.

**Goal:** Phase 1~3에서 확보한 customers 3 페이지(리스트/상세/신규)를 sm/md/lg 뷰포트와 axe-core a11y 스캔으로 횡단 검증한다. 반응형 baseline 3장(리스트 정상 상태)과 a11y serious/critical 0건을 보장한다.

**Architecture:** Phase 1·2·3의 mock-gateway 헬퍼 100% 재사용. 신규 spec 2개:
- `customers-responsive.spec.ts` — sm(390)/md(768)/lg(1280) 뷰포트로 리스트 정상 상태 시각 회귀
- `customers-a11y.spec.ts` — 리스트/상세/신규 3 페이지를 mock 상태에서 axe 스캔 (`@a11y` 태그)

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md` §4

**Related:** `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-form.md` (완료)

**Scope:**
- 반응형 baseline 3장 (sm/md/lg, 리스트 정상 상태)
- a11y 스캔 3 시나리오 (mocked customers 페이지)
- visual-log `2026-04-13/customers-cross/`

**Out of scope:**
- 모든 페이지 × 모든 뷰포트 매트릭스 (양 폭증) — 리스트만 3 뷰포트, 상세/신규는 a11y만
- 키보드 Tab 순서 정밀 검증 — axe의 focus-order 규칙으로 대체
- firefox/webkit (Phase 5+ 또는 별도 트랙)

---

## 파일 구조

**Create (web submodule):**
- `web/tests/e2e/visual/customers-responsive.spec.ts` — 3 뷰포트 × 리스트 정상
- `web/tests/e2e/visual/customers-responsive.spec.ts-snapshots/` — 3 baselines
- `web/tests/e2e/visual/customers-a11y.spec.ts` — 3 페이지 axe 스캔 (`@a11y` 태그)

**Create (부모 레포):**
- `docs/superpowers/visual-log/2026-04-13/customers-cross/before-list-{sm,md,lg}.png`
- `docs/superpowers/visual-log/2026-04-13/customers-cross/NOTES.md`

---

## Task 1: 반응형 spec + 3 baseline

뷰포트:
- sm: 390×844 (모바일)
- md: 768×1024 (태블릿)
- lg: 1280×800 (데스크탑)

- [ ] **Step 1: spec 작성**

```ts
import { expect } from "@playwright/test";
import { test } from "./_helpers/auth-fixture";
import { mockListNormal } from "./_helpers/mock-gateway";

const VIEWPORTS = [
  { tag: "sm", width: 390, height: 844 },
  { tag: "md", width: 768, height: 1024 },
  { tag: "lg", width: 1280, height: 800 },
];

const ROWS = [
  { _id: "c1", customer_name: "고객 A", customer_type: "company", tax_id: "123", default_currency: "KRW" },
  { _id: "c2", customer_name: "고객 B", customer_type: "individual", tax_id: "987", default_currency: "USD" },
];

for (const vp of VIEWPORTS) {
  test(`customers 리스트 — 정상 상태 시각 회귀 (${vp.tag} ${vp.width}×${vp.height})`, async ({ authedPage }) => {
    await authedPage.setViewportSize({ width: vp.width, height: vp.height });
    await mockListNormal(authedPage, "customers", ROWS);
    await authedPage.goto("/customers");
    await expect(authedPage.getByText("고객 A")).toBeVisible();
    await expect(authedPage).toHaveScreenshot(`customers-list-${vp.tag}.png`, {
      maxDiffPixelRatio: 0.01,
    });
  });
}
```

- [ ] **Step 2: 3 시나리오 baseline 생성** — `--update-snapshots`
- [ ] **Step 3: 안정성 재실행 PASS**
- [ ] **Step 4: 커밋 — `test(visual): customers 리스트 반응형 3 뷰포트 시각 회귀`**

---

## Task 2: a11y spec — 3 페이지 axe 스캔

- [ ] **Step 1: spec 작성**

```ts
import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "./_helpers/auth-fixture";
import { mockGetByIdNormal, mockListNormal } from "./_helpers/mock-gateway";

const SAMPLE_CUSTOMER = { _id: "c1", customer_name: "고객 A", customer_type: "company", tax_id: "123", default_currency: "KRW", docstatus: 0 };

test("@a11y customers 리스트 — serious/critical 0건", async ({ authedPage }) => {
  await mockListNormal(authedPage, "customers", [SAMPLE_CUSTOMER]);
  await authedPage.goto("/customers");
  await authedPage.getByText("고객 A").waitFor();
  const results = await new AxeBuilder({ page: authedPage }).withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"]).analyze();
  const blocking = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(blocking, "customers 리스트 a11y 위반").toEqual([]);
});

test("@a11y customers 상세 — serious/critical 0건", async ({ authedPage }) => { /* mockGetByIdNormal → /customers/c1 → axe */ });
test("@a11y customers 신규 — serious/critical 0건", async ({ authedPage }) => { /* /customers/new → axe */ });
```

- [ ] **Step 2: 실행 — `pnpm playwright test tests/e2e/visual/customers-a11y.spec.ts`**
  - 위반 시: violations 콘솔 출력 후 spec 으로 차단. 본 Phase 에서 위반이 발견되면 **Phase 4 의 책임은 발견·기록** 까지이며, 수정은 별도 이슈로 분리한다 (NOTES 에 명시).
- [ ] **Step 3: 통과 또는 발견된 위반을 NOTES 에 기록 후 spec 을 `test.fixme` 로 보존하고 후속 이슈 생성**
- [ ] **Step 4: 커밋**

---

## Task 3: visual-log + 부모 커밋

- [ ] **Step 1: 3 baseline 사본 복사**
- [ ] **Step 2: NOTES.md 작성** — 뷰포트 결과 + a11y 위반 요약
- [ ] **Step 3: 부모 visual-log 커밋 + submodule 포인터 갱신**

---

## Task 4: DoD

- [ ] 시각 회귀 전체 재실행: PASS 16/16 (Phase 1: 4 + Phase 2: 5 + Phase 3: 4 + Phase 4 반응형: 3) — a11y 별도
- [ ] a11y 별도 실행: PASS 3/3 또는 위반 기록
- [ ] 사용자 보고

---

## 자가검토

- ✅ 뷰포트 3건은 매트릭스 폭발 회피 — 리스트 1 페이지만 횡단
- ✅ a11y 는 mocked 페이지에서 실행 — 백엔드 의존 없이 결정론적
- ⚠️ a11y 위반 발견 시 Phase 4 책임은 차단·기록까지. 수정은 컴포넌트 단위 별도 이슈 — Phase 4 에서 컴포넌트 수정 금지(스코프 위반)
- ⚠️ 반응형 baseline 은 `viewport`별 헤더 메뉴 변형 등으로 의도된 변경 빈발 — `maxDiffPixelRatio: 0.01` 이 너무 빡빡하면 0.02 까지 완화 가능 (그 이상은 baseline 갱신)
