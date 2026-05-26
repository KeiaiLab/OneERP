# 튜토리얼: Payroll Process (급여처리) / Tutorial: Payroll Process

## 개요 (Overview)

직원 등록에서 급여 지급 및 회계 처리까지의 전체 급여 흐름을 단계별로 실습한다.
이 시나리오는 HR, Payroll, Accounting 3개 서비스를 횡단하며,
급여 구조 (Salary Structure) 기반의 자동 계산과 회계 연동을 보여준다.

This tutorial covers the end-to-end Payroll flow — from employee registration
through salary calculation to accounting journal entries.
It spans HR, Payroll, and Accounting services.

## 사전 조건 (Prerequisites)

- HR, Payroll, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 직원과 급여 구조가 준비되어 있어야 한다.
- 직원을 등록하기 전에 `POST /api/v1/departments` 와 `GET /api/v1/departments/tree` 로 유효한 조직도와 상위 부서 관계를 먼저 구성한다.
- 급여 분개를 확인하려면 회계 전표 생성 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 직원 등록, 급여 처리, 급여명세서 확인 흐름이 완료된다.
- 급여 결과가 회계 분개로 연결된다.
- 다음 제조 흐름 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [제조 흐름 튜토리얼](./05-manufacturing-flow.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# HR (포트 8006 / Port 8006)
uv run --package oneerp-hr --directory services/hr \
    uvicorn app.main:app --port 8006 --reload

# Payroll (포트 8007 / Port 8007)
uv run --package oneerp-payroll --directory services/payroll \
    uvicorn app.main:app --port 8007 --reload

# Accounting (포트 8005 / Port 8005)
uv run --package oneerp-accounting --directory services/accounting \
    uvicorn app.main:app --port 8005 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

---

## Step 1: 직원 등록 (Register Employee)

HR 서비스에서 직원을 등록한다.

```bash
curl -s -X POST http://localhost:8006/api/v1/employees \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "홍길동",
    "date_of_birth": "1990-05-15",
    "date_of_joining": "2025-01-02",
    "department": "개발팀",
    "designation": "선임개발자",
    "employment_type": "REGULAR",
    "reports_to": "EMP-MANAGER-001",
    "status": "active"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "id": "EMP-0001",
  "employee_name": "홍길동",
  "department": "개발팀",
  "employment_type": "REGULAR",
  "reports_to": "EMP-MANAGER-001"
}
```

**발생하는 이벤트 (Emitted Event):** `employee.created`

- Payroll 서비스가 이벤트를 수신하여 급여 구조 초기화를 준비한다.
- `GET /api/v1/employees/directory?status=active` 로 보고라인/직속 인원 수가 즉시 반영되는지 확인한다.

## Step 1A: 휴가유형 워크벤치 점검 (Review Leave Type Workbench)

연말 연차 이월이나 휴가 승인 전에 휴가유형이 정책/잔액/신청 이력과 함께 보이는지 먼저 확인한다.

```bash
curl -s http://localhost:8006/api/v1/leave-types | jq
curl -s http://localhost:8006/api/v1/leave-types/LT-0001/summary | jq
```

### 기대 결과 (Expected Result)

- `status_badge=request_backlog|policy_unassigned|paid_carry_forward` 중 하나가 각 유형에 표시된다.
- `summary.policy_count`, `summary.balance_employee_count`, `summary.open_application_count`, `summary.max_carry_forward_days` 가 함께 반환된다.
- 사용 이력이 남은 휴가유형 삭제는 `ERR-HR-050` 으로 차단된다.

## Step 1B: 휴가 잔액 워크벤치 점검 (Review Leave Balance Workbench)

연말 이월 후보와 만료 임박 잔액을 같은 화면에서 점검한다.

```bash
curl -s "http://localhost:8006/api/v1/leave-balances?employee_id=EMP-0001&fiscal_year=2026" | jq
curl -s http://localhost:8006/api/v1/leave-balances/LB-0001/summary | jq
```

### 기대 결과 (Expected Result)

- 목록 `summary` 에 `employee_count`, `expiring_soon_count`, `carry_forward_ready_count` 가 함께 표시된다.
- 각 잔액 행에 `status_badge`, `recommended_action`, `summary.expected_carry_forward_days`, `available_actions` 가 포함된다.
- 상세 `carry_forward_summary` 에 `carry_forward_cap_days`, `expected_carry_forward_days`, `expires_in_days`, `utilization_rate_pct` 가 표시된다.

## Step 1C: 휴가 신청 워크벤치 점검 (Review Leave Application Workbench)

휴가 승인 전에 승인 대기와 잔액 부족 후보가 같은 화면에서 보이는지 확인한다.

```bash
curl -s "http://localhost:8006/api/v1/leave-applications?employee_id=EMP-0001&leave_type=연차" | jq
curl -s http://localhost:8006/api/v1/leave-applications/LA-0001/summary | jq
```

### 기대 결과 (Expected Result)

- 목록 `summary` 에 `open_count`, `approved_count`, `insufficient_balance_count` 가 함께 표시된다.
- 각 신청 행에 `status_badge`, `leave_balance_summary.remaining_days`, `leave_balance_summary.remaining_after_request`, `recommended_action`, `available_actions` 가 포함된다.
- `status_badge=pending_balance_review` 인 신청은 승인 전에 잔액 조정 검토가 필요하다는 뜻이다.

## Step 1D: 모바일 근태 기록 검증 (Capture Attendance Before Payroll)

급여 계산 전에 모바일/키오스크 출퇴근이 위치 증빙과 함께 저장되는지 확인한다.

```bash
curl -s -X POST http://localhost:8006/api/v1/attendances/check-in \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP-0001",
    "employee_name": "홍길동",
    "department": "개발팀",
    "attendance_date": "2026-03-25",
    "capture_channel": "mobile_widget",
    "ip_address": "10.10.0.22",
    "gps_latitude": 37.5665,
    "gps_longitude": 126.9780,
  "shift_name": "주간",
    "scheduled_start_time": "09:00",
    "scheduled_end_time": "18:00",
    "recorded_at": "2026-03-25T09:10:00"
  }' | jq

curl -s "http://localhost:8006/api/v1/attendances?attendance_date=2026-03-25&capture_channel=mobile_widget&location_status=verified" | jq
curl -s "http://localhost:8006/api/v1/attendances/weekly-summary?employee_id=EMP-0001&week_start_date=2026-03-23" | jq
```

### 기대 결과 (Expected Result)

- 체크인 응답에 `late_minutes`, `status_badge`, `location_summary`가 포함된다.
- 근태 워크벤치 목록은 `summary.mobile_widget_count`, `summary.location_verified_count`, `available_actions`를 함께 반환한다.
- 주간 요약에서 `exceeded_52h`와 `overtime_hours`를 급여 계산 전에 검토할 수 있다.

## Step 1E: 인사발령 워크벤치 점검 (Review Employee Transfer Workbench)

급여 계산 전에 부서/직급 발령이 직원 마스터와 급여 동기화 문맥까지 함께 보이는지 확인한다.

```bash
curl -s -X POST http://localhost:8006/api/v1/employee-transfers \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMP-0001",
    "transfer_date": "2026-03-25",
    "to_department": "기획팀",
    "to_designation": "대리",
    "reason": "조직개편"
  }' | jq

curl -s "http://localhost:8006/api/v1/employee-transfers?employee=EMP-0001" | jq
curl -s -X POST http://localhost:8006/api/v1/employee-transfers/ETR-0001/submit | jq
curl -s http://localhost:8006/api/v1/employee-transfers/ETR-0001/summary | jq
```

### 기대 결과 (Expected Result)

- 목록 `summary` 에 `draft_count`, `submitted_count`, `effective_today_count`, `payroll_sync_pending_count` 가 함께 표시된다.
- 각 발령 행에 `status_badge`, `recommended_action`, `available_actions`, `summary.change_scope/payroll_sync_pending` 가 포함된다.
- 상세 `/summary` 는 `change_summary`, `impact_summary`, `sync_summary` 를 반환해 발령 영향과 급여 동기화 상태를 동시에 설명한다.

---

## Step 2: 급여 구조 설정 (Configure Salary Structure)

직원에게 적용할 급여 구조를 정의한다.
Define the Salary Structure with earnings and deductions.

- 직원 등록 전에 `GET /api/v1/designations/hierarchy` 로 정렬된 직급 체계와 현재 재직 인원 수를 확인한다.
- 퇴사 처리된 직원만 남은 직급은 급여 구조 정리 후 삭제할 수 있으므로, 폐지된 직급을 정리할 때는 먼저 직원을 퇴사 또는 다른 직급으로 전환한다.

### 급여 구조 생성 (Create Salary Structure)

```bash
curl -s -X POST http://localhost:8007/api/v1/salary-structures \
  -H "Content-Type: application/json" \
  -d '{
    "structure_name": "정규직 개발자 급여",
    "payroll_frequency": "Monthly",
    "earnings": [
      {
        "component": "기본급",
        "formula_or_amount": 4000000,
        "is_fixed": true
      },
      {
        "component": "식대",
        "formula_or_amount": 200000,
        "is_fixed": true
      },
      {
        "component": "교통보조",
        "formula_or_amount": 100000,
        "is_fixed": true
      }
    ],
    "deductions": [
      {
        "component": "국민연금",
        "formula_or_amount": "기본급 * 0.045",
        "is_formula": true
      },
      {
        "component": "건강보험",
        "formula_or_amount": "기본급 * 0.03545",
        "is_formula": true
      },
      {
        "component": "장기요양보험",
        "formula_or_amount": "건강보험 * 0.1281",
        "is_formula": true
      },
      {
        "component": "고용보험",
        "formula_or_amount": "기본급 * 0.009",
        "is_formula": true
      },
      {
        "component": "소득세",
        "formula_or_amount": 0,
        "is_fixed": true,
        "description": "간이세액표 기반 계산 (Simplified Tax Table)"
      }
    ]
  }' | jq
```

### 급여 구조 할당 (Assign Salary Structure)

```bash
curl -s -X POST http://localhost:8007/api/v1/salary-structure-assignments \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMP-0001",
    "salary_structure": "SS-0001",
    "from_date": "2025-01-01",
    "base": 4000000
  }' | jq
```

---

## Step 3: 급여 처리 생성 (Create Payroll Entry)

월말에 급여를 일괄 처리한다.
Process monthly payroll at the end of the period.

```bash
curl -s -X POST http://localhost:8007/api/v1/payroll-entries \
  -H "Content-Type: application/json" \
  -d '{
    "payroll_frequency": "Monthly",
    "posting_date": "2026-03-25",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "department": "개발팀",
    "salary_structure": "SS-0001"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "PRLL-0001",
  "payroll_frequency": "Monthly",
  "posting_date": "2026-03-25"
}
```

---

## Step 4: 급여명세서 확인 (Verify Salary Slips)

급여 처리가 생성되면 대상 직원별 급여명세서 (Salary Slip)가 자동 생성된다.

```bash
curl -s "http://localhost:8007/api/v1/salary-slips?payroll_entry=PRLL-0001" | jq
```

### 급여 계산 내역 (Payroll Calculation Breakdown)

| 항목 (Component) | 금액 (Amount) |
|-------------------|--------------|
| **지급 항목 (Earnings)** | |
| 기본급 (Base Salary) | 4,000,000 |
| 식대 (Meal Allowance) | 200,000 |
| 교통보조 (Transportation) | 100,000 |
| **지급 합계 (Gross Pay)** | **4,300,000** |
| **공제 항목 (Deductions)** | |
| 국민연금 (National Pension, 4.5%) | 180,000 |
| 건강보험 (Health Insurance, 3.545%) | 141,800 |
| 장기요양보험 (Long-term Care, 건보의 12.81%) | 18,163 |
| 고용보험 (Employment Insurance, 0.9%) | 36,000 |
| **공제 합계 (Total Deduction)** | **375,963** |
| **실수령액 (Net Pay)** | **3,924,037** |

---

## Step 5: 급여 처리 제출 (Submit Payroll Entry)

```bash
curl -s -X POST http://localhost:8007/api/v1/payroll-entries/PRLL-0001/submit | jq
```

**발생하는 이벤트 (Emitted Event):** `payroll_entry.submitted`

- 각 급여명세서가 자동으로 제출된다.
- `salary_slip.submitted` 이벤트가 직원 수만큼 발행된다.
- Accounting 서비스가 이벤트를 수신하여 급여 분개 (Payroll Journal Entry)를 생성한다.

---

## Step 6: 회계 자동 분개 — 자동 (Auto Journal Entry — Automatic)

Accounting 서비스가 급여 분개를 자동 생성한다.

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 급여 — 인건비 (Salary Expense) | 4,300,000 | - |
| 대변 | 미지급급여 (Salary Payable) | - | 3,924,037 |
| 대변 | 국민연금 예수금 (National Pension Payable) | - | 180,000 |
| 대변 | 건강보험 예수금 (Health Insurance Payable) | - | 141,800 |
| 대변 | 장기요양보험 예수금 (Long-term Care Payable) | - | 18,163 |
| 대변 | 고용보험 예수금 (Employment Insurance Payable) | - | 36,000 |

### 분개 확인 (Verify Journal Entry)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=PRLL-0001" | jq
```

---

## Step 7: 급여 지급 (Disburse Salary)

실제 급여를 지급한다.
Disburse the actual salary to the employee's bank account.

```bash
# 지급 전표 생성 (Create payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries \
  -H "Content-Type: application/json" \
  -d '{
    "payment_type": "Pay",
    "party_type": "Employee",
    "party": "EMP-0001",
    "paid_amount": 3924037,
    "received_amount": 3924037,
    "reference_doctype": "Salary Slip",
    "reference_name": "SLIP-0001",
    "mode_of_payment": "은행이체"
  }' | jq

