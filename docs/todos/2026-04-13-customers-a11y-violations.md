# customers 페이지 a11y 위반 — ✅ 해소 완료 (2026-04-13)

**상태**: CLOSED — 같은 날 후속 수정으로 4 위반 모두 해소.

## 해소 요약

| 위반 | 수정 위치 | 변경 내용 |
|------|-----------|-----------|
| `color-contrast` (serious, 3 페이지) | `web/app/globals.css` | `--color-fg-subtle` `#757682` (4.49:1) → `#646571` (5.04:1) |
| `button-name` (critical, 9건, 신규 폼) | `web/components/crud/field-renderer.tsx` | Select trigger 에 `id` + `aria-label={field.label}` 추가 |

**검증**: `pnpm playwright test tests/e2e/visual/customers-a11y.spec.ts` → **3/3 PASS** (해소 직후)
**시각 회귀 영향**: 6 baseline 모두 `maxDiffPixelRatio 0.01` 통과 — baseline 갱신 불필요.

다음은 발견 시점의 최초 분석 (참고용 보존):

---

발견일: 2026-04-13 (시각 이중 루프 본게임 Phase 4 스캔)
스캐너: `@axe-core/playwright` WCAG 2.1 AA
영향 페이지: `/customers`, `/customers/:id`, `/customers/new`

## 위반 요약

| 페이지 | rule id | impact | 위치/사유 |
|--------|---------|--------|-----------|
| 리스트 | `color-contrast` | serious | `text-fg-subtle` 토큰의 9pt 회색 텍스트 — 4.49:1 (≥4.5:1 필요) |
| 상세 | `color-contrast` | serious | 동일 토큰 |
| 신규 | `button-name` | **critical** (9건) | discernible text 누락 — 아이콘 전용 버튼 추정 |
| 신규 | `color-contrast` | serious | "Ctrl+S 저장 / Esc 취소" 안내 등 |

## 재현

```bash
cd web && PLAYWRIGHT_BASE_URL=http://localhost:3000 \
  pnpm playwright test tests/e2e/visual/customers-a11y.spec.ts
# (현재 test.fixme 로 차단 중이므로 fixme → test 로 일시 변경 후 실행)
```

## 수정 방향

- **color-contrast**: `text-fg-subtle`(#757682) 토큰을 ≥4.5:1 만족하도록 다크닝 또는 폰트 사이즈 ≥10pt 보장. 디자인 시스템 단위 변경이라 디자이너 검토 필요.
- **button-name (신규)**: `entity-form-page.tsx` 내부 또는 form 컴포넌트 트리에서 아이콘 전용 버튼 9건 식별 → `aria-label` 부여. 후보:
  - 라인 아이템 추가/삭제 버튼
  - 토스트 닫기
  - 헤더 햄버거/유저 메뉴

## 차단 위치

- `web/tests/e2e/visual/customers-a11y.spec.ts` — `test.fixme` 3건
- 위반 해소 후 `test.fixme` → `test` 복원 + 본 todo 종료

## 우선순위

- **critical (button-name)**: 다음 스프린트 내 처리 권장 — screen reader 사용자에게 9 버튼이 무명
- **serious (color-contrast)**: 디자인 토큰 변경 — 타 페이지에 영향 광범위, 별도 디자인 리뷰 후
