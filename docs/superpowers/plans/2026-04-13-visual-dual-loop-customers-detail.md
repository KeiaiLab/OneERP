# 시각 이중 루프 본게임 Phase 2 — customers 상세 4 시나리오 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans`. Steps use checkbox (`- [ ]`) syntax.

**Goal:** customers 상세/수정 흐름의 4 시나리오(정상 진입 / 수정 저장 성공 / 검증 에러 / 권한 없음)를 mock-gateway 확장으로 결정론적으로 재현하고, 정상 진입 화면 1장의 시각 회귀 baseline을 추가한다.

**Architecture:** Phase 1 인프라(`_helpers/mock-gateway.ts`, `_helpers/auth-fixture.ts`) 재사용. `mock-gateway` 에 `mockGetById*` 4 함수 + `mockUpdate*` 2 함수를 **추가**한다 (리스트 헬퍼는 손대지 않음). spec은 `customers-detail.spec.ts` 단일 파일.

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md` §4

**Related:** Phase 1 `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-list.md` (완료)

**Scope:**
- customers 상세 페이지 정상 진입 (시각 회귀 baseline 1장)
- 상세 → 수정 페이지 전환 + 저장 성공
- 수정 폼 검증 에러 표시
- 상세 진입 시 403 권한 없음 처리
- visual-log 사이클 4건 (`docs/superpowers/visual-log/2026-04-13/customers-detail/`)

**Out of scope:** 신규 폼(Phase 3), 반응형/a11y 횡단(Phase 4), 다른 엔티티 전파.

---

## 파일 구조

**Modify (web submodule):**
- `web/tests/e2e/visual/_helpers/mock-gateway.ts` — `mockGetByIdNormal/Error/Forbidden/Loading`, `mockUpdateOk/ValidationError` 6 함수 추가
- `web/tests/e2e/visual/_helpers/mock-gateway.test.ts` — 신규 함수 호출 가능성 4건 추가

**Create (web submodule):**
- `web/tests/e2e/visual/customers-detail.spec.ts` — 4 시나리오 + 정상 진입 시각 회귀 1장
- `web/tests/e2e/visual/customers-detail.spec.ts-snapshots/customers-detail-normal-chromium-darwin.png` — Playwright 자동 생성

**Create (부모 레포):**
- `docs/superpowers/visual-log/2026-04-13/customers-detail/before-normal.png`
- `docs/superpowers/visual-log/2026-04-13/customers-detail/NOTES.md`

**Modify (web submodule, 필요 시 1줄):**
- 검증 에러 메시지 selector가 안정적이지 않으면 폼 컴포넌트에 `data-testid="form-error"` 1줄 추가만 허용. 그 이상 컴포넌트 수정 금지.

---

## 사전 체크 (Task 0)

- [ ] **Step A: 브랜치 확인**

```bash
cd /Users/phil/WorkSpace/apps/OneErp/web && git branch --show-current
# feature/visual-dual-loop-customers-list 그대로 사용 (Phase 2 별도 브랜치 불필요)
```

- [ ] **Step B: dev 서버 기동 확인** (port 3000 또는 3001)

- [ ] **Step C: customers `EntityConfig` 확인 — 필수 필드 / 검증 규칙 파악**

```bash
grep -nE "customer_name|required|validate" web/lib/crud/entities/customers*.ts 2>/dev/null
```

---

## Task 1: mock-gateway 확장 — getById/update 6 함수

**Files:**
- Modify: `web/tests/e2e/visual/_helpers/mock-gateway.ts`
- Modify: `web/tests/e2e/visual/_helpers/mock-gateway.test.ts`

- [ ] **Step 1: 테스트 추가 (실패 확인)**

`mock-gateway.test.ts` 에 다음 추가:
```ts
it("mockGetByIdNormal 은 단일 도큐먼트를 돌려준다", async () => { /* ... */ });
it("mockGetByIdForbidden 은 403 을 돌려준다", async () => { /* ... */ });
it("mockUpdateOk 는 PUT/PATCH 를 200 으로 처리한다", async () => { /* ... */ });
it("mockUpdateValidationError 는 422 를 돌려준다", async () => { /* ... */ });
```

Run: `cd web && pnpm test _helpers/mock-gateway.test.ts` → FAIL.

- [ ] **Step 2: 헬퍼 구현**

`mock-gateway.ts` 에 다음 시그니처 추가:
```ts
function entityIdPattern(service: string, entity: string, id: string): RegExp {
  return new RegExp(`/api/gateway/api/v1/${service}/${entity}/${id}(\\?|$)`);
}

