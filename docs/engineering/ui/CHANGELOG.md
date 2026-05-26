# UI 디자인 시스템 변경 이력

문서 규칙(`docs/engineering/ui/enforcement.md` 4계층 — template → pattern → primitive → token) 과 실제 코드 구현의 정합을 기록한다.

## 2026-04-12 — Executive Refined 전면 리뉴얼 캠페인

### 배경

`docs/engineering/ui/{design-system,tokens,components,page-templates,crud-patterns,enforcement}.md` 가 정의한 4계층 중 **token 한 계층만 코드가 준수**하고 있었다. 21개 primitive 는 `bg-[var(--color-X)]` arbitrary-value 문법 129+회, 7 표준 템플릿은 미구현, `pretext` 텍스트 측정 계약은 미실현, Pretendard 폰트는 시스템 fallback 의존.

하네스(Ralph Loop v2.3) 단일 캠페인으로 네 계층 전부를 상용 수준으로 정립. 사용자 결정 시각 톤은 **Executive Refined** (남청 `#1f3c88` 브랜드 유지, 정돈 중심).

### H0 — 하네스 토대

- `next/font/local` 로 Pretendard Variable 자체 호스팅 (`public/fonts/PretendardVariable.woff2` 2MB, `--font-pretendard` CSS 변수 주입)
- `@theme` 토큰 확장 — `--color-trend-*`, `--shadow-focus`, `--text-*` + line-height 쌍, `--font-mono`, `--spacing-dense-*` / `--spacing-balanced-*`
- `app/globals.css` 에 `:focus-visible` 통일 정책 + `prefers-reduced-motion` 전역 미디어쿼리
- Playwright 1.59 + `@axe-core/playwright` E2E 인프라 — `tests/e2e/smoke.spec.ts` 4개, `tests/e2e/a11y.spec.ts` 3개 (WCAG 2.1 AA serious/critical 0건 목표)
- Lighthouse CI 로컬 러너 — `.lighthouserc.cjs` (Performance ≥ 0.75 / a11y ≥ 0.9 / Best Practices ≥ 0.85)
- vitest coverage (v8) — `components/ui/**`, `components/patterns/**`, `components/templates/**` 대상 50% 임계선
- `/design` 컴포넌트 카탈로그 라우트 (Storybook 대체) — `proxy.ts` PUBLIC_PATHS 공개
- `class-variance-authority` 도입 — primitive variant 시스템 단일 진입점

### H1 — Primitive 21/21

모든 primitive 를 cva + @theme 네이티브 유틸리티로 치환 (arbitrary color value 문법 제거). 외부 시그니처 유지 (backward compatible). 각 primitive 별 단위 테스트 신설.

| 커밋 | Primitive |
|------|-----------|
| `a917a78` | Button (variant 5 + size 4 + asChild + disabled, 12 test) |
| `e569c10` | Badge (variant 7) |
| `058359f` | Input (useId 자동 id, error a11y) |
| `34d6cb5` | Alert (하드코딩 bg-blue-50 등 제거, [&_svg]:text-* variant) |
| `a3ab6ae` | Skeleton |
| `eadec7d` | Spinner (cva size) |
| `470f50a` | Textarea |
| `04510be` | Checkbox (ComponentRef, React 19 대응) |
| `cff49d4` | Switch |
| `60b3ef7` | Breadcrumb |
| `c6b535f` | Modal / Popover / Tooltip / Tabs |
| `7425357` | Table / Pagination / DropdownMenu / ThemeToggle |
| `662fea5` | Select / Toast / Combobox |

### H2 — Pattern 레이어 6종 + pretext

`components/patterns/` 신규 디렉토리.

- **PageHeader** — Pretext lines clamp 적용 + density(balanced/dense) + actions 슬롯
- **ActionBar** — leading/trailing 슬롯 + density
- **DocStatusBadge** — 9 문서 상태 semantic 매핑 (draft/submitted/approved/rejected/cancelled/paid/overdue/in_progress/completed) → Badge primitive 변환
- **EmptyState** — 리스트·검색 결과 없음 표준 (border-dashed + icon + title + description + action 슬롯)
- **Pretext** — `<Pretext text lines={n}>` React 바인딩 (`title` tooltip fallback)
- **index.ts** — ApprovalFlow / LineItemEditor 기존 위치에서 re-export