# 지급 전표 제출 (Submit payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries/PE-0003/submit | jq
```

- 분개 (Journal Entry): 차변 (Debit) 미지급급여 3,924,037 / 대변 (Credit) 은행 3,924,037

---

## 검증 (Verification)

### 1. 급여명세서 확인 (Verify Salary Slip)

```bash
curl -s "http://localhost:8007/api/v1/salary-slips/SLIP-0001" | jq '{net_pay, gross_pay, total_deduction}'
# 기대값 (Expected): net_pay=3924037, gross_pay=4300000, total_deduction=375963
```

### 2. 분개 차대변 일치 확인 (Verify Debit/Credit Balance)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=PRLL-0001" | jq
# 차변 합계 (4,300,000) = 대변 합계 (4,300,000) 확인
# Verify total debits (4,300,000) = total credits (4,300,000)
```

### 3. 미지급급여 잔액 0 확인 (Verify Salary Payable Balance is Zero)

급여 지급 후 미지급급여 (Salary Payable) 계정 잔액이 0이 되어야 한다.
After disbursement, the Salary Payable account balance should be zero.

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[HR]                    [Payroll]                  [Accounting]
  |                        |                           |
1. 직원 등록 ------------> (급여 구조 초기화 준비)      |
   Register Employee       Prepare Salary Init         |
  |                        |                           |
  |                   2. 급여 구조 설정                 |
  |                      Configure Salary Structure    |
  |                        |                           |
  |                   3. 급여 처리 생성                 |
  |                      Create Payroll Entry          |
  |                      -> 급여명세서 자동 생성         |
  |                         Auto-create Salary Slips   |
  |                        |                           |
  |                   4. 급여명세서 확인                |
  |                      Verify Salary Slips           |
  |                        |                           |
  |                   5. 급여 처리 제출 ------------->  급여 분개 생성
  |                      Submit Payroll Entry          Payroll JE
  |                        |                      (Dr: Salary Expense /
  |                        |                       Cr: Payable+Withholdings)
  |                        |                           |
  |                        |                      6-7. 급여 지급
  |                        |                          Disburse Salary
  |                        |                      (Dr: Salary Payable /
  |                        |                       Cr: Bank)
  |                        |                           |
  |                        |                      미지급급여 = 0
  |                        |                      Salary Payable = 0
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 급여 구조 (Salary Structure) 설정 — 지급 (Earnings)과 공제 (Deductions) 구성
- 4대보험 (Social Insurance) 공식 기반 자동 계산: 국민연금, 건강보험, 장기요양보험, 고용보험
- 급여 처리 (Payroll Entry) 제출 시 회계 자동 분개 (Auto Journal Entry) 생성
- 미지급급여 (Salary Payable) → 은행 (Bank) 지급까지의 전체 흐름
