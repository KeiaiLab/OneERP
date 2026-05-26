# customers-list — 2026-04-13 (본게임 Phase 1)

플랜: `docs/superpowers/plans/2026-04-13-visual-dual-loop-customers-list.md`
스킬: `.claude/skills/visual-dual-loop.md`

## 사이클

- **1 (로딩)**: `mockListLoading(30s)` → `entity-list-skeleton` 가시 — Playwright PASS
- **2 (빈)**: `mockListEmpty` → EmptyState("등록된.*없|고객.*없") 가시 — Playwright PASS
- **3 (에러)**: `mockListError(500)` → catch 가 빈 목록으로 처리되어 EmptyState 폴백 (실제 FE 동작 — 재시도 버튼은 미노출). spec 제목/검증 로직을 실제 동작에 맞춰 정렬함 (커밋 `b5857ae`/`934279d`/`1ec95b0` 시리즈에서 조정 완료) — Playwright PASS
- **4 (정상)**: `mockListNormal(rows×2)` → "고객 A" 가시 + 시각 회귀 baseline 스냅샷 저장

## Playwright 실행 로그 (2026-04-13)

```
$ PLAYWRIGHT_BASE_URL=http://localhost:3000 pnpm playwright test tests/e2e/visual/customers-list.spec.ts
Running 4 tests using 4 workers
  ✓ 1 customers 리스트 — 로딩 상태는 skeleton 을 보인다 (731ms)
  ✓ 4 customers 리스트 — 빈 상태는 EmptyState 를 보인다 (757ms)
  ✓ 2 customers 리스트 — 에러 상태는 EmptyState 를 보인다 (catch 가 빈 목록으로 처리) (768ms)
  ✓ 3 customers 리스트 — 정상 상태 시각 회귀 스냅샷 (827ms)
  4 passed (3.8s)
```

## 증거

- `before-normal.png` — Task 3 Step 5 에서 생성한 baseline 스냅샷 사본 (출처: `web/tests/e2e/visual/customers-list.spec.ts-snapshots/customers-list-normal-chromium-darwin.png`)
- after 스냅샷은 의도된 UI 변경 시점에 추가

## a11y 기본선

- `EntityListPage` 의 list/table 시맨틱 유지 — 4 테스트가 `getByText`/`getByTestId` 로 간접 검증
- 로딩 스켈레톤은 `data-testid="entity-list-skeleton"` 으로 노출 — screen reader 는 정적 노드로 인식

## 회귀 규칙

본 baseline 이후 customers 리스트 UI 의도 변경 시:
1. `cd web && pnpm playwright test tests/e2e/visual/ --update-snapshots`
2. 새 baseline 사본을 `after-normal.png` 로 본 디렉토리에 추가
3. 본 NOTES 에 변경 사유와 before/after 링크 한 줄 append
4. web submodule + 부모 레포 두 커밋 분리 (스냅샷 자체는 submodule, 증거 사본은 부모)
