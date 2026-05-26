# 회계 모듈 (Accounting Module)

## 개요 (Overview)

회계 모듈은 계정과목 관리 (Chart of Accounts), 분개 처리 (Journal Entry), 총계정원장 (General Ledger), 매출채권/매입채무 (Accounts Receivable/Payable), 은행대사 (Bank Reconciliation), 예산 관리 (Budget), 결산 (Period Closing), 세금 신고 (Tax Filing) 등 재무회계 전반을 지원한다.

## 사전 조건 (Prerequisites)

- 회사와 기본 통화가 설정되어 있어야 한다.
- 계정과목표가 준비되어 있어야 한다.
- 회계 관련 권한이 부여되어 있어야 한다.

## 완료 조건 (Completion Criteria)

- 계정과목, 분개, 원장, AR/AP 화면의 기본 사용법을 이해한다.
- 자동 분개가 발생하는 흐름을 확인한다.
- 회계 관련 보고서를 조회할 수 있다.

## 다음 단계 (Next Step)

- [경비 모듈](./07-expenses.md)

## 관련 튜토리얼 (Related Tutorials)

- [판매→수금 튜토리얼](../tutorials/01-order-to-cash.md)
- [구매→지급 튜토리얼](../tutorials/02-procure-to-pay.md)

## 주요 기능 (Key Features)

- 계정과목 관리 (Chart of Accounts Management)
- 분개 처리 (Journal Entry Processing)
- 총계정원장 조회 (General Ledger Inquiry)
- 매출채권 (Accounts Receivable, AR) / 매입채무 (Accounts Payable, AP) 관리
- 은행대사 (Bank Reconciliation)
- 예산 관리 (Budget Management)
- 기간 마감 (Period Closing)
- 세금 관리 (Tax Management)

## 업무 흐름 (Workflow)

```
분개 입력 (Journal Entry) → 제출 (Submit) → 원장 반영 (Post to Ledger)
                                                  ↓
                                    재무제표 (Financial Statements)
```

## 상세 기능 (Detailed Features)

### 계정과목 관리 (Chart of Accounts Management)

#### 조회 (View)
1. **회계 (Accounting) > 계정과목 (Chart of Accounts)** 메뉴를 선택한다. (Navigate to Accounting > Chart of Accounts.)
2. 트리 형태로 계정과목 체계가 표시된다. (The chart of accounts is displayed in a tree structure.)
3. 계정과목을 클릭하면 상세 정보를 확인할 수 있다. (Click an account to view details.)

#### 생성 (Create)
1. 상위 계정을 선택한 후 **"하위 계정 추가 (Add Sub-Account)"** 를 클릭한다. (Select a parent account and click "Add Sub-Account".)
2. 계정 코드 (Account Code), 계정명 (Account Name), 계정 유형 (Account Type: 자산 Asset/부채 Liability/자본 Equity/수익 Revenue/비용 Expense)을 입력한다.
3. **"저장 (Save)"** 버튼을 클릭한다. (Click "Save".)

### 분개 처리 (Journal Entry Processing)

#### 생성 (Create)
1. **회계 (Accounting) > 분개 (Journal Entry)** 메뉴에서 **"신규 (New)"** 를 클릭한다. (Navigate to Accounting > Journal Entry and click "New".)
2. 분개 유형 (Entry Type: 일반분개 General Entry, 기초잔액 Opening Entry 등)을 선택한다.
3. 차변 (Debit)/대변 (Credit) 계정과 금액을 입력한다. 차변 합계와 대변 합계가 일치해야 한다. (Enter debit/credit accounts and amounts. Debit and credit totals must match.)
4. 적요 (Remarks)를 입력하고 **"저장 (Save)"** 한다.
5. 확인 후 **"제출 (Submit)"** 하면 원장 (Ledger)에 반영된다.

#### 승인 요청 (Request Approval)
1. 초안 분개전표에서 **"승인 요청 (Request Approval)"** 을 클릭한다.
2. 결재자 사용자 ID와 요청 코멘트를 입력한다.
3. 시스템은 `approval_status=pending` 으로 전환하고 승인 대기 중에는 수정/삭제를 막는다.
4. 지정 결재자는 **"승인 (Approve)"** 또는 **"반려 (Reject)"** 를 선택한다.
5. 승인되면 전표가 자동 제출되어 원장에 반영되고, 반려되면 반려 사유를 확인한 뒤 수정 후 다시 승인 요청한다.

#### 초안 삭제 (Delete Draft)
1. 아직 제출하지 않은 분개전표를 열고 **"삭제 (Delete)"** 를 클릭한다.
2. 시스템은 초안 상태인지 확인한 뒤 삭제를 수행한다.
3. 승인 대기 중인 전표는 삭제할 수 없으며, 이 경우 **"승인 대기 중인 전표는 삭제할 수 없습니다"** 메시지가 표시된다.
4. 제출된 전표도 삭제할 수 없으며, 이 경우 **"초안 상태에서만 삭제할 수 있습니다"** 메시지가 표시된다.

