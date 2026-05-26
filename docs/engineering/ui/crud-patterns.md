# CRUD UI 패턴 가이드

## 개요

OneERP FE는 `EntityConfig` 기반으로 CRUD 페이지를 자동 생성한다. 모듈별 설정 객체만 정의하면 목록, 상세, 생성, 수정 페이지가 동일한 패턴으로 렌더링된다.

이 CRUD 시스템은 독립적인 편의 기능이 아니라 OneERP 디자인 시스템의 하위 규약이다. 즉 CRUD 화면도 반드시 `template -> pattern -> primitive -> token` 경로를 따른다.

## 디자인 시스템 연결 규칙

- 목록 화면은 `List` 템플릿을 따른다.
- 상세/생성/수정 화면은 `Detail/Form` 템플릿을 따른다.
- `EntityListPage`, `EntityFormPage`, `EntityDetailPage`는 primitive가 아니라 semantic pattern으로 취급한다.
- route 파일은 CRUD semantic pattern을 우선 사용하고, `components/ui/*`를 직접 대량 조합하지 않는다.
- dense mode는 테이블, bulk action, line item editor에만 선택적으로 적용한다.
- 긴 텍스트가 있는 리스트 셀, 헤더, 코멘트 preview는 `pretext` 기반 text metrics contract 또는 명시적 truncation 정책을 가져야 한다.

---

## EntityConfig 구조

모든 엔티티 모듈은 `EntityConfig` 인터페이스를 따르는 설정 객체를 정의한다
(`apps/web/lib/crud/types.ts`).

```typescript
interface EntityConfig {
  entity: string;          // API 경로명 (예: "customers")
  service: ServiceKey;     // 프록시 대상 서비스 (예: "selling")
  label: {
    singular: string;      // 한국어 단수 (예: "고객")
    plural: string;        // 한국어 복수 (예: "고객")
  };
  columns: ColumnDef[];    // 목록 테이블 컬럼
  formFields: FieldDef[];  // 폼 필드
  detailFields?: FieldDef[];  // 상세 표시 필드 (미지정 시 formFields 사용)
  lineItems?: LineItemDef;    // 라인 아이템 (트랜잭션 문서만)
  actions?: ActionDef[];      // 상태전이 액션
  docStatus?: DocStatusConfig; // DocStatus 배지 설정
  idField?: string;           // 기본 ID 필드명
  deletable?: boolean;        // 삭제 가능 여부 (기본: true)
  editable?: boolean;         // 수정 가능 여부 (기본: true)
}
```

### 설정 파일 위치

- 모듈 설정: `apps/web/lib/modules/{entity-name}.ts`
- 레지스트리: `apps/web/lib/modules/index.ts` (자동 생성)
- 타입 정의: `apps/web/lib/crud/types.ts`

---

## CRUD 컴포넌트

### EntityListPage — 목록 페이지

`apps/web/components/crud/entity-list-page.tsx`

`EntityConfig.columns` 기반으로 테이블 + 페이지네이션 + 검색 + "새 문서" 버튼을 렌더링한다.

**기능:**
- `ColumnDef` 기반 동적 테이블 렌더링
- `FormatType`에 따른 값 포맷 (currency, date, number, percent)
- `?page=N&page_size=M` 파라미터를 API에 전달하는 페이지네이션
- 키워드 검색 (디바운스 적용)
- DocStatus 배지 자동 표시

**템플릿 연결:**

- `List` 템플릿의 핵심 pattern이다.
- `PageHeader`, `FilterBar`, `BulkActionBar`, `Pagination`과 함께 사용한다.
- dense content가 허용되는 대표 영역이다.

**텍스트 규칙:**

- 컬럼 텍스트는 기본적으로 overflow 정책을 명시한다.
- 품목명, 거래처명, 설명 컬럼처럼 길어질 수 있는 필드는 줄 수 제한을 가져야 한다.
- virtualization 또는 skeleton height 안정화가 필요할 때 `pretext` 기반 측정 계약을 사용한다.

**사용 예:**

```tsx
import { EntityListPage } from "@/components/crud/entity-list-page";
import { salesOrderConfig } from "@/lib/modules/sales-orders";

export default function SalesOrdersPage() {
  return <EntityListPage config={salesOrderConfig} />;
}
```

### EntityFormPage — 생성/수정 폼

`apps/web/components/crud/entity-form-page.tsx`

