# 시각 이중 루프 본게임 Phase 5 — suppliers 전파 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans`.

**Goal:** customers Phase 1~4 패턴을 `suppliers` 엔티티에 전파해 헬퍼 재사용성을 검증한다. 새 코드는 spec 4 파일뿐 — mock-gateway 변경 0.

**Architecture:** `service: "buying"` 만 다르고 형태는 customers와 동형. 4 spec 작성, 5 시각 baseline 추가(list 정상 + detail 정상 + form 빈 + 반응형 sm/md/lg), a11y 3 시나리오.

**Spec:** `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md`

**Scope:**
- list 4 상태 / detail 4 시나리오 / form 4 시나리오 / 반응형 3 / a11y 3 = 18 테스트
- visual-log `2026-04-13/suppliers/`

**Out of scope:** 헬퍼 변경, 컴포넌트 변경, 다른 엔티티

---

## Task 1: 4 spec 작성 + baseline 생성

**Files (web submodule):**
- `tests/e2e/visual/suppliers-list.spec.ts` — 4 상태 + 정상 baseline
- `tests/e2e/visual/suppliers-detail.spec.ts` — 4 시나리오 + 정상 baseline
- `tests/e2e/visual/suppliers-form.spec.ts` — 4 시나리오 + 빈 폼 baseline
- `tests/e2e/visual/suppliers-responsive.spec.ts` — sm/md/lg
- `tests/e2e/visual/suppliers-a11y.spec.ts` — 3 페이지 axe 스캔

각 spec은 customers 대응 spec을 "고객→공급업체", "customer→supplier", "selling→buying"로 치환한 미러.

- [ ] **Step 1**: 5 spec 작성
- [ ] **Step 2**: scenarios PASS (`--grep-invert "스냅샷"`)
- [ ] **Step 3**: baseline 생성 (`--update-snapshots --grep "스냅샷|시각 회귀"`)
- [ ] **Step 4**: 안정성 재실행 — 전체 PASS
- [ ] **Step 5**: 커밋 — `test(visual): suppliers 4 spec 전파 (list/detail/form/responsive/a11y)`

---

## Task 2: visual-log

- [ ] **Step 1**: 5 baseline 사본 → `docs/superpowers/visual-log/2026-04-13/suppliers/`
- [ ] **Step 2**: NOTES.md — customers와 동일 골격, 결과만 갱신
- [ ] **Step 3**: 부모 visual-log 커밋 + submodule 포인터 갱신

---

## Task 3: DoD

- [ ] 시각 회귀 + a11y 전체 재실행 → 전부 PASS
- [ ] 사용자 보고

---

## 자가검토

- ✅ 헬퍼 0 변경 — 패턴 재사용성 입증이 본 Phase 의 핵심 가치
- ✅ a11y serious/critical 0건 기대 (Phase 4 토큰·Select 수정의 전파 효과)
- ⚠️ baseline drift 우려: suppliers 디자인이 customers와 다른 헤더/사이드바 항목을 가질 가능성 — 발견 시 Phase 5 내에서 baseline 그대로 채택, 컴포넌트 수정 안 함
