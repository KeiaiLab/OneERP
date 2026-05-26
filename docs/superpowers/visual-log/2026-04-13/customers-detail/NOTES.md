# customers-detail — 2026-04-13 (본게임 Phase 2)

플랜: `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-detail.md`
스킬: `.claude/skills/visual-dual-loop.md`

## 시나리오

- **1 (정상 진입)**: `mockGetByIdNormal(SAMPLE)` → "고객 A" 가시 — Playwright PASS
- **2 (수정 → 저장 성공)**: `mockGetByIdNormal + mockUpdateOk` → 폼 진입 → 저장 클릭 → "수정되었습니다" 토스트 — Playwright PASS
- **3 (검증 에러 422)**: `mockUpdateValidationError` → 422 catch → "저장 중 오류가 발생했습니다" 토스트 — Playwright PASS
  - **주의**: 현재 FE는 422 응답을 필드 단위 에러로 매핑하지 않고 공통 실패 토스트로만 표시한다. 실제 동작에 spec을 정렬했으며, 필드 매핑은 향후 `entity-form-page.tsx` 개선 과제로 남김.
- **4 (권한 없음 403)**: `mockGetByIdForbidden` → 토스트("데이터를 불러올 수 없습니다") + 폴백 화면("데이터를 찾을 수 없습니다") — Playwright PASS
- **5 (정상 진입 시각 회귀)**: `mockGetByIdNormal` → baseline 스냅샷 저장 + 안정성 재실행 PASS

## Playwright 실행 로그 (2026-04-13)

```
$ PLAYWRIGHT_BASE_URL=http://localhost:3000 pnpm playwright test tests/e2e/visual/customers-detail.spec.ts
Running 5 tests using 5 workers
  ✓ customers 상세 — 정상 진입 시 필드가 표시된다 (1.4s)
  ✓ customers 상세 — 권한 없음(403) 시 폴백 화면이 표시된다 (1.4s)
  ✓ customers 상세 — 정상 진입 시각 회귀 스냅샷 (1.4s)
  ✓ customers 수정 — 422 검증 에러 시 저장 실패 토스트가 표시된다 (1.4s)
  ✓ customers 상세 → 수정 → 저장 성공 (1.5s)
  5 passed (4.1s)
```

## 증거

- `before-normal.png` — Phase 2 Task 2 Step 3 에서 생성한 baseline 사본
  - 출처: `web/tests/e2e/visual/customers-detail.spec.ts-snapshots/customers-detail-normal-chromium-darwin.png`

## a11y 기본선

- "수정" 링크는 `<Link><Button>수정</Button></Link>` 구조 — `getByRole("button", { name: /^저장$/ })` 으로 폼 페이지 진입 후 접근
- 토스트는 `Toast` 컴포넌트가 fixed 위치 + `role` 미지정 — 시나리오 2/3에서 텍스트 기반 매칭으로 검증
- 폴백 화면("데이터를 찾을 수 없습니다")은 시맨틱 컨테이너 없는 평문 — 향후 `role="alert"` 또는 `role="status"` 보강 후보

## 회귀 규칙

본 baseline 이후 customers 상세 UI 의도 변경 시:
1. `cd web && pnpm playwright test tests/e2e/visual/customers-detail.spec.ts --update-snapshots`
2. 새 baseline 사본을 `after-normal.png` 로 본 디렉토리에 추가
3. 본 NOTES 에 변경 사유와 before/after 링크 한 줄 append
4. submodule 커밋 + 부모 visual-log 커밋 + submodule 포인터 갱신 커밋 — Phase 1과 동일 3 커밋 패턴
