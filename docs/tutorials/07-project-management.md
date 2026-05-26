# 튜토리얼: Project Management (프로젝트 관리) / Tutorial: Project Management

## 개요 (Overview)

프로젝트 생성에서 타임시트 (Timesheet) 기록, 원가 집계 (Cost Aggregation),
수익 인식 (Revenue Recognition)까지의 전체 흐름을 단계별로 실습한다.
이 시나리오는 Projects 서비스의 `TimesheetService`, `ProjectCostService`,
`RevenueRecognitionService`를 활용한다.

This tutorial covers the full Project Management flow — from project creation
through timesheet tracking, cost aggregation, and revenue recognition.

## 사전 조건 (Prerequisites)

- Projects, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 고객과 직원 마스터가 준비되어 있어야 한다.
- 타임시트와 청구 흐름을 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 프로젝트, 타임시트, 청구, 수익 인식 흐름이 완료된다.
- 원가와 수익성을 확인할 수 있다.
- 다음 품질 관리 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [품질 관리 튜토리얼](./08-quality-control.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Projects (포트 8011 / Port 8011)
uv run --package oneerp-projects --directory services/projects \
    uvicorn app.main:app --port 8011 --reload

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

## Step 1: 프로젝트 생성 (Create Project)

```bash
curl -s -X POST http://localhost:8011/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "ERP 도입 컨설팅",
    "customer": "CUST-0001",
    "project_manager": "EMP-0001",
    "expected_start_date": "2026-03-01",
    "expected_end_date": "2026-06-30",
    "company": "COMP-001",
    "cost_center": "CC-IT",
    "budget": 50000000
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "id": "PROJ-0001",
  "project_name": "ERP 도입 컨설팅",
  "generated_task_ids": []
}
```

프로젝트 관리자는 직원 마스터에 존재해야 하며, 잘못된 직원 ID를 보내면 `ERR-PRJ-010`으로 차단된다.

```bash
curl -s "http://localhost:8011/api/v1/projects?status=open&company=COMP-001&project_manager=EMP-0001" | jq
```

프로젝트 목록은 `project_manager_name`, `task_count`, `completed_task_count`, `overdue_milestone_count`와 함께 `summary.total_budget`, `summary.average_progress`를 돌려준다.

---

## Step 2: 작업 생성과 상태 전이 (Create Tasks and Drive Status)

```bash
# 선행 태스크 생성
curl -s -X POST http://localhost:8011/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "킥오프 완료",
    "project_ref": "PROJ-0001",
    "assigned_to": "EMP-0001",
    "start_date": "2026-03-01",
    "end_date": "2026-03-02"
  }' | jq

# 후속 태스크 생성
curl -s -X POST http://localhost:8011/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "요구사항 문서 작성",
    "project_ref": "PROJ-0001",
    "assigned_to": "EMP-0001",
    "start_date": "2026-03-03",
    "end_date": "2026-03-07",
    "predecessor_task_ids": ["TASK-0001"],
    "expected_time": 24
  }' | jq
```

- 선행 태스크가 완료되기 전에는 후속 태스크를 `working`/`pending_review`/`completed`로 바꿀 수 없다.
- 담당자가 없는 작업은 `working`으로 전환할 수 없다.
- 실제 공수가 0이면 `pending_review`로 전환할 수 없고, `pending_review` 상태를 거친 작업만 `completed`가 된다.
- 타임시트 로그나 후속 작업이 남아 있는 작업은 삭제가 차단된다.

---

## Step 3: 리소스 배정 (Allocate Resources)

프로젝트에 인력과 자재를 배정한다.

```bash
# 인력 배정 (Labor allocation)
curl -s -X POST http://localhost:8011/api/v1/resource-allocations \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ-0001",
    "type": "labor",
    "employee_id": "EMP-0001",
    "hours": 160,
    "hourly_rate": 150000
  }' | jq

# 자재 배정 (Material allocation)
curl -s -X POST http://localhost:8011/api/v1/resource-allocations \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ-0001",
    "type": "material",
    "description": "라이선스 비용",
    "amount": 5000000
  }' | jq
```

---

## Step 3A: 마일스톤 완료 + 청구 준비 상태 확인

```bash
# 마일스톤 생성
curl -s -X POST http://localhost:8011/api/v1/milestones/ \
  -H "Content-Type: application/json" \
  -d '{
    "milestone_name": "UAT 완료",
    "project": "PROJ-0001",
    "due_date": "2026-04-01",
    "completion_criteria": "고객 승인서 업로드",
    "billing_amount": "2500000"
  }' | jq

# 완료 처리
curl -s -X POST http://localhost:8011/api/v1/milestones/MLS-0001/complete | jq

# 청구 준비 워크벤치 조회
curl -s "http://localhost:8011/api/v1/milestones/?project=PROJ-0001&billing_status=ready_to_invoice" | jq '.summary, .data[0].status_badge, .data[0].billing_summary'
```

### 기대 결과 (Expected Result)

```json
{
  "ready_to_invoice_count": 1,
  "total_billing_amount": 2500000.0,
  "status_badge": "completed_ready_to_invoice",
  "billing_status": "ready_to_invoice"
}
```

완료된 마일스톤은 청구 초안과 함께 워크벤치에 바로 나타나며,
운영자는 `billing_status=ready_to_invoice` 필터로 청구 대기 건만 모아볼 수 있다.

---

## Step 4: 타임시트 기록 + 제출 (Record + Submit Timesheet)

`TimesheetService.submit_timesheet()` — total_hours > 0, time_logs 합계 일치, 작업일자 기간 무결성을 검증한 뒤 상태를 submitted로 변경한다.

```bash
# 타임시트 생성 (Create timesheet)
curl -s -X POST http://localhost:8011/api/v1/timesheets \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP-0001",
    "project": "PROJ-0001",
    "start_date": "2026-03-01",
    "end_date": "2026-03-15",
    "time_logs": [
      {"date": "2026-03-03", "project_ref": "PROJ-0001", "hours": 8, "activity_type": "요구분석"},
      {"date": "2026-03-04", "project_ref": "PROJ-0001", "hours": 8, "activity_type": "요구분석"},
      {"date": "2026-03-05", "project_ref": "PROJ-0001", "hours": 6, "activity_type": "설계"},
      {"date": "2026-03-06", "project_ref": "PROJ-0001", "hours": 8, "activity_type": "설계"},
      {"date": "2026-03-07", "project_ref": "PROJ-0001", "hours": 4, "activity_type": "고객 미팅"}
    ],
    "total_hours": 34
  }' | jq
# 응답 (Response): {"_id": "TS-0001", ...}

# 타임시트 제출 (Submit timesheet)
curl -s -X POST http://localhost:8011/api/v1/timesheets/TS-0001/submit | jq
```

### 기대 결과 (Expected Result)

```json
{
  "timesheet_id": "TS-0001",
  "total_hours": 34,
  "status": "submitted"
}
```

제출 직후 운영 워크벤치에서 미청구 타임시트와 급여 준비 시간 요약을 확인할 수 있다.

```bash
curl -s "http://localhost:8011/api/v1/timesheets?employee_id=EMP-0001&docstatus=1&billed=false" | jq
curl -s "http://localhost:8011/api/v1/timesheets/TS-0001" | jq '.status_badge, .payroll_summary, .billing_summary'
```

제출 완료 타임시트나 작업/마일스톤/자원 배정/프로젝트 청구가 남아 있는 프로젝트는 삭제할 수 없다.

---

## Step 4: 타임시트 기반 청구 (Invoice from Timesheet)

`TimesheetService.generate_invoice_from_timesheet()` — 타임시트 기반 청구서를 생성한다.
청구금액 = hours x hourly_rate

```bash
curl -s -X POST http://localhost:8011/api/v1/timesheets/TS-0001/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "hourly_rate": 150000
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "billing_id": "PBL-0001",
  "timesheet_id": "TS-0001",
  "total_hours": 34,
  "hourly_rate": 150000,
  "amount": 5100000
}
```

청구금액: 34시간 x 150,000원 = **5,100,000원**
타임시트에 `billed: true` 표시가 된다.

---

## Step 5: 프로젝트 원가 집계 (Calculate Project Cost)

`ProjectCostService.calculate_project_cost()` — 인건비 + 자재비 + 경비를 합산한다.

### 운영 팁: 활동 유형 워크벤치

타임시트가 누적되면 `/api/v1/activity-types` 목록에서 활동 유형별 `usage_summary`와 `rate_summary`를 즉시 확인할 수 있다.

- `status_badge=margin_watch` 활동 유형은 원가 단가보다 청구 단가가 낮은 경우이므로 `recommended_action=raise_billing_rate`를 우선 검토한다.
- `recommended_action=review_unbilled_timesheets`는 제출은 되었지만 아직 청구되지 않은 시간이 남아 있는 경우다.
- 상세 화면(`/api/v1/activity-types/{doc_id}`)의 `expected_margin_amount`는 누적 시간 기준 예상 마진 금액이다.

```bash
curl -s "http://localhost:8011/api/v1/projects/PROJ-0001/cost" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "project_id": "PROJ-0001",
  "labor_cost": 24000000,
  "material_cost": 5000000,
  "expense_cost": 0,
  "total_cost": 29000000
}
```

인건비: 160시간 x 150,000원 = 24,000,000원
자재비: 5,000,000원

---

## Step 6: 수익성 분석 (Profitability Analysis)

`ProjectCostService.get_profitability()` — 매출 대비 원가로 수익률을 분석한다.

```bash
curl -s "http://localhost:8011/api/v1/projects/PROJ-0001/profitability" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "project_id": "PROJ-0001",
  "revenue": 5100000,
  "total_cost": 29000000,
  "profit": -23900000,
  "margin_percent": -468.63
}
```

아직 청구가 1건(5.1M)뿐이므로 수익률이 음수이다.
프로젝트 진행에 따라 추가 청구가 발생하면 수익률이 개선된다.

---

## Step 7: 진행률 기준 수익 인식 (Revenue Recognition by Progress)

프로젝트 진행률을 업데이트하고 수익 인식을 수행한다.
`RevenueRecognitionService.recognize_by_progress()` — 진행률 x 계약금 - 기인식 = 추가 인식.

```bash
# 프로젝트 진행률 업데이트 (Update completion percentage)
curl -s -X PUT http://localhost:8011/api/v1/projects/PROJ-0001 \
  -H "Content-Type: application/json" \
  -d '{"percent_complete": 40}' | jq

# 진행률 기준 수익 인식 (Revenue recognition by progress)
curl -s -X POST http://localhost:8011/api/v1/projects/PROJ-0001/recognize-revenue \
  -H "Content-Type: application/json" \
  -d '{
    "method": "progress",
    "recognition_date": "2026-04-01"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "recognition_id": "PRREC-0001",
  "project_id": "PROJ-0001",
  "recognized_amount": 2040000,
  "total_contract_value": 5100000,
  "completion_percentage": 40
}
```

인식 금액: 계약금 5,100,000 x 40% - 기인식 0 = **2,040,000원**

### 완료 기준 수익 인식 (Revenue Recognition by Completion)

`RevenueRecognitionService.recognize_by_completion()` — 프로젝트 100% 완료 시에만 전액 인식.

```bash
# 프로젝트 100% 완료 (Mark project as 100% complete)
curl -s -X PUT http://localhost:8011/api/v1/projects/PROJ-0001 \
  -H "Content-Type: application/json" \
  -d '{"percent_complete": 100}' | jq

# 완료 기준 수익 인식 (Revenue recognition by completion)
curl -s -X POST http://localhost:8011/api/v1/projects/PROJ-0001/recognize-revenue \
  -H "Content-Type: application/json" \
  -d '{
    "method": "completion",
    "recognition_date": "2026-07-01"
  }' | jq
# 나머지 3,060,000원 인식 (Recognize remaining amount)
```

---

## 검증 (Verification)

### 1. 타임시트 청구 확인 (Verify Timesheet Billing)

```bash
curl -s "http://localhost:8011/api/v1/timesheets/TS-0001" | jq '.billed'
# 기대값 (Expected): true
```

### 2. 원가 합계 확인 (Verify Total Cost)

```bash
curl -s "http://localhost:8011/api/v1/projects/PROJ-0001/cost" | jq '.total_cost'
# 기대값 (Expected): 29000000
```

### 3. 수익 인식 기록 확인 (Verify Revenue Recognition Records)

```bash
curl -s "http://localhost:8011/api/v1/revenue-recognitions?project=PROJ-0001" | jq
# 2건: 진행률 기준 2,040,000 + 완료 기준 3,060,000 = 5,100,000
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Projects]                                  [Accounting]
    |                                           |
  1. 프로젝트 생성                               |
     Create Project                             |
    |                                           |
  2. 리소스 배정 (인력/자재)                      |
     Allocate Resources                         |
    |                                           |
  3. 타임시트 기록 + 제출                         |
     Record + Submit Timesheet                  |
    |                                           |
  4. 타임시트 기반 청구 -----------------------> 청구 분개
     Invoice from Timesheet                     Billing JE
    |                                           |
  5. 프로젝트 원가 집계                           |
     Calculate Project Cost                     |
     (인건비 + 자재비 + 경비)                     |
    |                                           |
  6. 수익성 분석                                 |
     Profitability Analysis                     |
    |                                           |
  7. 수익 인식 (진행률/완료 기준) ------------->  수익 인식 분개
     Revenue Recognition                        Revenue JE
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 프로젝트 리소스 배정 (Resource Allocation) — 인력, 자재, 경비 유형별 관리
- 타임시트 (Timesheet) 기록, 제출, 청구 — hours x hourly_rate 기반 청구
- 프로젝트 원가 (Project Cost) 집계 — 인건비 + 자재비 + 경비
- 수익성 분석 (Profitability Analysis) — 수익률(margin) = (매출 - 원가) / 매출
- 수익 인식 (Revenue Recognition) 방법: 진행률 기준 (Progress) vs 완료 기준 (Completion)
- 일괄 인보이싱 (Auto Invoicing) — 미청구 타임시트 일괄 처리