#### 반복 전표 템플릿 (Recurring Journal Template)
1. 자주 쓰는 월말 조정 분개는 **"템플릿 저장 (Save as Template)"** 으로 템플릿화한다.
2. 템플릿명, 반복 주기 (daily/weekly/monthly/quarterly/yearly), 다음 전기일, 기본 결재자를 저장한다.
3. 다음 회차에는 **"템플릿으로 생성 (Create from Template)"** 을 눌러 전기일만 입력하면 같은 라인 구조의 초안 전표가 만들어진다.
4. 템플릿으로 생성된 분개는 `template_id`를 보존하며, 사용 시 템플릿의 다음 전기일과 사용 횟수가 함께 갱신된다.

#### 자동 분개 (Auto Journal Entry)
매출 송장 제출 (Sales Invoice Submit), 구매 송장 제출 (Purchase Invoice Submit), 급여 처리 (Payroll Processing), 감가상각 (Depreciation), 기간마감 (Period Closing) 등에서 자동으로 분개가 생성된다.

### 총계정원장 (General Ledger)

1. **회계 (Accounting) > 총계정원장 (General Ledger)** 메뉴를 선택한다.
2. 계정과목 (Account), 조회 시작일/종료일 (Posting Date From/To), 원천 전표 번호 (Voucher No)를 지정하여 제출된 분개만 조회한다.
3. 필요하면 원천 전표 유형 (Voucher Type)과 원가센터 (Cost Center)까지 지정해 원장을 더 좁힐 수 있다.
4. 목록에서 각 라인의 차변 (Debit)/대변 (Credit), 누적 잔액 (Running Balance), 원가센터 (Cost Center), 원천 전표 번호를 확인한다.
5. 특정 라인을 클릭하면 원본 분개전표 ID와 적요 (Remarks)를 드릴다운하여 확인할 수 있다.

### 원가센터 관리 (Cost Center Management)

1. **회계 (Accounting) > 원가센터 (Cost Centers)** 메뉴를 선택한다.
2. **"신규 (New)"** 에서 회사 (Company), 원가센터명 (Cost Center Name), 상위 원가센터 (Parent Cost Center), 그룹 여부 (Group)을 입력한다.
3. 같은 회사 안에서는 동일한 원가센터명을 중복 저장할 수 없고, 상위 원가센터는 반드시 기존 원가센터여야 한다.
4. **트리 보기 (Tree View)** 는 회사별 건수 요약과 부모-자식 구조를 함께 표시하므로, 본사/부서/프로젝트 단위 비용 배부 체계를 한 번에 확인할 수 있다.
5. 하위 원가센터가 있거나 분개/예산에서 이미 사용한 원가센터는 삭제할 수 없다. 이 경우 삭제 대신 새 원가센터로 전환한 후 참조 문서를 정리해야 한다.

### 매출채권 관리 (Accounts Receivable Management)

1. **회계 (Accounting) > 매출채권 (Accounts Receivable)** 메뉴를 선택한다.
2. 고객 (Customer), 원천 송장 번호 (Voucher No), 기준일 (As of Date)을 지정해 고객별 미수금 (Outstanding) 현황을 조회한다.
3. 결제 기한 범위 (Due Date From/To), 연체만 보기 (Overdue Only), 최소/최대 연체일수 (Overdue Days)로 필터링할 수 있다.
4. 목록 하단의 요약 영역에서 총 미수금, 연체 미수금, 연령분석 (Aging Buckets: current / 1-30 / 31-60 / 61-90 / 91+)과 고객별 우선 추적 목록을 함께 확인한다.
5. 특정 라인을 클릭하면 고객별 미수금 합계, 최근 독촉 단계, 권장 후속 액션 (`register_payment`, `create_dunning`, `view_dunning_history`)을 확인할 수 있다.

### 매입채무 관리 (Accounts Payable Management)

1. **회계 (Accounting) > 매입채무 (Accounts Payable)** 메뉴를 선택한다.
2. 공급업체 (Supplier), 원천 송장 번호 (Voucher No), 기준일 (As of Date)을 지정해 공급업체별 미지급금 (Outstanding) 현황을 조회한다.
3. 지급 기한 범위 (Due Date From/To), 연체만 보기 (Overdue Only), 최소/최대 연체일수 (Overdue Days), 상태 배지 (Status Badge)로 지급 우선순위를 좁힐 수 있다.
4. 목록 하단의 요약 영역에서 총 미지급금, 연체 미지급금, 연령분석 (Aging Buckets: current / 1-30 / 31-60 / 61-90 / 91+)과 공급업체별 우선 지급 목록을 함께 확인한다.
5. 특정 라인을 클릭하면 공급업체별 미지급금 합계, 다음 지급 예정일, 권장 후속 액션 (`register_payment`, `create_payment_order`)과 지급 일정 요약을 확인할 수 있다.

### 은행대사 (Bank Reconciliation)

#### 은행 거래 명세 가져오기 (Import Bank Statement)
1. **회계 (Accounting) > 은행 거래 명세 가져오기 (Import Bank Statement)** 에서 은행 파일을 업로드한다. (Upload the bank statement file.)
2. 시스템이 자동으로 거래를 매칭한다. (The system automatically matches transactions.)
3. 매칭되지 않는 항목은 수동으로 처리한다. (Unmatched items are processed manually.)