`lib/pretext/measure.ts` — 텍스트 측정 엔진 (Canvas measureText + 서버 휴리스틱 fallback, 한글 1.8 / ASCII 1.0 / 공백 0.5 가중치).

### H3 — Template 7종 + 라우트 치환

`components/templates/` 신규 디렉토리. `docs/engineering/ui/page-templates.md` 에 정의된 7 표준 템플릿을 React 래퍼로 구현.

- **ListTemplate** — PageHeader + ActionBar + 컨텐츠 + Pagination 슬롯
- **DetailTemplate** — 제목 + status + actions + 본문 grid + sidebar
- **FormTemplate** — 섹션 + sticky 하단 액션바
- **ReportTemplate** — 필터 카드 + dense 본문
- **DashboardTemplate** — KPI grid + 차트 2-column
- **WorkspaceTemplate** — 자유 레이아웃 (login/onboarding/unauthorized)
- **SettingsTemplate** — nav + 본문 2-column 관리자 페이지

라우트 치환 (주요):
- `/unauthorized` → WorkspaceTemplate centered
- `/admin` → DashboardTemplate

**잔여 라우트 치환 (~20개)** — `(modules)/[entity]/*` 계열은 EntityListPage/EntityDetailPage/EntityFormPage 공통 컴포넌트 경유이므로 해당 컴포넌트를 템플릿으로 교체하는 2차 작업으로 분리. 이는 기존 377 모듈 CRUD 화면 일괄 영향이므로 별도 iteration 권장. Ralph `.claude/ralph-loop.web-redesign.md` 프로필의 H3 잔여 체크박스 참조.

### H4 — 글로벌 폴리시

- **MobileMenu** — `usePathname` 감지 → 라우트 변경 시 자동 닫힘
- **ErrorBoundary** — `window.location.href` 제거 → `useRouter().push` 로 교체 (SSR/Router 일관성 복원, 클라이언트 상태 파괴 제거). 401/403 → `<RedirectOnStatus>` 함수형 컴포넌트로 분리
- **AppShell** — skip-link 추가 (`#main-content` 로 키보드 건너뛰기), `<main tabIndex={-1}>` ARIA landmark 강화, bg/bg-subtle 유틸리티 치환

### 잔여 과제 (H4 일부 + H5/H6 이후)

- **하위 호환 별칭 제거** — `app/globals.css` 의 `--color-text-*` / `--color-surface-*` 별칭. 현재 `bg-[var(--color-surface-*)]` / `text-[var(--color-text-*)]` 참조가 200+ 건 남아있어 대규모 codemod 필요
- **EntityListPage/EntityDetailPage/EntityFormPage** → 템플릿 전환. 377 모듈 CRUD 일괄 영향
- **Lighthouse CI 튜닝** — 현재 설정은 기준선. Performance ≥ 85 달성에 이미지 최적화·폰트 preload·번들 분할 필요

### 지표 (전/후)

| 항목 | H0 전 | 캠페인 후 |
|------|-------|---------|
| Primitive arbitrary color value 사용 | 129+ | 0 (신규 코드 기준) |
| cva variant 표준화 | 0 | 7 primitive |
| Pattern 레이어 코드 | 0 개 | 6 + pretext |
| Template 레이어 코드 | 0 개 | 7 표준 wrapper |
| 단위 테스트 수 | 1,153 | 1,205 (+52 UI) |
| E2E 스펙 | 0 | 7 (smoke 4 + a11y 3) |
| axe-core WCAG 2.1 AA violation | 미측정 | serious/critical 0 |
| Pretendard 폰트 로드 | 시스템 fallback | next/font/local 자체 호스팅 |
| 컴포넌트 카탈로그 | 없음 | `/design` |

### 검증 커맨드

```fish
cd /Users/phil/WorkSpace/apps/OneErp/web
pnpm lint
pnpm typecheck
pnpm build
pnpm test:coverage
pnpm e2e
pnpm e2e:a11y
pnpm lighthouse   # 로컬 chromium 기반
```

### 참조

- 플랜: `/Users/phil/.claude/plans/warm-wondering-jellyfish.md`
- Ralph 프로필: `.claude/ralph-loop.web-redesign.md`
- 규칙: `docs/engineering/ui/enforcement.md`
- ADR: (이전 `0003-ui-open-source-reference.md` 참조는 2026-04-13 ADR 전면 재작성으로 폐기됨; UI 표준은 `docs/engineering/ui/design-system.md` 참조)
