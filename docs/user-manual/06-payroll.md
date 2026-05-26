# 급여 모듈 (Payroll Module)

## 개요 (Overview)

급여 모듈은 급여 구조 설계 (Salary Structure), 급여 명세서 생성 (Salary Slip), 4대보험 (Social Insurance), 원천징수 (Withholding Tax), 연말정산 (Year-end Settlement), 퇴직금 (Severance Pay) 등 한국 급여 체계를 지원한다.

## 사전 조건 (Prerequisites)

- HR, Payroll, Accounting 서비스와 직원 마스터가 준비되어 있어야 한다.
- 급여 구조와 공제 규칙이 설정되어 있어야 한다.
- 급여 분개와 지급 결과를 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 급여 구조, 급여 처리, 급여 명세 흐름을 설명할 수 있다.
- 급여 결과가 회계로 연결되는 흐름을 확인할 수 있다.
- 다음 경비 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [경비 모듈](./07-expenses.md)

## 주요 기능 (Key Features)

- 급여 항목 정의 (Salary Component)
- 급여 구조 (Salary Structure)
- 급여 처리 (Payroll Entry)
- 급여 명세서 (Salary Slip)
- 4대보험 (Social Insurance): 국민연금 (National Pension)/건강보험 (Health Insurance)/고용보험 (Employment Insurance)/산재보험 (Industrial Accident Insurance)
- 원천징수 (Withholding Tax) / 소득세 (Income Tax)
- 연말정산 (Year-end Tax Settlement)
- 퇴직금 (Severance Pay)

## 업무 흐름 (Workflow)

```
급여 구조 설정        급여 처리         급여 명세서        제출/확정
(Salary Structure) → (Payroll Entry) → (Salary Slip)  → (Submit)
                                                            ↓
                                                    회계 분개 자동 생성
                                                 (Auto Journal Entry)
```

## 상세 기능 (Detailed Features)

### 급여 구조 설정 (Salary Structure Setup)

#### 급여 항목 정의 (Salary Component)
1. **급여 (Payroll) > 급여 항목 (Salary Component)** 에서 급여 구성 요소를 정의한다.
2. 유형 (Type): 수당 (Earning: 기본급 Basic Pay, 직책수당 Position Allowance, 식대 Meal Allowance 등) 또는 공제 (Deduction: 소득세 Income Tax, 4대보험 Social Insurance 등).
3. 계산 공식 (Calculation Formula)을 설정할 수 있다.

#### 급여 구조 생성 (Create Salary Structure)
1. **급여 (Payroll) > 급여 구조 (Salary Structure)** 에서 **"신규 (New)"** 를 클릭한다.
2. 구조명 (Structure Name)을 입력한다 (예 Example: "정규직 월급제 Full-time Monthly").
3. 포함할 급여 항목 (Salary Components: 수당 Earnings/공제 Deductions)을 추가한다.
4. 각 항목의 기본값 (Default Value)이나 계산 공식 (Formula)을 설정한다.
5. **"저장 (Save)"** 을 클릭한다.

### 급여 처리 (Payroll Processing)

#### 급여 명세서 생성 (Generate Salary Slips)
1. **급여 (Payroll) > 급여 처리 (Payroll Entry)** 에서 **"신규 (New)"** 를 클릭한다.
2. 급여 기간 (Payroll Period: 월 Month)과 대상 부서 (Department)/직원 (Employee)을 선택한다.
3. **"급여 명세서 생성 (Generate Salary Slips)"** 을 클릭한다.
4. 직원별 급여 명세서 (Salary Slip)가 자동 생성된다.

#### 급여 명세서 확인 (Review Salary Slip)
1. **급여 (Payroll) > 급여 명세서 (Salary Slip)** 에서 개별 명세서를 확인한다.
2. 기본급 (Basic Pay), 수당 (Earnings), 공제 (Deductions) 내역을 검토한다.
3. 수정이 필요하면 개별 조정한다. (Make individual adjustments if needed.)
4. **"제출 (Submit)"** 하면 급여가 확정된다.

#### 추가급여 (Additional Salary)
1. **급여 (Payroll) > 추가급여 (Additional Salary)** 에서 상여금 (Bonus), 성과급 (Incentive) 등을 등록한다.
2. 해당 월 급여에 자동 반영된다. (Automatically reflected in the month's payroll.)

### 4대보험 (Social Insurance)

#### 4대보험 관리 (Social Insurance Management)
1. **급여 (Payroll) > 4대보험 (Social Insurance)** 에서 직원별 보험 가입 정보를 관리한다.
2. 국민연금 (National Pension), 건강보험 (Health Insurance), 고용보험 (Employment Insurance), 산재보험 (Industrial Accident Insurance) 요율이 자동 적용된다.
3. 보수월액 (Monthly Remuneration) 변경 시 자동으로 보험료가 재계산된다.

### 원천징수 (Withholding Tax)

1. **급여 (Payroll) > 원천징수 (Withholding Tax)** 에서 월별 원천징수 내역을 확인한다.
2. 간이세액표 (Simplified Tax Table)에 따라 소득세 (Income Tax)가 자동 계산된다.
3. 부양가족 수 (Number of Dependents)에 따라 공제가 적용된다.

### 연말정산 (Year-end Tax Settlement)

1. **급여 (Payroll) > 연말정산 (Year-end Settlement)** 에서 대상 연도를 선택한다.
2. 직원별 소득공제 (Income Deduction)/세액공제 (Tax Credit) 자료를 입력한다.
3. 추가납부 (Additional Payment) 또는 환급 (Refund) 금액이 자동 계산된다.
4. **"확정 (Confirm)"** 하면 다음 급여에 반영된다.

### 퇴직금 (Severance Pay)

1. **급여 (Payroll) > 퇴직금 (Severance Pay)** 에서 퇴직 직원의 퇴직금을 산정한다.
2. 근속연수 (Years of Service), 평균임금 (Average Wage) 기반으로 자동 계산된다.
3. **"확정 (Confirm)"** 하면 지급 처리된다.

### 급여 세금 신고 (Payroll Tax Filing)

1. **급여 (Payroll) > 급여 세금 신고 (Payroll Tax Filing)** 에서 원천징수 이행상황 신고서 (Withholding Tax Return)를 생성한다.
2. 월별 (Monthly)/반기별 (Semi-annual) 신고 기간을 선택한다.
3. 신고서를 확인하고 **"제출 (Submit)"** 한다.

## 관련 보고서 (Related Reports)

- 급여 명세 요약 (Payroll Summary)
- 4대보험 신고 내역 (Social Insurance Filing Report)
- 원천징수 이행상황 (Withholding Tax Status)
- 연말정산 결과 보고서 (Year-end Settlement Report)

## FAQ

- **Q: 4대보험 요율 (Social Insurance Rates)은 자동으로 업데이트되나요?**
  A: 시스템 관리자가 요율 변경 시 업데이트해야 합니다. (System administrators must update rates when they change.)

- **Q: 연말정산 (Year-end Settlement) 결과는 어느 급여에 반영되나요?**
  A: 확정 후 다음 급여 처리 시 자동 반영됩니다. (Reflected in the next payroll processing after confirmation.)
