# UI 레퍼런스(오픈소스) 선정

> 목표: Metronic을 “패턴 분석” 대상으로 두되, 실제 구현은 **오픈소스 레퍼런스**를 기반으로 OneERP의 신규 디자인 시스템(토큰/컴포넌트/템플릿)을 만든다.

## 선정 기준

- 라이선스: 상업적 사용/수정/재배포 가능한 **퍼미시브(MIT/Apache-2.0 등)** 우선
- ERP 화면 적합성: 폼/테이블/필터/워크플로우/대시보드 패턴이 풍부
- 접근성: 키보드/ARIA를 컴포넌트 레벨에서 확보 가능
- 커스터마이징: 토큰/테마 기반으로 “새로운 비주얼 언어”를 만들 수 있어야 함

## 1차 레퍼런스(결정)

### Tabler (Admin/Dashboard UI)

- 용도: 레이아웃/정보 밀도/대시보드 구성/테이블 주변 UI 패턴 레퍼런스
- 라이선스: MIT
- 레퍼런스: https://github.com/tabler/tabler

### Tabler Icons

- 용도: 기본 아이콘 세트(ERP 네비게이션/액션/상태 아이콘)
- 라이선스: MIT
- 레퍼런스: https://github.com/tabler/tabler-icons

## 2차 레퍼런스(보조)

### AdminLTE

- 용도: “관리자 UI”의 표준 패턴(사이드바/폼/테이블/페이지 구조) 보조 레퍼런스
- 라이선스: MIT
- 레퍼런스: https://github.com/ColorlibHQ/AdminLTE

### CoreUI (Bootstrap 기반 UI Kit)

- 용도: Bootstrap 계열 컴포넌트/레이아웃 패턴 참고
- 라이선스: 코드 MIT
- 레퍼런스: https://github.com/coreui/coreui-free-bootstrap-admin-template

## 컴포넌트 프리미티브(구현 기반)

### Radix UI Primitives

- 용도: 접근성 중심 프리미티브(대화상자/드롭다운/툴팁 등)를 기반으로 OneERP 컴포넌트를 구축
- 라이선스: MIT
- 레퍼런스: https://github.com/radix-ui/primitives

## 라이선스 준수 원칙(요약)

- 레퍼런스의 “아이디어/패턴/구조”를 참고하되, OneERP 컴포넌트/스타일은 **신규 구현**을 기본으로 한다.
- 아이콘/코드/에셋을 직접 포함하는 경우, 해당 프로젝트의 LICENSE/NOTICE 준수 절차를 문서화한다.
