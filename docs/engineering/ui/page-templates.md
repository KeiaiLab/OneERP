# 페이지 템플릿

## 목표

OneERP의 신규 화면은 자유형 레이아웃에서 시작하지 않는다. 먼저 페이지 템플릿을 고르고, 그 다음 semantic pattern을 조합한다. 템플릿은 정보 구조, 액션 위치, density 기본값, 감사 및 권한 표시 방식을 함께 고정한다.

## 표준 템플릿

### 1. List

용도:

- 검색, 필터, 정렬, 페이지네이션, bulk action이 핵심인 화면

기본 구조:

- PageHeader
- FilterBar
- BulkActionBar
- Table 또는 EntityCardList
- Pagination

기본 density:

- balanced shell
- dense content allowed

필수 규칙:

- primary action은 우상단에 둔다.
- 검색과 필터는 상단에 고정된 위치를 가진다.
- 긴 셀 텍스트는 `pretext` 기반 줄 수 정책 또는 명시적 truncation 정책을 가진다.

### 2. Detail/Form

용도:

- 문서 보기, 생성, 수정, 승인, 첨부, 댓글, 활동 로그

기본 구조:

- PageHeader
- Summary or status band
- FormSection group
- LineItemEditor if needed
- Approval panel / attachments / activity log

기본 density:

- balanced

필수 규칙:

- 기본은 읽기와 편집의 명확한 분리
- 상세 header의 긴 제목은 clamp 정책을 가진다.
- line item 영역만 dense mode를 허용한다.

### 3. Report

용도:

- 파라미터 입력 후 결과 테이블, 차트, export를 제공하는 화면

기본 구조:

- PageHeader
- Report parameter panel
- Result summary
- Table and/or chart area
- Export actions

기본 density:

- balanced shell
- dense result grid allowed

필수 규칙:

- 파라미터 입력과 결과 영역을 시각적으로 분리한다.
- chart와 table의 우선순위는 리포트 목적에 따라 결정한다.

### 4. Dashboard

용도:

- KPI, feed, queue, chart, alerts를 조합하는 개요 화면

기본 구조:

- PageHeader
- KPI grid
- chart/widget rows
- queue/feed panels

기본 density:

- balanced

필수 규칙:

- 카드 자체는 여유 있게 유지한다.
- 카드 내부 수치와 메타만 compact를 허용한다.
- 긴 카드 제목은 두 줄을 넘기지 않는다.

### 5. Workspace

용도:

- 모듈 진입점, 바로가기, 최근 작업, 개요를 보여주는 화면

기본 구조:

- PageHeader
- workspace hero or summary block
- quick links
- recent items
- recommended actions

기본 density:

- balanced

### 6. Settings/Admin

용도:

- 마스터 데이터, 권한, 워크플로우 설정, 매트릭스형 편집

기본 구조:

- PageHeader
- left navigation or tab navigation
- dense matrix or settings forms
- save/apply actions

기본 density:

- balanced shell
- dense content allowed

필수 규칙:

- matrix, permission grid, module toggle은 dense mode 허용
- 설명 텍스트와 실제 설정 영역을 명확히 분리한다.

### 7. Inbox

용도:

- 승인, 할당, 알림 기반 업무 큐

기본 구조:

- PageHeader
- queue filter controls
- list/table
- preview pane or detail panel

기본 density:

- dense default

필수 규칙:

- queue scanning 속도가 최우선
- preview text는 `pretext` 기반 preview line count를 가진다.

## 템플릿 선택 규칙

- 신규 화면은 반드시 7개 템플릿 중 하나를 먼저 선택한다.
- 템플릿 선택은 요구사항 문서 또는 설계 문서에 남긴다.
- 하나의 화면에서 템플릿을 혼합해야 한다면, 주 템플릿 하나를 기준으로 부속 패턴을 추가한다.

## 예외 규칙

다음 경우에만 템플릿 예외를 허용한다.

- 기존 7개 템플릿으로 핵심 정보 구조를 설명할 수 없는 경우
- 제품 차별화가 필요한 새 업무 흐름인 경우
- 보고/설정/승인/상세 패턴을 동시에 포함하는 특수 콘솔인 경우

예외 절차:

- `docs/plans`에 짧은 설계 문서를 먼저 추가
- 왜 기존 템플릿으로 안 되는지 설명
- 필요한 새 pattern 또는 새 template 정의

## 화면별 표준화 항목

모든 템플릿은 다음을 같이 정의해야 한다.

- 기본 density
- 주 액션 위치
- 보조 액션 위치
- 권한/상태/감사 정보 노출 위치
- text overflow 처리 원칙
- 사용해야 할 semantic pattern 목록

## DoD

- [ ] 신규 화면이 표준 템플릿에서 시작하도록 문서화된다.
- [ ] 템플릿별 density, 액션 위치, text overflow 원칙이 고정된다.
- [ ] 자유형 페이지는 예외 절차 없이는 허용되지 않는다.
