# 시작하기 (Getting Started)

## 사전 조건 (Prerequisites)

- 로그인 URL과 계정이 준비되어 있어야 한다.
- 회사와 사용자 계정이 생성되어 있어야 한다.
- 최소한 대시보드 접근 권한이 있어야 한다.

## 완료 조건 (Completion Criteria)

- 대시보드가 표시된다.
- 좌측 사이드바에서 주요 모듈에 접근할 수 있다.
- 첫 설정 단계로 이동할 수 있다.

## 다음 단계 (Next Step)

- [회계 모듈](./01-accounting.md)

## 첫 로그인 (First Login)

1. 웹 브라우저에서 OneERP 접속 URL을 입력한다. (Enter the OneERP URL in your web browser.)
2. 관리자로부터 발급받은 이메일과 임시 비밀번호로 로그인한다. (Log in with the email and temporary password provided by your administrator.)
3. 최초 로그인 시 비밀번호 변경을 요구할 수 있다. (You may be prompted to change your password on first login.)

## 대시보드 (Dashboard)

로그인 후 대시보드가 표시된다. 대시보드에는 주요 업무 현황이 요약되어 있다:
(After login, the dashboard is displayed with a summary of key business status:)

- **미결 결재건 (Pending Approvals)** — 승인을 기다리는 문서 수 (Number of documents awaiting approval)
- **주요 지표 (Key Metrics)** — 매출 (Revenue), 매입 (Purchase), 재고 현황 (Inventory status) 등
- **최근 활동 (Recent Activity)** — 최근 생성/수정된 문서 목록 (Recently created/modified documents)
- **알림 (Notifications)** — 시스템 알림 및 업무 알림 (System and task notifications)

## 기본 네비게이션 (Basic Navigation)

좌측 사이드바에서 모듈별 메뉴를 선택할 수 있다:
(Select module menus from the left sidebar:)

- **회계 (Accounting)** — 계정과목 (Chart of Accounts), 분개 (Journal Entry), 원장 (General Ledger)
- **판매 (Selling)** — 고객 (Customer), 견적 (Quotation), 판매주문 (Sales Order)
- **구매 (Buying)** — 공급업체 (Supplier), 발주 (Purchase Order), 입고 (Receipt)
- **재고 (Stock)** — 품목 (Item), 창고 (Warehouse), 입출고 (Receipt/Delivery)
- **인사 (HR)** — 직원 (Employee), 부서 (Department), 휴가 (Leave)
- **급여 (Payroll)** — 급여 구조 (Salary Structure), 급여 명세 (Salary Slip)
- **경비 (Expenses)** — 경비 청구 (Expense Claim), 법인카드 (Corporate Card)
- **CRM** — 리드 (Lead), 기회 (Opportunity), 캠페인 (Campaign)
- **자산 (Assets)** — 고정자산 (Fixed Asset), 감가상각 (Depreciation)
- **제조 (Manufacturing)** — BOM, 작업지시 (Work Order)
- **프로젝트 (Projects)** — 프로젝트 (Project), 태스크 (Task)
- **품질 (Quality)** — 검사 (Inspection), 부적합 (Non-Conformance)
- **관리 (Administration)** — 사용자 (User), 역할 (Role), 설정 (Settings)

## 기본 설정 순서 (Initial Setup Steps)

OneERP를 처음 사용할 때 다음 순서로 기본 설정을 진행한다:
(Follow these steps when setting up OneERP for the first time:)

### Step 1: 회사 정보 (Company Information)
1. **관리 (Administration) > 회사 (Company)** 메뉴에서 회사를 등록한다. (Register your company under Administration > Company.)
2. 회사명 (Company Name), 사업자등록번호 (Business Registration Number), 대표자 (Representative), 주소 (Address) 등을 입력한다.
3. 사업자등록 (Business Registration) 정보를 함께 등록한다.

### Step 2: 회계연도 및 통화 (Fiscal Year & Currency)
1. **회계 (Accounting) > 회계연도 (Fiscal Year)** 에서 현재 회계연도를 설정한다. (Set the current fiscal year under Accounting > Fiscal Year.)
2. **관리 (Administration) > 통화 (Currency)** 에서 사용할 통화를 확인한다 (KRW 기본). (Verify the currency — KRW is the default.)
3. 외화 거래가 있다면 환율 (Exchange Rate)을 등록한다. (Register exchange rates if foreign currency transactions are needed.)

### Step 3: 계정과목 체계 (Chart of Accounts)
1. **회계 (Accounting) > 계정과목 (Chart of Accounts)** 에서 계정과목 트리를 확인/수정한다. (Review/edit the chart of accounts tree.)
2. 표준 계정과목이 기본 제공되며, 필요에 따라 추가한다. (Standard accounts are provided by default; add more as needed.)

### Step 4: 사용자 및 역할 (Users & Roles)
1. **관리 (Administration) > 사용자 (User)** 에서 사용자를 등록한다. (Register users under Administration > User.)
2. **관리 (Administration) > 역할 (Role)** 에서 역할을 정의하고 권한 (Permission)을 설정한다.
3. 사용자에게 적절한 역할을 할당한다. (Assign appropriate roles to users.)

### Step 5: 채번 규칙 (Naming Series)
1. **관리 (Administration) > 채번 규칙 (Naming Series)** 에서 문서별 채번 패턴을 설정한다. (Set document numbering patterns.)
2. 예 (Example): 판매주문 (Sales Order) `SO-2026-0001`, 구매주문 (Purchase Order) `PO-2026-0001`

## 공통 기능 (Common Features)

### 문서 목록 (Document List)
- 상단 검색바에서 이름/번호로 검색할 수 있다. (Search by name or number in the top search bar.)
- 컬럼 헤더를 클릭하면 정렬된다. (Click column headers to sort.)
- 필터를 사용하여 조건별로 문서를 찾을 수 있다. (Use filters to find documents by criteria.)

### 문서 생성 (Create Document)
- 목록 화면에서 **"신규 (New)"** 버튼을 클릭한다. (Click the "New" button on the list screen.)
- 필수 항목(*)을 입력한다. (Enter required fields marked with *.)
- **"저장 (Save)"** 버튼으로 초안 (Draft) 상태로 저장한다. (Click "Save" to save as Draft.)
- 트랜잭션 문서는 **"제출 (Submit)"** 버튼으로 확정한다. (Click "Submit" to finalize transaction documents.)

### 문서 상태 (Document Status)
- **초안 (Draft)** — 수정 가능 (Editable)
- **제출 (Submitted)** — 확정, 수정 불가 (Finalized, not editable — cancel and recreate if needed)
- **취소 (Cancelled)** — 취소된 문서 (Cancelled document)