export async function mockGetByIdNormal(page, entity, id, doc, service = "selling"): Promise<void>;
export async function mockGetByIdError(page, entity, id, status = 500, service = "selling"): Promise<void>;
export async function mockGetByIdForbidden(page, entity, id, service = "selling"): Promise<void>; // 403
export async function mockGetByIdLoading(page, entity, id, delayMs = 30_000, service = "selling"): Promise<void>;

// PUT/PATCH/POST 모두 매칭 — method 미체크 (Playwright route 는 GET 외 자동 통과 안 함이라 명시 필요)
export async function mockUpdateOk(page, entity, id, returnDoc, service = "selling"): Promise<void>;
export async function mockUpdateValidationError(page, entity, id, errors, service = "selling"): Promise<void>; // 422 + {detail: [...]}
```

각 구현은 `meOk(page)` 호출 후 `page.route(entityIdPattern(...), handler)` 패턴.

- [ ] **Step 3: 테스트 통과 확인** + biome/tsc 0 에러.

- [ ] **Step 4: 커밋**
```bash
cd web && git add tests/e2e/visual/_helpers/mock-gateway.ts tests/e2e/visual/_helpers/mock-gateway.test.ts
git commit -m "test(visual): mock-gateway getById/update 헬퍼 6 함수 추가"
```

---

## Task 2: customers-detail.spec.ts — 4 시나리오 + 시각 회귀 1장

**Files:**
- Create: `web/tests/e2e/visual/customers-detail.spec.ts`

- [ ] **Step 1: 스펙 작성 (4 시나리오)**

```ts
import { expect } from "@playwright/test";
import {
  mockGetByIdNormal, mockGetByIdForbidden,
  mockUpdateOk, mockUpdateValidationError,
  mockListNormal,
} from "./_helpers/mock-gateway";
import { test } from "./_helpers/auth-fixture";

const ID = "c-test-001";
const URL = `/customers/${ID}`;
const EDIT_URL = `${URL}/edit`;
const SAMPLE = { _id: ID, customer_name: "고객 A", customer_type: "company", tax_id: "123-45-67890", default_currency: "KRW" };

