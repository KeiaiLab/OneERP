# 관리자 모듈 (Administration Module)

## 개요 (Overview)

관리자 모듈은 사용자 관리 (User Management), 역할/권한 설정 (Role/Permission), 회사/테넌트 관리 (Company/Tenant), 시스템 설정 (System Settings), 채번 규칙 (Naming Series) 등 시스템 전반의 관리 기능을 제공한다.

## 사전 조건 (Prerequisites)

- Super Admin 또는 Company Admin 권한이 있어야 한다.
- 테넌트와 회사 정보를 수정할 수 있어야 한다.
- 기본 관리 작업에 접근할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 사용자, 역할, 회사, 테넌트, 채번 규칙 화면의 목적을 이해한다.
- 초기 설정과 운영 설정의 진입점을 구분할 수 있다.
- 다음 설정 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [초기 설정 튜토리얼](../tutorials/10-admin-setup.md)

## 주요 기능 (Key Features)

- 사용자 관리 (User Management)
- 역할 및 권한 (Role & Permission)
- 회사 관리 (Company Management)
- 테넌트 관리 (Tenant Management)
- 통화 관리 (Currency Management)
- 시스템 설정 (System Settings)
- 채번 규칙 (Naming Series)
- 워크플로우 정의 (Workflow Definition)
- 감사 추적 (Audit Trail)
- 플랜 관리 (Plan Management): Starter / Standard / Enterprise

## 업무 흐름 (Workflow)

```
테넌트 생성        회사 등록          사용자/역할 설정       시스템 설정
(Tenant Create) → (Company Reg.) → (User/Role Setup)  → (System Config)
```

## 상세 기능 (Detailed Features)

### 사용자 관리 (User Management)

#### 생성 (Create)
1. **관리 (Administration) > 사용자 (User)** 에서 **"신규 (New)"** 를 클릭한다.
2. 이메일 (Email, 로그인 ID Login ID), 이름 (Name)을 입력한다.
3. 역할 (Role)을 할당한다 (복수 선택 가능 Multiple selection allowed).
4. 소속 회사 (Company), 부서 (Department)를 지정한다.
5. 인증 제공자 (Authentication Provider)를 `password` 또는 `oidc`로 선택하고, OIDC 연동 계정이면 subject를 매핑하거나 초대 상태를 `pending`으로 기록한다.
6. 저장 후 사용자 목록은 `summary`, `status_badge`, `recommended_action`, `available_actions`, `access_summary`, `auth_summary`를 함께 보여 주므로 OIDC 연동, 초대 대기, 관리자 권한 범위를 한 화면에서 점검할 수 있다.

#### 비활성화 (Deactivate)
1. 퇴직 (Resignation) 등의 사유로 사용자를 비활성화 (Deactivate)한다.
2. 비활성화된 사용자는 로그인할 수 없다. (Deactivated users cannot log in.)
3. 데이터는 보존된다. (Data is preserved.)
4. 활성 사용자 (Active User)는 바로 삭제할 수 없으며, 먼저 비활성화한 뒤 삭제해야 한다.

### 역할 및 권한 (Role & Permission)

#### 역할 정의 (Define Role)
1. **관리 (Administration) > 역할 (Role)** 에서 **"신규 (New)"** 를 클릭한다.
2. 역할명 (Role Name)을 입력한다 (예 Example: 회계담당자 Accountant, 구매관리자 Purchase Manager, 인사관리자 HR Manager).
3. **"저장 (Save)"** 을 클릭한다.

#### 권한 설정 (Permission Setup)
1. **관리 (Administration) > 역할 권한 (Role Permission)** 에서 역할별 접근 권한을 설정한다.
2. 모듈별로 읽기 (Read)/쓰기 (Write)/삭제 (Delete)/제출 (Submit) 권한을 설정한다.
3. 필드 수준 권한 (Field Level Permission)도 설정할 수 있다.

#### 기본 제공 역할 (Default Roles)
- **시스템 관리자 (System Administrator)** — 전체 권한 (Full Access)
- **회계 관리자 (Accounting Manager)** — 회계 모듈 전체 권한 (Full access to Accounting module)
- **영업 담당자 (Sales User)** — 판매 모듈 제한적 권한 (Limited access to Selling module)
- **일반 사용자 (General User)** — 기본 읽기 권한 (Basic read access)

### 회사 관리 (Company Management)

