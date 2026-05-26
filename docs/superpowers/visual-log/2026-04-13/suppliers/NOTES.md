# suppliers — 2026-04-13 (본게임 Phase 5 전파)

플랜: `docs/superpowers/plans/2026-04-13-visual-dual-loop-suppliers.md`

## 전파 결과

customers Phase 1~4 패턴을 `suppliers` 엔티티에 전파. **mock-gateway 헬퍼 0 변경**, spec 5 파일만 추가.

| 영역 | 시나리오 | 결과 |
|------|----------|------|
| list | 4 상태 (로딩/빈/에러/정상) + baseline | 4 PASS + baseline 1 |
| detail | 5 시나리오 (정상/수정/422/403/baseline) | 5 PASS + baseline 1 |
| form | 4 시나리오 (필수값/Ctrl+S/500/baseline) | 4 PASS + baseline 1 |
| responsive | sm/md/lg | 3 PASS + baseline 3 |
| a11y | 리스트/상세/신규 axe | **3 PASS** — 위반 0건 |

**전체 19 PASS** (customers 19 합산 시 38/38 PASS, 7.9s)

## a11y 전파 효과 — 핵심 가치

customers Phase 4의 토큰·Select 수정(`--color-fg-subtle` `#646571` + Select `aria-label={field.label}`)이 suppliers에 **자동 전파**되어 위반 0건 달성:
- color-contrast: 토큰 변경이 글로벌 적용
- button-name: Select 컴포넌트(`field-renderer.tsx`) 공유 → suppliers form의 Select trigger도 자동 라벨링

→ 첫 엔티티(customers)에서의 디자인 시스템·컴포넌트 수정이 후속 엔티티들의 a11y 부채를 0으로 만드는 패턴 입증.

## 증거 (6 baseline)

- `before-list-normal.png` / `before-detail-normal.png` / `before-form-blank.png`
- `before-list-sm.png` / `before-list-md.png` / `before-list-lg.png`
- 출처: `web/tests/e2e/visual/suppliers-{list,detail,form,responsive}.spec.ts-snapshots/`

## 디스커버리

- 리스트 EmptyState selector 가 `getByText` 가 아니라 `getByTestId("empty-state")` — 플랜 작성 단계의 가정과 다름. customers spec 의 실제 selector 를 따라 spec 작성 직후 1회 보정.
- suppliers `formFields` 에 select 타입 없음 → button-name 위반 회피 (디자인적 우연이지만 a11y 안전).

## 회귀 규칙

customers 패턴과 동일. baseline 갱신 시 3 커밋 패턴 유지 (submodule + 부모 visual-log + 포인터).
