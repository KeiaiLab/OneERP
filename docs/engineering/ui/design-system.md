# FE Design System

## 목표

OneERP 프론트엔드는 ERP 화면을 임의 조합으로 만들지 않고, 다음 경로로만 구현한다.

`template -> pattern -> primitive -> token`

이 문서의 목적은 현대적인 프리미엄 SaaS 인상을 유지하면서도, ERP 특유의 높은 텍스트 밀도와 반복 업무 화면을 재사용 가능한 구조로 강제하는 것이다.

## 디자인 방향

- 브랜드 톤: 프리미엄 SaaS형
- 정보 밀도: 균형형
- 기준 원칙:
  - 기본 화면은 여유 있고 정제된 인상
  - 리스트, 테이블, 승인함, 관리자 화면에서만 compact density 허용
  - 브랜드 accent와 상태 색상은 분리
  - 테이블, 카드, 폼, 헤더는 동일한 표면 규칙을 공유

## 단일 소스 오브 트루스

- 토큰: `docs/engineering/ui/tokens.md`
- 컴포넌트 카탈로그: `docs/engineering/ui/components.md`
- 페이지 템플릿: `docs/engineering/ui/page-templates.md`
- CRUD 패턴: `docs/engineering/ui/crud-patterns.md`
- 강제 규칙: `docs/engineering/ui/enforcement.md`

## 계층 구조

### 1. Foundation

코드 위치:

- `apps/web/app/tokens.css`
- `apps/web/app/globals.css`

책임:

- semantic color
- typography scale
- spacing scale
- radius
- elevation
- motion
- z-index
- density tokens
- text metrics contract

규칙:

- raw palette 이름을 직접 사용하지 않는다.
- semantic token만 노출한다.
- density는 spacing뿐 아니라 line clamp와 row height 정책도 포함한다.

### 2. Primitive UI

코드 위치:

- `apps/web/components/ui`

책임:

- Button
- Input
- Select
- Modal
- Tabs
- Tooltip
- Table
- Popover
- Checkbox
- Pagination

규칙:

- 비즈니스 의미를 가지지 않는다.
- Radix UI는 접근성과 상호작용 primitive로만 사용한다.
- 제품 화면은 primitive를 직접 대량 조합하지 않는다.

### 3. ERP Semantic Patterns

코드 위치:

- 권장: `apps/web/components/patterns`
- 현행: `apps/web/components/crud`, `layout`, `dashboard`, `approval`

책임:

- PageHeader
- FilterBar
- ActionBar
- DocStatusBadge
- KPI Card
- ApprovalPanel
- EntityListPage
- EntityFormPage
- EntityDetailPage
- FormSection
- LineItemEditor

규칙:

- 제품 일관성은 이 계층에서 만든다.
- route는 semantic pattern을 우선 사용한다.
- 새 업무 화면은 이 계층 없이 `ui/*`를 직접 조합해서 만들지 않는다.

### 4. Page Templates

책임:

- List
- Detail/Form
- Report
- Dashboard
- Workspace
- Settings/Admin
- Inbox

규칙:

- 신규 화면은 반드시 7개 템플릿 중 하나에 매핑한다.
- 자유형 레이아웃은 예외 승인 없이는 허용하지 않는다.

## 텍스트 레이아웃 서브시스템

OneERP는 긴 한국어 라벨, 다국어 품목명, 승인 의견, dense table cell을 안정적으로 처리해야 한다. 이를 위해 디자인 시스템에 텍스트 측정 계약을 포함한다.

코드 위치:

- `apps/web/lib/text-layout`

핵심 엔진:

- `pretext`

역할:

- multiline line count prediction
- expected height prediction
- clamp/overflow 정책 계산
- dense/regular mode별 허용 줄 수 관리
- skeleton과 실제 렌더 높이 차이 축소

주 적용 대상:

- Table
- EntityCardList
- KPI/Card titles
- PageHeader
- ApprovalPanel
- report/export renderer

## 현재 코드베이스와의 매핑

현재 저장소에는 이미 다음 계층이 존재한다.

- `apps/web/components/ui`
- `apps/web/components/crud`
- `apps/web/components/layout`
- `apps/web/components/dashboard`
- `apps/web/components/approval`
- `apps/web/components/admin`
- `apps/web/components/form`

이 구조는 유지하되, 문서와 리뷰 기준에서는 다음처럼 해석한다.

- `ui` = primitive
- `crud/layout/dashboard/approval/admin/form` = 현행 semantic pattern 집합
- 향후 새 구현은 `patterns`로 통합하거나, 최소한 같은 규칙으로 운영

## 구현 원칙

- 신규 페이지는 템플릿을 먼저 선택한다.
- semantic pattern이 있으면 재사용하고, 없을 때만 새 pattern을 만든다.
- 새 primitive는 도메인 문맥을 가지지 않아야 한다.
- 긴 텍스트를 가진 화면은 `pretext` 기반 측정 계약 또는 명시적 overflow 정책을 반드시 가진다.
- balanced density를 기본으로 하고, dense density는 목적이 명확한 화면에만 적용한다.

## DoD

- [ ] 토큰, pattern, template, text layout contract가 코드 위치와 1:1로 대응된다.
- [ ] 신규 화면 추가 시 템플릿 선택과 예외 기준이 문서로 고정된다.
- [ ] primitive와 semantic pattern의 경계가 리뷰에서 판별 가능하다.
- [ ] `pretext`가 선택적 유틸이 아니라 핵심 텍스트 레이아웃 서브시스템으로 문서화된다.
