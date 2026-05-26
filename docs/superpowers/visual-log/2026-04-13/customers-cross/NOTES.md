# customers-cross — 2026-04-13 (본게임 Phase 4 횡단)

플랜: `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-cross.md`

## 반응형 (Task 1) — 3 baseline 확보

| 뷰포트 | 해상도 | baseline 파일 | 결과 |
|--------|--------|---------------|------|
| sm | 390×844 | `before-list-sm.png` | PASS, 안정성 재실행 통과 |
| md | 768×1024 | `before-list-md.png` | PASS |
| lg | 1280×800 | `before-list-lg.png` | PASS |

```
$ pnpm playwright test tests/e2e/visual/customers-responsive.spec.ts
3 passed (3.3s)
```

## a11y (Task 2) — axe-core WCAG 2.1 AA 스캔

**결과**: 3 페이지 모두 serious/critical 위반 발견 — `test.fixme` 로 의도적 차단 (3 skipped).

| 페이지 | rule id | impact | 개수 |
|--------|---------|--------|------|
| 리스트 | `color-contrast` | serious | 1 |
| 상세 | `color-contrast` | serious | 1 |
| 신규 | `button-name` | **critical** | 9 |
| 신규 | `color-contrast` | serious | 1 |

### 후속 이슈

`docs/todos/2026-04-13-customers-a11y-violations.md` — 디자인 토큰 다크닝 + 아이콘 버튼 `aria-label` 보강 후 `test.fixme` → `test` 복원.

### Phase 4 책임 경계

본 Phase 의 책임은 **위반 발견·차단·기록** 까지. 컴포넌트 수정은 별도 이슈로 분리한다 (Phase 4 스코프 위반 회피).

## 증거

- `before-list-sm.png` / `before-list-md.png` / `before-list-lg.png`
  - 출처: `web/tests/e2e/visual/customers-responsive.spec.ts-snapshots/customers-list-{sm,md,lg}-chromium-darwin.png`

## 회귀 규칙

반응형 baseline 갱신 절차는 Phase 1·2·3과 동일. a11y 스펙은 위반 해소 시점에 fixme 제거 후 PASS 확인.