`EntityConfig.formFields` 기반으로 동적 폼을 렌더링한다.

**지원 필드 타입:**

| FieldType | 설명 | 렌더링 |
|-----------|------|--------|
| `text` | 텍스트 입력 | `<Input>` |
| `number` | 숫자 입력 | `<Input type="number">` |
| `date` | 날짜 선택 | `<Input type="date">` |
| `select` | 선택 목록 | `<Select>` + `options` |
| `textarea` | 멀티라인 텍스트 | `<Textarea>` |
| `checkbox` | 체크박스 | `<Checkbox>` |
| `currency` | 통화 입력 | `<Input>` + 통화 포맷 |
| `link` | 엔티티 참조 | 검색 가능 드롭다운 (`linkTo` 설정) |

**필드 유효성 검사:**

```typescript
interface FieldValidation {
  min?: number;         // 최소값
  max?: number;         // 최대값
  minLength?: number;   // 최소 길이
  maxLength?: number;   // 최대 길이
  pattern?: string;     // 정규식 패턴
  message?: string;     // 커스텀 에러 메시지
}
```

**레이아웃 (colSpan):**

폼 필드는 12컬럼 그리드에 배치된다.

| colSpan | 너비 | 용도 |
|---------|------|------|
| 3 | 25% | 짧은 코드, 숫자 |
| 4 | 33% | 날짜, 선택 목록 |
| 6 | 50% | 이름, 중간 텍스트 (기본) |
| 12 | 100% | 설명, 메모 |

**템플릿 연결:**

- `Detail/Form` 템플릿의 입력 영역으로 사용한다.
- 기본 density는 balanced다.
- form section 단위로 정보 그룹을 나눈다.

**텍스트 규칙:**

- 긴 placeholder나 설명 텍스트는 field help text 영역으로 분리한다.
- 라벨이 긴 경우 줄바꿈이 전체 그리드를 깨지 않도록 clamp 또는 width policy를 정한다.

### EntityDetailPage — 상세 페이지

`apps/web/components/crud/entity-detail-page.tsx`

읽기전용 상세 뷰 + 상태전이 액션 버튼을 렌더링한다.

**기능:**
- `detailFields` (또는 `formFields`) 기반 읽기전용 렌더링
- `ActionDef` 기반 상태전이 버튼 (제출, 취소 등)
- DocStatus 배지 표시
- 수정/삭제 버튼 (Draft 상태에서만 활성화)

**템플릿 연결:**

- `Detail/Form` 템플릿의 읽기 중심 버전이다.
- 상태 밴드, 승인 패널, 첨부, 활동 로그와 함께 조합된다.

**텍스트 규칙:**

- 제목, 문서명, 거래처명처럼 긴 헤더 텍스트는 clamp 규칙이 필요하다.
- 상세 필드 중 긴 서술형 텍스트는 preview와 full view를 분리한다.

**ActionDef 구조:**

```typescript
interface ActionDef {
  action: string;      // API 액션 경로 (예: "submit", "cancel")
  label: string;       // 버튼 라벨 (예: "제출")
  variant: "primary" | "secondary" | "danger";  // 버튼 스타일
  fromStatus: number[];  // 실행 가능 상태 (예: [0] = Draft에서만)
  confirmMessage?: string;  // 확인 다이얼로그 메시지
}
```

---

## 특수 컴포넌트

### DocStatusBadge — 문서 상태 배지

`apps/web/components/crud/doc-status-badge.tsx`

문서 상태를 시각적으로 표시한다.

| DocStatus | 값 | 배지 색상 | 라벨 |
|-----------|-----|----------|------|
| Draft | 0 | 회색 | 초안 |
| Submitted | 1 | 파란색 | 제출됨 |
| Cancelled | 2 | 빨간색 | 취소됨 |

커스텀 매핑도 가능하다 (`DocStatusConfig`):

```typescript
docStatus: {
  field: "status",
  mapping: {
    "Active": { label: "활성", variant: "success" },
    "Inactive": { label: "비활성", variant: "secondary" },
    "Suspended": { label: "정지", variant: "danger" },
  }
}
```

**디자인 시스템 규칙:**

- `DocStatusBadge`는 primitive `Badge`의 상위 semantic pattern이다.
- 상태 색상은 brand accent를 재사용하지 않고 status semantic token을 쓴다.

