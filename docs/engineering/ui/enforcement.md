# UI Enforcement Rules

## 목적

OneERP는 디자인 시스템을 "권장 가이드"가 아니라 "허용 경로 제한"으로 운영한다. 이 문서는 신규 화면, 신규 컴포넌트, 신규 variant가 어떤 경로로 추가될 수 있는지와, 어떤 구현 방식이 금지되는지 정리한다.

## 허용 구현 경로

모든 신규 화면은 아래 순서를 따른다.

`template -> pattern -> primitive -> token`

설명:

- template가 정보 구조를 고른다.
- pattern이 업무 패턴을 조합한다.
- primitive가 UI 상호작용을 제공한다.
- token이 시각 언어와 텍스트 측정 계약을 제공한다.

## 계층별 규칙

### Route (`apps/web/app`)

- route는 페이지 조합만 담당한다.
- route에서 `components/ui/*`를 직접 대량 조합하지 않는다.
- route는 template 또는 semantic pattern을 우선 사용한다.

### Primitive (`apps/web/components/ui`)

- 도메인 의미를 가지지 않는다.
- 비즈니스 액션, 상태, approval, entity 개념을 포함하지 않는다.
- variant는 token으로 설명 가능해야 한다.

### Pattern (`apps/web/components/crud`, `layout`, `dashboard`, `approval`, 향후 `patterns`)

- 업무 화면의 재사용 가능한 패턴을 제공한다.
- density mode를 명시한다.
- 긴 텍스트에 대한 overflow 정책 또는 `pretext` 계약을 명시한다.

### Template

- 신규 화면은 7개 표준 템플릿 중 하나를 먼저 선택한다.
- 자유형 레이아웃은 예외 절차 없이는 허용하지 않는다.

## 금지 사항

- route 파일에서 `Button`, `Input`, `Select`, `Badge` 등을 직접 조합해 업무 화면 전체를 구성
- token 확장 없이 ad-hoc Tailwind class를 화면마다 반복 추가
- brand accent와 status semantic을 같은 역할에 혼용
- dense mode를 공식 token 없이 화면별 임시 spacing class로 구현
- 긴 텍스트 컴포넌트에서 clamp/overflow 정책 없이 배포
- semantic pattern이 필요한데 primitive를 복붙 조합으로 별도 구현

## `pretext` 사용 규칙

`pretext`는 선택적 편의 기능이 아니라 OneERP 텍스트 레이아웃 서브시스템의 핵심 엔진으로 본다.

다음 컴포넌트는 우선 적용 대상이다.

- Table primary cell
- KPI card title
- PageHeader title
- Approval comment preview
- Entity card preview
- report/export blocks

규칙:

- text metrics contract를 문서 또는 component API에 명시한다.
- balanced와 dense mode의 허용 줄 수를 분리한다.
- skeleton, preview, rendered content가 같은 높이 계약을 공유하도록 설계한다.

## PR 리뷰 체크리스트

- 이 화면은 어떤 표준 템플릿을 따르는가
- 새 컴포넌트는 primitive인가 pattern인가
- route가 `ui/*`를 직접 과도하게 조합하고 있지 않은가
- 새 variant가 token 확장으로 승격되어야 하는가
- 긴 텍스트가 있는 컴포넌트는 overflow 정책 또는 `pretext` 계약이 있는가
- dense mode 사용이 화면 목적에 맞는가
- status color와 brand accent가 분리되어 있는가

## 예외 절차

다음은 예외로 본다.

- 새 자유형 페이지
- 새 semantic pattern
- 새 density mode
- 새 의미 체계 색상
- 기존 text metrics contract를 벗어나는 텍스트 처리

절차:

1. `docs/plans`에 짧은 설계 문서를 먼저 추가
2. 기존 template/pattern으로 해결되지 않는 이유를 적는다
3. 필요한 새 pattern 또는 새 template을 명시한다
4. 영향 범위를 검토한 뒤 반영한다

구조, 경계, 스택, 권한, 테넌시, 데이터, CI에 영향을 미치면 ADR로 승격한다.

## 운영 원칙

- 문서가 먼저, 구현이 나중이다.
- 예외는 허용하되 무의식적 예외는 금지한다.
- 같은 문제를 두 번 이상 ad-hoc class로 풀었다면 token 또는 pattern으로 승격한다.