test("customers 상세 — 정상 진입 시 필드가 표시된다", async ({ authedPage }) => { /* mockGetByIdNormal → goto → expect 고객 A */ });
test("customers 상세 → 수정 → 저장 성공", async ({ authedPage }) => { /* mockGetByIdNormal + mockUpdateOk → 수정 → 토스트 */ });
test("customers 수정 — 검증 에러 시 폼 에러 메시지가 표시된다", async ({ authedPage }) => { /* mockUpdateValidationError → 에러 텍스트 */ });
test("customers 상세 — 권한 없음(403) 처리", async ({ authedPage }) => { /* mockGetByIdForbidden → 토스트 또는 빈 화면 */ });
test("customers 상세 — 정상 진입 시각 회귀 스냅샷", async ({ authedPage }) => { /* toHaveScreenshot baseline */ });
```

- [ ] **Step 2: 4 시나리오 먼저 PASS 시키기 (selector 보정 — 1ec95b0 패턴 답습)**

실제 컴포넌트 출력 확인:
```bash
grep -nE "data-testid|getByRole|토스트|저장" web/components/crud/entity-detail-page.tsx web/components/crud/entity-form-page.tsx
```

검증 에러 selector가 약하면 `data-testid="form-error"` 1줄 추가만 허용.

Run: `cd web && pnpm playwright test tests/e2e/visual/customers-detail.spec.ts --grep -v "스냅샷"`
Expected: PASS 4/4.

- [ ] **Step 3: 정상 진입 baseline 스냅샷 생성**
```bash
cd web && pnpm playwright test tests/e2e/visual/customers-detail.spec.ts --grep "스냅샷" --update-snapshots
```

- [ ] **Step 4: 안정성 확인 — 재실행 PASS**
```bash
cd web && pnpm playwright test tests/e2e/visual/customers-detail.spec.ts
```
Expected: PASS 5/5.

- [ ] **Step 5: 커밋**
```bash
cd web && git add tests/e2e/visual/customers-detail.spec.ts tests/e2e/visual/customers-detail.spec.ts-snapshots/
git commit -m "test(visual): customers 상세 4 시나리오 + 정상 진입 시각 회귀 스냅샷"
```

---

## Task 3: visual-log 증거 작성

**Files:**
- Create: `docs/superpowers/visual-log/2026-04-13/customers-detail/before-normal.png` (baseline 사본)
- Create: `docs/superpowers/visual-log/2026-04-13/customers-detail/NOTES.md`

- [ ] **Step 1: baseline 복사**
```bash
cd /Users/phil/WorkSpace/apps/OneErp
mkdir -p docs/superpowers/visual-log/2026-04-13/customers-detail
cp web/tests/e2e/visual/customers-detail.spec.ts-snapshots/customers-detail-normal-chromium-darwin.png \
   docs/superpowers/visual-log/2026-04-13/customers-detail/before-normal.png
```

- [ ] **Step 2: NOTES 작성** — Phase 1 NOTES와 동일 골격, 5 시나리오 결과·a11y 기본선·회귀 규칙.

- [ ] **Step 3: 부모 커밋**
```bash
git add docs/superpowers/visual-log/2026-04-13/customers-detail/
git commit -m "chore(visual-log): customers-detail 본게임 Phase 2 증거 4 시나리오"
```

- [ ] **Step 4: submodule 포인터 갱신 커밋**
```bash
git add web && git commit -m "chore(web): visual-dual-loop 본게임 Phase 2 customers detail 커밋 포인터 갱신"
```

---

## Task 4: DoD 검증 + 후속 예고

- [ ] **Step 1: 산출물 전수 확인** — `ls web/tests/e2e/visual/`, 부모 visual-log, 양 레포 git log
- [ ] **Step 2: Playwright 전체 재실행** — `cd web && pnpm playwright test tests/e2e/visual/` → PASS 9/9 (Phase 1 4건 + Phase 2 5건)
- [ ] **Step 3: 사용자 보고**
> "본게임 Phase 2 (customers 상세 4 시나리오) 완료. 다음 후보: Phase 3 customers **신규** 폼 (폼 검증/키보드 네비/submit 실패). 진행할까요?"

---

## 자가검토

- ✅ 4 시나리오 모두 mock-gateway 단일 인터페이스로 결정론 보장
- ✅ Phase 1 헬퍼 변경 없음 — 추가만 (회귀 위험 0)
- ✅ baseline 1장 추가 — Phase 1과 동일 임계값(0.01) 유지
- ⚠️ 수정 폼 검증 메시지 selector — 컴포넌트 grep 결과에 따라 `data-testid` 1줄 추가 가능성. 그 이상 손대면 **Out of scope**
- ⚠️ "권한 없음" 처리는 현재 FE에서 토스트만 띄우고 빈 화면 잔존 가능 — Phase 1 에러 시나리오와 동일하게 **실제 동작에 spec을 정렬**, 컴포넌트 변경하지 않음

## 실행 인계

`docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-detail.md` 저장 완료. 인라인 실행 권장 (Phase 1 패턴 답습).
