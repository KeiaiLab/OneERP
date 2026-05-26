# 경비 모듈 (Expenses Module)

## 개요 (Overview)

경비 모듈은 직원 경비 청구 (Expense Claim), 법인카드 관리 (Corporate Card), 출장 신청/정산 (Travel Request/Settlement) 등 기업 경비 관리를 지원한다. 모든 경비 문서는 전자결재 (Approval Workflow)를 통해 승인된다.

## 사전 조건 (Prerequisites)

- 경비 모듈과 결재 모듈이 활성화되어 있어야 한다.
- 경비 유형과 결재 템플릿이 설정되어 있어야 한다.
- 영수증 첨부와 승인 요청을 처리할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 경비 청구서가 제출되고 승인 흐름이 시작된다.
- 법인카드 거래를 경비 항목에 연결할 수 있다.
- 출장 정산과 회계 반영 흐름을 확인할 수 있다.

## 다음 단계 (Next Step)

- [전자결재 모듈](./13-approval.md)

## 관련 튜토리얼 (Related Tutorials)

- [경비→결재→회계 튜토리얼](../tutorials/03-expense-approval.md)

## 주요 기능 (Key Features) 

- 경비유형 설정 (Expense Type Setup)
- 경비 청구 (Expense Claim)
- 법인카드 관리 (Corporate Card Management)
- 법인카드 거래 자동 매칭 (Auto Matching)
- 출장 신청 (Travel Request)
- 출장 정산 (Travel Settlement)

## 업무 흐름 (Workflow)

```
경비 발생         경비 청구          승인            지급
(Expense)    → (Expense Claim) → (Approval)   → (Payment)
                     ↑
법인카드 거래 자동 매칭 (Corporate Card Auto Matching)
```

## 상세 기능 (Detailed Features)

### 경비유형 설정 (Expense Type Setup)

1. **경비 (Expenses) > 경비유형 (Expense Type)** 에서 사용할 경비 유형을 정의한다. (Define expense types to use.)
2. 예 (Examples): 교통비 (Transportation), 식비 (Meals), 숙박비 (Accommodation), 접대비 (Entertainment), 사무용품 (Office Supplies) 등.
3. 유형별 한도 (Limit), 연결 계정과목 (Linked Account)을 설정한다.

### 경비 청구 (Expense Claim)

#### 생성 (Create)
1. **경비 (Expenses) > 경비 청구 (Expense Claim)** 에서 **"신규 (New)"** 를 클릭한다.
2. 경비 항목 (Expense Items)을 추가한다:
   - 경비유형 (Expense Type)을 선택한다.
   - 금액 (Amount), 일자 (Date), 설명 (Description)을 입력한다.
   - 영수증 (Receipt)을 첨부한다.
3. 여러 항목을 한 청구서에 포함할 수 있다. (Multiple items can be included in one claim.)
4. **"제출 (Submit)"** 하면 승인 프로세스 (Approval Process)가 시작된다.

#### 승인/반려 (Approve/Reject)
1. 승인권자 (Approver)는 **경비 (Expenses) > 경비 청구 (Expense Claim)** 에서 대기 중인 청구서를 확인한다.
2. 영수증 (Receipt)과 금액 (Amount)을 검토한다.
3. **"승인 (Approve)"** 또는 **"반려 (Reject)"** 를 선택한다.
4. 승인된 경비는 급여 (Payroll)에 포함되거나 별도 지급된다.

### 법인카드 관리 (Corporate Card Management)

#### 법인카드 등록 (Register Corporate Card)
1. **경비 (Expenses) > 법인카드 (Corporate Card)** 에서 **"신규 (New)"** 를 클릭한다.
2. 카드번호 (Card Number, 마스킹 Masked), 카드사 (Card Issuer), 소유자 (Cardholder)를 입력한다.
3. 사용 한도 (Credit Limit)를 설정한다.

#### 법인카드 거래 관리 (Corporate Card Transaction Management)
1. **경비 (Expenses) > 법인카드 거래 (Corporate Card Transaction)** 에서 거래 내역을 확인한다.
2. 각 거래에 경비유형 (Expense Type)과 프로젝트 (Project)/부서 (Department)를 매칭한다.
3. 적요 (Remarks)를 입력하고 영수증 (Receipt)을 첨부한다.
4. **"제출 (Submit)"** 하면 승인 (Approval) 후 회계에 자동 반영된다.

### 출장 관리 (Business Trip Management)

#### 출장 신청 (Travel Request)
1. **경비 (Expenses) > 출장신청 (Travel Request)** 에서 **"신규 (New)"** 를 클릭한다.
2. 출장 목적 (Purpose), 기간 (Period), 목적지 (Destination)를 입력한다.
3. 예상 경비 (Estimated Expenses)를 항목별로 입력한다.
4. **"제출 (Submit)"** 하면 승인 프로세스 (Approval Process)가 시작된다.

#### 출장 정산 (Travel Settlement)
1. 출장 완료 후 실제 지출 경비를 경비 청구서 (Expense Claim)로 제출한다. (Submit actual expenses via Expense Claim after trip completion.)
2. 출장 신청 (Travel Request)과 연결하여 예산 대비 실적을 비교한다. (Link to Travel Request to compare budget vs. actual.)

## 관련 보고서 (Related Reports)

- 경비 청구 현황 (Expense Claim Status)
- 법인카드 사용 내역 (Corporate Card Usage Report)
- 부서별 경비 분석 (Department Expense Analysis)

## FAQ

- **Q: 경비 청구 (Expense Claim)가 반려 (Rejected)되면 어떻게 하나요?**
  A: 반려 사유를 확인하고 내용을 수정하여 다시 제출합니다. (Check the rejection reason, revise, and resubmit.)

- **Q: 법인카드 거래 (Corporate Card Transaction)는 자동으로 가져오나요?**
  A: 카드사 연동이 설정된 경우 자동으로 거래 내역이 수집됩니다. (Transactions are auto-imported when card issuer integration is configured.)
