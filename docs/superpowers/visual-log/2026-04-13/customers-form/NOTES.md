# customers-form — 2026-04-13 (본게임 Phase 3)

플랜: `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-form.md`
스킬: `.claude/skills/visual-dual-loop.md`

## 시나리오

- **1 (필수값 누락)**: 빈 폼 → 저장 클릭 → "고객명은(는) 필수입니다" — Playwright PASS
  - react-hook-form `rules.required` 가 client-side 차단. 서버 호출 0회.
- **2 (Ctrl+S 키보드 제출)**: "고객명" 입력 → `Control+s` → POST 200 → `router.push(/customers/c-new)` 로 상세 페이지 이동 — Playwright PASS
  - 토스트("생성되었습니다")는 push 직후 unmount 되어 단언 race — URL 변경(`waitForURL`) 으로 종착 검증
  - 후속 GET 은 `mockGetByIdNormal` 로 무해화
- **3 (서버 500)**: "고객명" 입력 → 저장 → POST 500 → catch → "저장 중 오류가 발생했습니다" — Playwright PASS
- **4 (빈 폼 진입 시각 회귀)**: goto `/customers/new` → "고객 추가" 가시 → baseline 저장 + 안정성 재실행 PASS

## Playwright 실행 로그 (2026-04-13)

```
$ PLAYWRIGHT_BASE_URL=http://localhost:3000 pnpm playwright test tests/e2e/visual/customers-form.spec.ts
Running 4 tests using 4 workers
  ✓ customers 신규 — 빈 폼 진입 시각 회귀 스냅샷 (1.4s)
  ✓ customers 신규 — 빈 폼 제출 시 필수 항목 검증 메시지가 표시된다 (1.5s)
  ✓ customers 신규 — 서버 500 응답 시 실패 토스트가 표시된다 (1.5s)
  ✓ customers 신규 — Ctrl+S 키보드 단축키로 저장 시 성공 토스트가 표시된다 (1.5s)
  4 passed (4.2s)
```

## 증거

- `before-blank.png` — Phase 3 Task 2 Step 3 baseline 사본
  - 출처: `web/tests/e2e/visual/customers-form.spec.ts-snapshots/customers-form-blank-chromium-darwin.png`

## a11y / 키보드 기본선

- 필수 표시는 라벨 옆 빨간 `*` (form-field.tsx) — screen reader 는 `aria-required` 미부여 (개선 후보)
- Ctrl+S 단축키는 `useKeyboardShortcut` 으로 등록 — 시나리오 2에서 실 동작 검증
- Esc(취소)는 본 Phase 미검증 — Phase 4(횡단)에서 다룸
- 저장 버튼은 `<Button type="submit">저장</Button>` — `getByRole("button", { name: /^저장$/ })` 로 안정적 접근

## 회귀 규칙

본 baseline 이후 신규 폼 UI 의도 변경 시:
1. `cd web && pnpm playwright test tests/e2e/visual/customers-form.spec.ts --update-snapshots`
2. 새 baseline 사본을 `after-blank.png` 로 본 디렉토리에 추가
3. 본 NOTES 에 변경 사유 한 줄 append
4. submodule 커밋 + 부모 visual-log 커밋 + submodule 포인터 갱신 — Phase 1·2와 동일 3 커밋 패턴
