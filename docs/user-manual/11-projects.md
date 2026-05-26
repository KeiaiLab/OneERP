# 프로젝트 모듈 (Projects Module)

## 개요 (Overview)

프로젝트 모듈은 프로젝트 생성 (Project Creation), 태스크 관리 (Task Management), 타임시트 기록 (Timesheet), 마일스톤 추적 (Milestone Tracking), 원가 관리 (Cost Management), 수익 인식 (Revenue Recognition) 등 프로젝트 기반 업무를 지원한다.

## 사전 조건 (Prerequisites)

- Projects, Accounting 서비스와 고객/직원 마스터가 준비되어 있어야 한다.
- 타임시트와 청구 흐름을 볼 권한이 필요하다.
- 원가와 수익 인식 기준을 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 프로젝트, 타임시트, 청구, 수익 인식 흐름을 설명할 수 있다.
- 프로젝트 원가와 수익성을 확인할 수 있다.
- 다음 품질 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [품질 모듈](./12-quality.md)

## 주요 기능 (Key Features)

- 프로젝트 관리 (Project Management)
- 태스크 관리 (Task Management)
- WBS (작업분해구조, Work Breakdown Structure)
- 마일스톤 (Milestone)
- 타임시트 (Timesheet)
- 프로젝트 원가 (Project Cost)
- 프로젝트 청구 (Project Billing)
- 수익 인식 (Revenue Recognition): 완공기준 (Completed Contract)/진행기준 (Percentage of Completion)

## 업무 흐름 (Workflow)

```
프로젝트 생성        태스크 분배       작업 수행       타임시트 기록      청구
(Project Create) → (Task Assign) → (Execute)   → (Timesheet)    → (Billing)
```

## 상세 기능 (Detailed Features)

### 프로젝트 관리 (Project Management)

#### 생성 (Create)
1. **프로젝트 (Projects) > 프로젝트 (Project)** 에서 **"신규 (New)"** 를 클릭한다.
2. 프로젝트명 (Project Name), 고객 (Customer), 시작일/종료일 (Start/End Date)을 입력한다.
3. 예산 (Budget), 프로젝트 관리자 (Project Manager)를 설정한다. 프로젝트 관리자는 반드시 직원 마스터에 등록된 사용자여야 한다.
4. 프로젝트 템플릿 (Template)을 선택하면 표준 태스크 (Standard Tasks)가 자동 생성되며, 생성 응답의 `generated_task_ids`로 즉시 확인할 수 있다.
5. **"저장 (Save)"** 을 클릭한다.

#### 현황 확인 (Status Review)
1. 프로젝트 목록에서 상태 (Status), 회사 (Company), 프로젝트 관리자 (Project Manager) 필터를 조합해 포트폴리오를 좁힌다.
2. 목록 응답/화면에서 프로젝트 관리자명, 작업 수, 완료 작업 수, 지연 마일스톤 수, 총 예산, 평균 진행률을 함께 확인한다.
3. 진행 상태 (Status): `open` → `in_progress` → `completed` → `cancelled`

### 태스크 관리 (Task Management)

#### 생성 (Create)
1. **프로젝트 (Projects) > 태스크 (Task)** 에서 **"신규 (New)"** 를 클릭한다.
2. 태스크명 (Task Name), 소속 프로젝트 (Project), 담당자 (Assignee)를 입력한다.
3. 시작일/종료일 (Start/End Date), 예상 공수 (Estimated Effort)를 설정한다.
4. 선행 태스크 (Predecessor: 의존 관계 Dependency)를 설정할 수 있다.
5. 담당자가 없는 작업은 `진행중 (working)` 으로 전환할 수 없다.
6. 실제 공수 (Actual Time)가 0이면 `검토 대기 (pending_review)` 로 전환할 수 없다.
7. 완료 처리 (completed)는 반드시 검토 대기 상태를 거친 뒤에만 허용된다.

#### 추적 (Track)
1. 태스크 목록에서 상태 (Status), 담당자 (Assignee), 프로젝트 (Project) 기준으로 필터링한다.
2. 담당자가 진행 상황을 갱신한다. (Assignees update progress.)
3. 후속 작업이 선행 관계로 참조하거나 타임시트 로그가 남아 있는 작업은 삭제할 수 없다.
4. 프로젝트를 삭제하려면 연결된 작업, 마일스톤, 자원 배정, 프로젝트 청구, 제출 완료 타임시트를 먼저 정리해야 한다.

### WBS (작업분해구조, Work Breakdown Structure)

1. **프로젝트 (Projects) > WBS요소 (WBS Element)** 에서 프로젝트를 계층적으로 분해한다. (Decompose the project hierarchically.)
2. 상위/하위 WBS 요소 (Parent/Child WBS Elements)를 정의하여 체계적으로 관리한다.

### 마일스톤 (Milestone)