### ApprovalFlow — 결재선 스텝퍼

`apps/web/components/approval/ApprovalFlow.tsx`

전자결재 문서의 결재선 진행 상태를 스텝퍼 UI로 표시한다.

**표시 정보:**
- 결재선 순서 (sequence)
- 각 결재자 역할/이름
- 현재 진행 단계 하이라이트
- 승인/반려/대기 상태 아이콘

### LineItemEditor — 라인 아이템 인라인 편집

`apps/web/components/crud/line-item-editor.tsx`

트랜잭션 문서의 라인 아이템을 인라인 테이블로 편집한다.

**기능:**
- 행 추가/삭제
- 인라인 편집 (클릭하여 편집)
- `autoComputeAmount: true` 시 qty * rate → amount 자동 계산
- 합계 자동 계산

**템플릿 연결:**

- `Detail/Form` 템플릿 안에서만 보조 dense zone으로 허용한다.
- 문서 전체 density를 dense로 바꾸지 않고 line item 영역만 dense를 쓴다.

**텍스트 규칙:**

- 품목명, 규격, 설명 컬럼은 dense mode 기준 줄 수 제한이 필요하다.
- line item row height가 흔들리면 `pretext` 측정 계약을 사용한다.

**LineItemDef 구조:**

```typescript
interface LineItemDef {
  key: string;           // 필드명 (예: "items")
  label: string;         // 라벨 (예: "품목")
  columns: LineItemColumnDef[];  // 컬럼 정의
  autoComputeAmount?: boolean;   // qty * rate → amount 자동 계산
}
```

---

## 페이지 레이아웃

### (modules) 레이아웃 — 업무 모듈

사이드바 내비게이션 + 콘텐츠 영역으로 구성된다.

```
┌──────────────────────────────────────────────┐
│  상단 바 (로고, 검색, 사용자 메뉴)            │
├──────────┬───────────────────────────────────┤
│          │                                   │
│ 사이드바  │         콘텐츠 영역               │
│          │                                   │
│ ▸ 판매   │  ┌─────────────────────────────┐  │
│ ▸ 구매   │  │  PageHeader (제목 + 액션)    │  │
│ ▸ 재고   │  ├─────────────────────────────┤  │
│ ▸ 회계   │  │                             │  │
│ ▸ HR     │  │  목록 테이블 / 폼 / 상세     │  │
│ ▸ 급여   │  │                             │  │
│ ▸ 경비   │  │                             │  │
│ ▸ CRM    │  └─────────────────────────────┘  │
│ ▸ 자산   │                                   │
│ ▸ 프로젝트│                                   │
│ ▸ 품질   │                                   │
│          │                                   │
├──────────┴───────────────────────────────────┤
│  하단 바 (버전 정보)                          │
└──────────────────────────────────────────────┘
```

### (admin) 레이아웃 — 관리자 전용

시스템 설정, 사용자 관리, 역할/권한 설정 등 관리자 기능에 사용된다.
Tenant Admin 이상 권한이 필요하다.

관리자 화면은 shell 자체는 balanced를 유지하되, 권한 매트릭스나 토글 매트릭스 같은 실제 내용 영역은 dense mode를 허용한다.

---

## 텍스트 측정 규칙

CRUD 계층은 다음 경우 `pretext` 기반 text metrics contract를 사용하거나, 최소한 동일한 overflow 정책을 명시해야 한다.

- 목록 테이블의 긴 primary text cell
- Entity card list의 제목/보조 정보
- 상세 페이지 header의 긴 문서명
- approval 또는 activity preview
- line item editor의 긴 품목명과 설명

원칙:

- balanced mode와 dense mode는 허용 줄 수가 다르다.
- skeleton, preview, 실제 텍스트 block은 같은 높이 계약을 공유한다.
- 테이블과 카드에서 "자동으로 적당히 줄바꿈"되는 상태를 허용하지 않는다.

---

## 모듈 추가 방법

새 엔티티의 CRUD 페이지를 추가하려면:

1. `apps/web/lib/modules/{entity-name}.ts`에 `EntityConfig` 정의
2. `apps/web/lib/modules/index.ts`에 import + 레지스트리 등록
3. App Router 경로에 페이지 파일 생성

BE에서 `EntityMeta`로 API가 자동 생성되므로, FE는 `EntityConfig`만 정의하면 전체 CRUD가 작동한다.