#### 회사 정보 (Company Information)
1. **관리 (Administration) > 회사 (Company)** 에서 회사 기본 정보를 관리한다.
2. 회사명 (Company Name), 회사 코드 (Company Code), 사업자등록번호 (Business Registration No.), 대표자 (Representative), 주소 (Address)를 입력한다.
3. 기본 통화 (Default Currency), 회계연도 (Fiscal Year), 기본 회사 여부 (Default Company)를 설정한다.
4. 상위 회사 (Parent Company)를 지정하면 본사-사업장 계층을 구성할 수 있다.
5. 회사 목록은 상태 배지 (Status Badge), 기본/지사 여부, 하위 회사 수, 권장 액션 (Recommended Action)을 함께 보여 주므로 멀티컴퍼니 운영 상태를 한 화면에서 점검할 수 있다.
6. 기본 회사는 다른 회사를 기본값으로 전환하기 전에는 삭제할 수 없다. 회사 전환기 (Company Switcher)의 기본 컨텍스트를 보호하기 위한 안전 장치다.

#### 사업자등록 (Business Registration)
1. **관리 (Administration) > 사업자등록 (Business Registration)** 에서 사업자등록증 정보를 관리한다.
2. 업태 (Business Type), 종목 (Business Category), 사업장 주소 (Business Address)를 입력한다.

### 테넌트 관리 (Tenant Management)

1. **관리 (Administration) > 테넌트 (Tenant)** 에서 멀티테넌트 환경 (Multi-tenant Environment)을 관리한다.
2. 각 테넌트 (Tenant)는 독립된 데이터 공간 (Isolated Data Space)을 가진다.
3. 테넌트별 설정 (Settings), 사용자 (Users)를 관리한다.

### 통화 관리 (Currency Management)

1. **관리 (Administration) > 통화 (Currency)** 에서 사용할 통화를 등록한다. (Register currencies to use.)
2. 통화 코드는 ISO 4217 3자리 대문자로 저장되며, 활성 통화만 **카탈로그 (Catalog)** 에 노출된다.
3. 기본 통화 (Default Currency: KRW)는 비활성화하거나 삭제할 수 없다.
4. 회사 기본 통화 또는 시스템 기본 통화로 참조 중인 통화는 삭제할 수 없다.
5. 환율 (Exchange Rate)은 **회계 (Accounting) > 환율 (Exchange Rate)** 에서 관리한다.

### 시스템 설정 (System Settings)

1. **관리 (Administration) > 시스템 설정 (System Settings)** 에서 전역 설정 (Global Settings)을 관리한다.
2. 날짜 형식 (Date Format), 시간대 (Timezone), 언어 (Language) 등을 설정한다.
3. 이메일 발송 설정 (Email Configuration)을 구성한다.

### 채번 규칙 (Naming Series)

#### 설정 (Setup)
1. **관리 (Administration) > 채번 규칙 (Naming Series)** 에서 문서별 채번 패턴 (Numbering Pattern)을 설정한다.
2. 접두사 (Prefix), 연도 (Year), 월 (Month), 일련번호 (Sequence) 형식을 조합한다.
3. 예시 (Examples):
   - 판매주문 (Sales Order): `SO-{YYYY}-{####}` → SO-2026-0001
   - 구매주문 (Purchase Order): `PO-{YYYY}-{####}` → PO-2026-0001
   - 분개 (Journal Entry): `JE-{YYMM}-{####}` → JE-2603-0001

### 워크플로우 정의 (Workflow Definition)

1. **관리 (Administration) > 워크플로우 정의 (Workflow Definition)** 에서 문서 유형별 상태 흐름 (State Flow)을 정의한다.
2. 상태 (States: 초안 Draft → 제출 Submitted → 승인 Approved → 취소 Cancelled)를 설정한다.
3. 각 상태 전환 (State Transition) 시 실행할 액션 (Action)을 지정한다.

### 감사 추적 (Audit Trail)

1. 시스템의 모든 주요 작업은 감사 추적 로그 (Audit Trail Log)에 기록된다.
2. 누가 (Who), 언제 (When), 어떤 문서를 (What), 어떻게 변경했는지 (How) 추적한다.
3. **관리 (Administration)** 영역에서 감사 로그를 조회할 수 있다.

## 관련 보고서 (Related Reports)

- 사용자 활동 로그 (User Activity Log)
- 역할별 사용자 현황 (Users by Role)
- 감사 추적 보고서 (Audit Trail Report)

## FAQ

- **Q: 플랜 (Plan)별 차이는 무엇인가요?**
  A: Starter는 기본 기능, Standard는 고급 기능 포함, Enterprise는 전체 기능 및 전용 지원을 제공합니다. (Starter has basic features, Standard includes advanced features, Enterprise provides full features with dedicated support.)

- **Q: 사용자를 삭제 (Delete)할 수 있나요?**
  A: 데이터 무결성을 위해 삭제 대신 비활성화 (Deactivate)를 권장합니다. (Deactivation is recommended instead of deletion for data integrity.)

- **Q: 멀티테넌트 (Multi-tenant)란 무엇인가요?**
  A: 하나의 시스템에서 여러 조직이 독립된 데이터로 운영하는 구조입니다. (A single system serving multiple organizations with isolated data.)