1. **프로젝트 (Projects) > 마일스톤 (Milestone)** 에서 주요 이정표를 설정한다. (Set key milestones.)
2. 마일스톤별 완료 조건 (Completion Criteria), 예정일 (Due Date), 마일스톤 청구 금액 (Billing Amount)을 입력한다.
3. 목록 화면에서는 `project`, `status`, `billing_status`, `as_of_date` 기준으로 필터링하고 `ready_to_invoice_count`, `invoiced_count`, `total_billing_amount` 요약을 확인한다.
4. 완료된 마일스톤은 상태 배지(`completed`, `completed_ready_to_invoice`, `completed_billed`)와 청구 요약(`billing_summary`)을 함께 표시한다.
5. 청구 금액이 있는 마일스톤을 **"완료 처리 (Complete)"** 하면 프로젝트 청구 초안이 자동 생성되고 가능 액션에 **"청구 열기 (Open Billing)"** 가 노출된다.
6. 청구가 연결된 마일스톤은 삭제할 수 없다.

### 타임시트 (Timesheet)

#### 시간 기록 (Log Time)
1. **프로젝트 (Projects) > 타임시트 (Timesheet)** 에서 **"신규 (New)"** 를 클릭한다.
2. 기간 시작일/종료일을 지정하고, 각 time log에 **작업일자(Date)**, 프로젝트(Project), 태스크(Task), 활동 유형(Activity Type), 작업 시간(Hours)을 입력한다.
3. 종료일은 시작일보다 빠를 수 없으며, 작업일자는 타임시트 기간 안에 있어야 한다.
4. **"제출 (Submit)"** 하면 프로젝트 원가(Project Cost)에 반영되고 급여 준비 시간(`payroll_ready_hours`)로 집계된다.
5. 목록 화면에서는 직원/프로젝트/제출 여부/청구 여부 기준으로 필터링하고, 미청구 시간/급여 준비 시간 요약을 바로 확인할 수 있다.
6. 제출된 타임시트는 상세 화면에서 상태 배지(`submitted_unbilled`/`submitted_billed`), 청구 요약, 가능 액션(`create_invoice`, `view_invoice`)을 확인한다.

#### 활동 유형 (Activity Type)
1. **프로젝트 (Projects) > 활동 유형 (Activity Type)** 에서 활동 유형별 원가 단가(`costing_rate`)와 청구 단가(`billing_rate`)를 관리한다.
2. 목록 화면은 `summary(active_count, inactive_count, in_use_count, margin_watch_count, total_logged_hours, unbilled_hours)`를 제공하며, 각 행에서 상태 배지(`active_ready`/`active_in_use`/`margin_watch`/`inactive_*`)와 권장 액션을 확인할 수 있다.
3. 상세 화면은 `usage_summary`와 `rate_summary`를 제공해 최근 사용일, 사용 프로젝트 수, 미청구 시간, 예상 마진 금액을 즉시 파악할 수 있다.
4. 타임시트 사용 이력이 남아 있는 활동 유형은 삭제할 수 없으며 `ERR-PRJ-010`으로 차단된다. 이 경우 활동 유형을 비활성화하거나 미청구 시간을 먼저 정리한다.

### 프로젝트 원가 (Project Cost)

1. 타임시트 (Timesheet) 기반 인건비 (Labor Cost)가 자동 집계된다.
2. 경비 청구 (Expense Claim), 구매 주문 (Purchase Order) 등에서 프로젝트를 지정하면 원가에 포함된다.
3. 예산 (Budget) 대비 실적 (Actual)을 모니터링한다.

### 프로젝트 청구 (Project Billing)

1. **프로젝트 (Projects) > 프로젝트 청구 (Project Billing)** 에서 고객에게 청구서 (Invoice)를 발행한다.
2. 시간 기반 청구 (Time-based Billing): 타임시트 기록 기반 (Based on timesheet records)
3. 마일스톤 기반 청구 (Milestone-based Billing): 마일스톤 달성 시 청구 (Invoice upon milestone completion)
4. 정기 청구 (Recurring Billing): 월별 (Monthly)/분기별 (Quarterly) 정기 청구

### 프로젝트 수익 인식 (Revenue Recognition)

1. **프로젝트 (Projects) > 프로젝트 수익 인식 (Revenue Recognition)** 에서 수익 인식 일정을 관리한다.
2. 진행률 (Percentage of Completion) 기준으로 수익을 인식한다.
3. 회계 분개 (Journal Entry)가 자동 생성된다.

### 프로젝트 리스크 (Project Risk)

1. **프로젝트 (Projects) > 프로젝트 리스크 (Project Risk)** 에서 리스크를 등록한다.
2. 발생 확률 (Probability), 영향도 (Impact), 대응 계획 (Mitigation Plan)을 기록한다.
3. 정기적으로 리스크 현황을 리뷰한다. (Review risk status periodically.)

## 관련 보고서 (Related Reports)

- 프로젝트 현황 (Project Summary)
- 타임시트 분석 (Timesheet Analysis)
- 프로젝트 수익성 (Project Profitability)
- 마일스톤 진행 현황 (Milestone Progress)

## FAQ

- **Q: 수익 인식 (Revenue Recognition)에서 진행기준 (Percentage of Completion)이란?**
  A: 프로젝트 완성도에 비례하여 수익을 인식하는 방법입니다. 원가 투입 비율 또는 물리적 진행률로 측정합니다. (Revenue is recognized proportionally to project completion, measured by cost incurred or physical progress.)

- **Q: 하나의 태스크 (Task)에 여러 담당자 (Assignees)를 지정할 수 있나요?**
  A: 태스크에는 한 명의 주 담당자를 지정합니다. 협업이 필요하면 하위 태스크로 분할하세요. (Assign one primary assignee per task. Split into sub-tasks for collaboration.)