#### 은행대사 실행 (Run Bank Reconciliation)
1. **회계 (Accounting) > 은행대사 (Bank Reconciliation)** 에서 은행계좌 (Bank Account)를 선택한다.
2. 기간 (Period)을 지정하고 **"대사 실행 (Run Reconciliation)"** 을 클릭한다.
3. 매칭 결과를 확인하고 **"확정 (Confirm)"** 한다.

### 예산 관리 (Budget Management)

1. **회계 (Accounting) > 예산 (Budget)** 에서 부서 (Department)/프로젝트 (Project)별 예산을 등록한다.
2. 예산 목록 상단의 워크벤치에서 전체 예산, 집행액, 잔여액, `near_limit`/`over_budget` 건수를 바로 확인한다.
3. 상세 화면에서 `budget_usage_summary`, `version_summary`, `transfer_summary`를 확인해 현재 집행률과 최신 조정 버전, 예산 이전 대기 건을 함께 점검한다.
4. 예산 초과 시 `status_badge=over_budget`와 `recommended_action=create_budget_transfer`가 표시된다. 필요한 경우 **예산 이전 (Budget Transfer)** 문서를 만들어 대응한다.

### 기간 마감 (Period Closing)

#### 회계기간 운영 워크벤치
1. **회계 (Accounting) > 회계기간 (Accounting Period)** 화면에서 `status_badge=close_ready` 필터를 사용하면 즉시 마감 가능한 기간만 볼 수 있다.
2. 목록과 상세는 `period_scope_summary`와 `close_validation_summary`를 함께 보여준다. `draft_count > 0`이면 `status_badge=close_blocked`, `recommended_action=review_draft_entries`가 표시된다.
3. 마감된 기간은 `status_badge=closed_reopenable`로 바뀌고 `available_actions`에 `reopen`이 노출된다. 회계연도가 이미 결산되었으면 `status_badge=year_closed`로 표시되어 재개할 수 없다.
4. 회계기간 삭제는 열린 상태이면서 연결된 분개전표가 없을 때만 허용된다. 마감된 기간이나 분개전표가 있는 기간은 삭제되지 않는다.

#### 월마감 (Monthly Closing)
1. **회계 (Accounting) > 기간마감전표 (Period Closing Voucher)** 에서 **"신규 (New)"** 를 클릭한다.
2. 마감 기간 (Closing Period)과 이익잉여금 계정 (Retained Earnings Account)을 선택한다.
3. **"마감 실행 (Run Closing)"** 을 클릭하면 수익 (Revenue)/비용 (Expense) 계정이 마감된다.

### 세금 관리 (Tax Management)

#### 부가세 신고 (VAT Filing)
1. **회계 (Accounting) > 부가세 신고 (VAT Filing)** 에서 신고 기간 (Filing Period)을 선택한다.
2. 매출세액 (Output VAT), 매입세액 (Input VAT), 납부/환급세액 (Net VAT)이 자동 집계되고 신고 기한(Due Date)이 함께 표시된다.
3. 전자세금계산서 동기화 카드에서 발행/전송/대기 건수를 확인한다.
4. **"신고서 생성 (Generate Filing)"** 을 클릭하면 초안이 생성되고, 납부 예정이면 `submit_vat_return`, 환급 예정이면 `review_refund_documents` 액션이 안내된다.
5. 제출 후에는 `submitted_payable` 또는 `submitted_refund` 배지와 함께 납부/환급 후속 액션이 표시된다.

#### 전자세금계산서 (e-Tax Invoice)
1. 매출 송장 (Sales Invoice) 제출 (Submit) 시 자동으로 전자세금계산서가 생성된다.
2. **회계 (Accounting) > 전자세금계산서 (e-Tax Invoice)** 에서 발행 현황을 확인한다.
3. 국세청 (NTS) 연동을 통해 전자세금계산서를 발행한다.

## 관련 보고서 (Related Reports)

- 재무상태표 (Balance Sheet)
- 손익계산서 (Income Statement)
- 현금흐름표 (Cash Flow Statement)
- 시산표 (Trial Balance)
- 매출채권 연령분석 (AR Aging Report)
- 매입채무 연령분석 (AP Aging Report)

## FAQ

- **Q: 제출 (Submit)된 분개 (Journal Entry)를 수정할 수 있나요?**
  A: 제출된 분개는 수정할 수 없습니다. 취소 (Cancel) 후 새로 작성해야 합니다. (Submitted entries cannot be edited. Cancel and recreate.)

- **Q: 초안 분개를 삭제할 수 있나요?**
  A: 가능합니다. 다만 초안 상태(docstatus=0)에서만 삭제할 수 있고, 제출된 전표는 삭제 대신 취소 후 새 전표를 작성해야 합니다.

- **Q: 자동 분개 (Auto Journal Entry)는 어떤 경우에 생성되나요?**
  A: 매출 송장 (Sales Invoice), 구매 송장 (Purchase Invoice), 급여 처리 (Payroll), 감가상각 (Depreciation), 기간 마감 (Period Closing) 시 자동 생성됩니다.
