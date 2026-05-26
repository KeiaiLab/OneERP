# 컴포넌트 카탈로그

## 목표

OneERP 화면은 primitive UI를 직접 쌓아 올리는 방식이 아니라, semantic pattern과 page template을 통해 구성한다. 이 문서는 어떤 컴포넌트가 어느 계층에 속하는지와 각 계층의 책임을 고정한다.

## 계층

### Primitive UI

위치:

- `apps/web/components/ui`

책임:

- 시각적, 상호작용적 기본 부품
- 도메인 의미를 모르는 범용 UI
- token 기반 variant만 제공

대표 컴포넌트:

- Button
- Input
- Textarea
- Select
- Combobox
- Checkbox
- Switch
- Modal
- DropdownMenu
- Popover
- Tabs
- Tooltip
- Badge
- Table
- Skeleton
- Spinner
- Pagination

규칙:

- business action, approval, docstatus, entity 개념을 포함하지 않는다.
- route 파일에서 primitive를 대량 조합해 화면을 직접 구성하지 않는다.
- 새 variant는 token 계약으로 설명 가능해야 한다.

### Semantic Patterns

위치:

- 현행: `apps/web/components/crud`
- 현행: `apps/web/components/layout`
- 현행: `apps/web/components/dashboard`
- 현행: `apps/web/components/approval`
- 현행: `apps/web/components/admin`
- 현행: `apps/web/components/form`
- 권장 통합 경로: `apps/web/components/patterns`

책임:

- ERP 업무 패턴 캡슐화
- density mode 적용
- `pretext` 기반 text metrics contract 적용
- 페이지 템플릿이 재사용할 조합 단위 제공

대표 컴포넌트:

- PageHeader
- Sidebar
- ActionBar
- BulkActionBar
- DocStatusBadge
- EntityListPage
- EntityFormPage
- EntityDetailPage
- LineItemEditor
- ApprovalFlow
- ApprovalPanel
- KPI Card
- KPI Grid
- ActivityFeed

규칙:

- semantic pattern은 업무 맥락을 포함해도 된다.
- semantic pattern은 primitive보다 상위 계층이며, route는 이를 우선 사용한다.
- semantic pattern은 텍스트 overflow 정책을 명시해야 한다.

### Page Templates

위치:

- 권장: `apps/web/components/templates`
- 문서 SoT: `docs/engineering/ui/page-templates.md`

책임:

- 전체 화면 조합 규칙
- 공통 header/filter/footer placement
- density 기본값
- semantic pattern 조합 순서

## 카탈로그 규칙

### Primitive에 넣는 기준

- 도메인 문맥 없이 재사용 가능
- button/input/select 수준의 범용성
- variant가 token으로 설명 가능

### Semantic Pattern에 넣는 기준

- ERP 문맥이 있다
- 공통 레이아웃이나 업무 플로우를 포함한다
- 여러 primitive와 토큰 규칙을 조합한다
- 텍스트 밀도, 상태 배지, 액션 위치, 승인 상태 같은 규칙을 내장한다

### Template에 넣는 기준

- 페이지 전체 구조를 결정한다
- 어떤 pattern을 어디에 놓는지 표준화한다
- 동일한 화면군의 정보 구조를 강제한다

## 아이콘 정책

- 기본 아이콘 세트: Tabler Icons
- 아이콘은 semantic meaning보다 role-based로 사용한다.
- size, stroke, color는 token으로 제어한다.
- pattern 계층은 아이콘 팩에 직접 결합하지 말고 adapter 형태를 유지한다.

## Text Layout 책임

긴 텍스트를 갖는 다음 컴포넌트는 `pretext` 기반 측정 계약을 따라야 한다.

- Table primary cell
- KPI card title
- PageHeader title/subtitle
- Approval comment preview
- Entity card preview
- report/export block

규칙:

- clamp 여부를 component API에서 명시한다.
- dense와 balanced mode에서 허용 줄 수를 달리 정의한다.
- skeleton과 실제 content 높이가 크게 어긋나지 않게 한다.

## 금지 사항

- route 파일에서 `components/ui/*`만으로 업무 화면 전체를 직접 구성
- semantic pattern이 필요한데 primitive를 중복 조합해 별도 구현
- token 확장 없이 개별 컴포넌트에 임시 class 추가 반복
- `DocStatus`, `ApprovalAction`, `FilterBar` 같은 업무 패턴을 primitive 계층에 배치

## DoD

- [ ] primitive와 semantic pattern이 문서와 코드에서 동일하게 분리된다.
- [ ] pattern 계층의 대표 컴포넌트가 제품 표준으로 정의된다.
- [ ] 신규 화면이 primitive 직접 조합이 아니라 pattern/template을 사용하도록 리뷰 가능해진다.
- [ ] 텍스트 측정이 필요한 컴포넌트가 명시된다.
