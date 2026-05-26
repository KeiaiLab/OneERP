# 시각 이중 루프 본게임 Phase 3 — customers 신규 폼 4 시나리오 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans`.

**Goal:** customers 신규 등록 폼의 4 시나리오(필수값 누락 / Ctrl+S 키보드 제출 / 서버 실패 / 정상 진입 시각 회귀)를 mock-gateway 확장으로 결정론적으로 재현한다.

**Architecture:** Phase 1·2 인프라 재사용. mock-gateway에 `mockCreateOk`/`mockCreateError` 2 함수 추가 (POST 메서드 분기로 list mock과 충돌 회피). spec은 `customers-form.spec.ts`.

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md` §4

**Related:** `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-detail.md` (완료)

**Scope:**
- 신규 폼 4 시나리오
- baseline 1장 (빈 폼 진입 직후)
- visual-log `2026-04-13/customers-form/`

**Out of scope:** 반응형/a11y(Phase 4), 다른 엔티티 전파.

---

## 파일 구조

**Modify (web submodule):**
- `web/tests/e2e/visual/_helpers/mock-gateway.ts` — `mockCreateOk`, `mockCreateError` 추가 (POST 분기)
- `web/tests/e2e/visual/_helpers/mock-gateway.test.ts` — 신규 함수 호출 가능성 2건 추가

**Create (web submodule):**
- `web/tests/e2e/visual/customers-form.spec.ts` — 4 시나리오 + baseline 1장
- `web/tests/e2e/visual/customers-form.spec.ts-snapshots/customers-form-blank-chromium-darwin.png`

**Create (부모 레포):**
- `docs/superpowers/visual-log/2026-04-13/customers-form/before-blank.png`
- `docs/superpowers/visual-log/2026-04-13/customers-form/NOTES.md`

---

## Task 1: mock-gateway POST 핸들러 추가

- [ ] **Step 1: `mockCreateOk(page, entity, returnDoc, service)` 와 `mockCreateError(page, entity, status, service)` 구현**
  - URL 패턴: `entityPattern(service, entity)` 재사용 (list와 동일 collection endpoint)
  - method 분기: `route.request().method() !== "POST"` → `route.fallback()`
- [ ] **Step 2: 단위 테스트 2건 추가 (route 등록 확인)**
- [ ] **Step 3: vitest + biome + tsc 통과**
- [ ] **Step 4: 커밋 — `test(visual): mock-gateway POST(create) 헬퍼 2 함수 추가`**

⚠️ list mock과 동일 패턴이라 단일 spec 내에서 `mockListNormal + mockCreateOk` 동시 사용 시 핸들러 등록 순서 주의 — POST 핸들러를 list mock보다 **나중에 등록**해야 한다 (Playwright는 후등록 우선). 본 Phase는 폼만 다루므로 충돌 없음.

---

## Task 2: customers-form.spec.ts — 4 시나리오 + baseline

**시나리오:**

1. **빈 폼 제출 → required 에러**
   - goto `/customers/new`
   - "저장" 버튼 클릭 → "고객명은(는) 필수입니다" 가시
   - 서버 호출 없음 (mockCreateOk 등록해도 호출 안 됨)

2. **Ctrl+S 키보드 제출 → 성공 토스트**
   - `mockCreateOk(returnDoc={_id:"c-new"})`
   - "고객명" 입력 → `Control+s` press → "생성되었습니다" 토스트
   - 라우터가 `/customers/c-new` 로 push 됨 — 토스트만 검증 (URL 검증은 후속 라우트 mock 필요로 생략)

3. **서버 500 → 실패 토스트**
   - `mockCreateError(500)`
   - "고객명" 입력 → "저장" 클릭 → "저장 중 오류가 발생했습니다" 토스트

4. **빈 폼 진입 시각 회귀 baseline**
   - goto `/customers/new` → "고객 추가" 제목 가시 → `toHaveScreenshot("customers-form-blank.png", { maxDiffPixelRatio: 0.01 })`

- [ ] **Step 1: spec 작성**
- [ ] **Step 2: 4 시나리오 PASS 확인 (--grep-invert "스냅샷")**
- [ ] **Step 3: baseline 생성 (--update-snapshots)**
- [ ] **Step 4: 안정성 재실행 PASS**
- [ ] **Step 5: 커밋 — `test(visual): customers 신규 폼 4 시나리오 + 빈 폼 시각 회귀 스냅샷`**

⚠️ Ctrl+S 시나리오: 시나리오 2 의 push 후 새 GET 요청이 발생할 수 있으므로 `mockGetByIdNormal` 도 함께 등록해 잔여 라우터 이동을 무해화한다.

---

## Task 3: visual-log

- [ ] **Step 1: baseline 사본 복사**
- [ ] **Step 2: NOTES.md 작성** (Phase 2와 동일 골격)
- [ ] **Step 3: 부모 visual-log 커밋 + submodule 포인터 갱신**

---

## Task 4: DoD

- [ ] Playwright 전체 재실행 → PASS 13/13 (Phase 1: 4 + Phase 2: 5 + Phase 3: 4)
- [ ] 산출물 전수 ls 확인
- [ ] 사용자 보고

---

## 자가검토

- ✅ 4 시나리오가 mock-gateway 단일 인터페이스로 결정론 보장
- ✅ list mock과 POST 핸들러 등록 순서 충돌 — 본 Phase 내에선 발생 안 함, 주석으로 명시
- ✅ react-hook-form required 메시지("고객명은(는) 필수입니다") 가 entity-form-page.tsx 의 `buildValidationRules` 출력과 정확히 일치
- ⚠️ Ctrl+S 시나리오의 후속 router.push 처리 — 토스트만 검증하는 보수적 단언으로 처리
