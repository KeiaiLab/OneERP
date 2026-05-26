# Design Tokens

## 목표

OneERP 토큰은 시각 스타일을 꾸미는 값 모음이 아니라, 컴포넌트와 텍스트 레이아웃이 공유하는 실행 계약이다. 모든 화면은 토큰을 통해 동일한 브랜드 인상, 동일한 density 정책, 동일한 텍스트 안정성을 유지해야 한다.

## 토큰 계층

### 1. Semantic Color

색은 다음 축으로 나눈다.

- brand accent
- surface
- text
- border
- focus
- status semantic

필수 원칙:

- `blue`, `gray`, `red` 같은 raw palette 이름을 직접 노출하지 않는다.
- 버튼 primary와 선택 상태는 brand accent를 쓴다.
- success, warning, danger, info는 status semantic으로 분리한다.
- 재무 경고와 제품 브랜드를 같은 색 계열로 섞지 않는다.

예시:

- `--color-accent-solid`
- `--color-accent-soft`
- `--color-surface-page`
- `--color-surface-card`
- `--color-surface-muted`
- `--color-border-default`
- `--color-text-primary`
- `--color-text-secondary`
- `--color-status-success`
- `--color-status-warning`
- `--color-status-danger`

### 2. Typography

타이포는 단계 수를 줄이고 스캔 속도를 높이는 방식으로 설계한다.

권장 단계:

- page title
- section title
- card title
- body
- dense body
- meta

필수 원칙:

- 과도한 heading 단계 추가를 금지한다.
- 위계는 size보다 weight와 contrast로 먼저 만든다.
- dense table, approval queue, inspector panel은 별도 dense text token을 쓴다.

### 3. Spacing

기본 scale:

- 2
- 4
- 8
- 12
- 16
- 24
- 32
- 48

필수 원칙:

- spacing은 density mode와 함께 정의한다.
- ad-hoc spacing class를 반복해 화면별 리듬을 바꾸지 않는다.

### 4. Radius

권장 단계:

- `sm`
- `md`
- `lg`

원칙:

- OneERP는 과도한 round를 사용하지 않는다.
- 카드와 패널은 기본적으로 `md` 이하를 유지한다.

### 5. Elevation

권장 단계:

- `none`
- `soft`
- `raised`
- `overlay`

원칙:

- 대부분의 표면은 border 중심으로 구분한다.
- elevation은 modal, popover, drawer, 강조 패널에만 선택적으로 사용한다.

### 6. Motion

토큰화 대상:

- duration
- easing
- enter/exit transitions

원칙:

- motion은 짧고 목적이 있어야 한다.
- hover, focus, toast, drawer, modal 수준으로 제한한다.
- ERP 작업 흐름을 방해하는 장식용 애니메이션은 금지한다.

### 7. Z-index

레이어 규칙:

- base content
- sticky header
- dropdown/popover
- drawer
- modal
- toast
- tooltip

원칙:

- 계층 충돌은 token으로 해결한다.
- 컴포넌트 내부에 임의의 큰 z-index literal을 넣지 않는다.

## Density Tokens

OneERP는 전 화면을 같은 밀도로 운영하지 않는다.

### Balanced Mode

기본 적용:

- detail page
- form page
- dashboard shell
- workspace shell

특징:

- 더 큰 section spacing
- 여유 있는 control height
- 1차 읽기 중심 레이아웃

### Dense Mode

선택 적용:

- table-heavy list
- approval inbox
- admin settings matrix
- line item editor

특징:

- 더 짧은 row height
- 압축된 vertical spacing
- compact text token 사용

규칙:

- dense mode는 화면 목적이 분명할 때만 허용한다.
- dense mode는 spacing만 줄이지 말고 text clamp와 row height도 함께 줄인다.

## Text Metrics Contract

토큰은 `pretext` 기반 텍스트 측정과 연결된다.

관리 항목:

- font family
- font size
- line height
- letter spacing
- max lines
- truncation strategy
- dense/regular mode별 row allowance

예시 개념:

- card title: balanced 2 lines, dense 1 line
- table primary cell: balanced 2 lines, dense 1 line
- table secondary cell: balanced 1 line, dense 1 line
- page header title: balanced 2 lines, dense 1 line
- approval comment preview: balanced 3 lines, dense 2 lines

원칙:

- 긴 텍스트 처리 정책은 CSS clamp만으로 끝내지 않는다.
- 중요한 semantic component는 text metrics contract를 명시한다.
- skeleton, virtualization, overflow UI는 같은 측정 계약을 공유한다.

## Code Mapping

- runtime token source: `apps/web/app/tokens.css`
- global theme application: `apps/web/app/globals.css`
- text layout engine: `apps/web/lib/text-layout`

## 금지 사항

- raw palette class 직접 사용
- component file 내부의 임시 spacing/size literal 남발
- 상태 색상과 브랜드 색상 혼용
- dense mode를 토큰 없이 화면별 class로 구현
- 긴 텍스트를 가진 컴포넌트에서 overflow 정책 미정 상태로 배포

## DoD

- [ ] semantic token taxonomy가 문서와 코드에서 동일한 이름으로 관리된다.
- [ ] balanced/dense mode가 spacing과 text metrics까지 포함해 정의된다.
- [ ] `pretext` 입력값이 될 font metrics와 line allowance가 문서화된다.
- [ ] 컴포넌트가 raw style 값 대신 token 계약을 사용하도록 리뷰 가능해진다.
