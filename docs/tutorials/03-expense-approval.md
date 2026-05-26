# 튜토리얼: Expense-Approval (경비→결재→회계) / Tutorial: Expense Approval

## 개요 (Overview)

직원의 경비청구 (Expense Claim)에서 전자결재 (Approval Workflow) 승인을 거쳐
회계 자동 분개 (Auto Journal Entry)까지의 전체 흐름을 실습한다.
이 시나리오는 Expenses, Gateway(전자결재), Accounting 3개 서비스를 횡단하며,
결재선 (Approval Line) 기반의 승인 워크플로우를 보여준다.

This tutorial covers the complete Expense Approval flow — from submitting an Expense Claim
through a multi-level approval workflow to automatic accounting journal entries.
It spans Expenses, Gateway (Approval), and Accounting services.

## 사전 조건 (Prerequisites)

- Expenses, Gateway, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 결재 템플릿과 승인자 역할이 준비되어 있어야 한다.
- 경비 항목과 영수증을 입력할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 경비청구 제출, 결재 승인, 회계 자동 분개가 완료된다.
- 승인 이력과 전표가 연결되어 조회된다.
- 반려 후 재제출 흐름도 확인할 수 있다.

## 다음 단계 (Next Step)

- [초기 설정 튜토리얼](./10-admin-setup.md)

## 관련 문서 (Related Docs)

- [경비 모듈](../user-manual/07-expenses.md)
- [전자결재 모듈](../user-manual/13-approval.md)
- [회계 모듈](../user-manual/01-accounting.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Gateway (포트 8001 / Port 8001) — 전자결재 (Approval)
uv run --package oneerp-gateway --directory services/gateway \
    uvicorn app.main:app --port 8001 --reload

# Expenses (포트 8008 / Port 8008)
uv run --package oneerp-expenses --directory services/expenses \
    uvicorn app.main:app --port 8008 --reload

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

### 기초 데이터: 결재 템플릿 생성 (Create Approval Template)

경비청구에 사용할 결재 템플릿을 먼저 생성한다. 프리셋을 기반으로 만들고, 필요하면 부서별 복사본을 만든다.

```bash
curl -s -X GET http://localhost:8001/api/v1/approval-templates/presets \
  -H "X-Tenant-Id: demo" \
  -H "X-User-Sub: admin" \
  -H "X-User-Roles: admin" \
  -H "X-User-Permissions: *:*" | jq

curl -s -X POST http://localhost:8001/api/v1/approval-templates/presets/expense-claim \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -H "X-User-Sub: admin" \
  -H "X-User-Roles: admin" \
  -H "X-User-Permissions: *:*" \
  -d '{
    "template_name": "경비청구 결재"
  }' | jq

curl -s -X POST http://localhost:8001/api/v1/approval-templates/AT-2026-00001/clone \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: demo" \
  -H "X-User-Sub: admin" \
  -H "X-User-Roles: admin" \
  -H "X-User-Permissions: *:*" \
  -d '{
    "template_name": "경비청구 결재 - 영업본부"
  }' | jq
```

**응답 (Response):**
```json
{
  "approval_template_id": "AT-2026-00001",
  "message": "결재템플릿 프리셋이 생성되었습니다"
}
```

운영 팁:
- `form_fields.field_key`와 `data_binding_fields.target_field`는 각각 중복될 수 없다.
- `is_active=false`로 비활성화한 템플릿은 새 결재 요청 생성에 사용되지 않는다.
- 결재선 마스터가 연결된 템플릿은 참조를 해제하기 전까지 삭제할 수 없다.
- 같은 `sequence`에 여러 결재선을 두면 합의 단계가 되므로 모든 라인을 `approval_type=consensus`로 맞춘다.
- 결재선 목록의 `summary`와 각 행의 `approval_mode_badge`/`step_summary`를 보면 합의 단계 수와 전결 가능 단계를 즉시 점검할 수 있다.

---

## Step 1: 경비청구 생성 (Create Expense Claim)

직원이 출장/업무 관련 경비를 청구한다.
An employee submits business-related expenses.

```bash
curl -s -X POST http://localhost:8008/api/v1/expense-claims \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMP-0001",
    "expense_type": "출장비",
    "posting_date": "2026-03-23",
    "expenses": [
      {
        "expense_date": "2026-03-20",
        "description": "서울→부산 KTX 왕복",
        "expense_type": "교통비",
        "amount": 118600
      },
      {
        "expense_date": "2026-03-20",
        "description": "부산 숙박 1박",
        "expense_type": "숙박비",
        "amount": 150000
      },
      {
        "expense_date": "2026-03-21",
        "description": "고객 미팅 식대",
        "expense_type": "식비",
        "amount": 45000
      }
    ],
    "total_amount": 313600
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "EC-0001",
  "employee": "EMP-0001",
  "total_amount": 313600
}
```

---

## Step 2: 경비청구 제출 (Submit Expense Claim)

```bash
curl -s -X POST http://localhost:8008/api/v1/expense-claims/EC-0001/submit | jq
```

**발생하는 이벤트 (Emitted Event):** `expense_claim.submitted`

- Gateway 서비스가 이벤트를 수신한다.
- 결재 템플릿에 따라 자동으로 결재 요청 (Approval Request)을 생성한다.
- 1차 결재자 (팀장, Manager)에게 알림이 발송된다.

---

## Step 3: 결재 요청 조회 (Query Pending Approvals)

결재자가 자신에게 할당된 결재 요청을 조회한다.

```bash
curl -s "http://localhost:8001/api/v1/approval-requests?current_approver_role=manager" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "summary": {
    "by_status": {
      "pending": 1,
      "submitted": 0,
      "approved": 0,
      "rejected": 0,
      "cancelled": 0
    },
    "waiting_on_me_count": 1,
    "my_requested_count": 0,
    "consensus_pending_count": 0
  },
  "data": [
    {
      "_id": "AR-0001",
      "document_type": "expense_claim",
      "document_id": "EC-0001",
      "status": "pending",
      "status_badge": "pending_approval",
      "waiting_on_me": true,
      "current_step_summary": {
        "step": 1,
        "approval_type": "single",
        "pending_approver_count": 1
      },
      "available_actions": ["approve", "reject", "delegate"]
    }
  ],
  "total": 1
}
```

---

## Step 4: 1차 승인 — 팀장 (First Approval — Manager)

```bash
curl -s -X POST http://localhost:8001/api/v1/approval-requests/AR-0001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "출장 내역 확인 완료"
  }' | jq
```

### 기대 결과 (Expected Result)

- 1차 결재선이 승인 처리된다.
- 자동으로 2차 결재자 (재무팀장, Finance Manager)에게 결재 요청이 넘어간다.

---

## Step 5: 2차 승인 — 재무팀장 (Second Approval — Finance Manager)

```bash
curl -s -X POST http://localhost:8001/api/v1/approval-requests/AR-0001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "경비 규정 준수 확인"
  }' | jq
```

**발생하는 이벤트 (Emitted Events):** `approval_request.approved`, `expense_claim.approved`

- 모든 결재선이 승인 완료되어 최종 승인 상태로 전환된다.
- Accounting 서비스가 `expense_claim.approved` 이벤트를 수신한다.

---

## Step 6: 회계 자동 분개 — 자동 (Auto Journal Entry — Automatic)

경비청구 승인 이벤트를 수신한 Accounting 서비스가 자동으로 분개를 생성한다.

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 교통비 (Transportation) | 118,600 | - |
| 차변 | 숙박비 (Accommodation) | 150,000 | - |
| 차변 | 식비 (Meals) | 45,000 | - |
| 대변 | 미지급비용 (Accrued Expenses) | - | 313,600 |

### 분개 확인 (Verify Journal Entry)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=EC-0001" | jq
```

---

## 결재 반려 시나리오 (Rejection Scenario)

결재자가 반려 (Reject)하면 경비청구가 Draft 상태로 돌아가며, 감사 워크벤치에서 반려 사유와 처리 문맥을 함께 확인할 수 있다.

```bash
curl -s -X POST http://localhost:8001/api/v1/approval-requests/AR-0001/reject \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "영수증 미첨부. 영수증 첨부 후 재청구 바랍니다."
  }' | jq
```

**발생하는 이벤트 (Emitted Event):** `approval_request.rejected`

- 경비청구가 Draft 상태로 복귀한다.
- 청구자에게 반려 알림 (Rejection Notification)이 발송된다.
- 청구자는 경비청구를 수정 후 다시 제출할 수 있다.

---

## 검증 (Verification)

### 0. 위임 규칙 워크벤치 확인

```bash
curl -s "http://localhost:8001/api/v1/delegation-rules?delegator=manager-001&document_type=ExpenseClaim&as_of_date=2026-04-10" | jq
```

- `summary.expiring_soon_count`가 1 이상이면 만료 임박 위임 규칙이 있다는 뜻이다.
- 각 행의 `status_badge`, `scope_summary`, `recommended_action`으로 전사 적용 규칙인지, 문서 제한 규칙인지, 기간 연장이 필요한지 바로 판단한다.

### 1. 결재 상태 확인 (Verify Approval Status)

```bash
curl -s "http://localhost:8001/api/v1/approval-requests/AR-0001" | jq '.status'
# 기대값 (Expected): "approved"
```

### 2. 경비청구 상태 확인 (Verify Expense Claim Status)

```bash
curl -s "http://localhost:8008/api/v1/expense-claims/EC-0001" | jq '.docstatus'
# 기대값 (Expected): 1 (Submitted + Approved)
```

### 3. 분개 차대변 일치 확인 (Verify Debit/Credit Balance)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=EC-0001" | jq
# 차변 합계 (313,600) = 대변 합계 (313,600) 확인
# Verify total debits (313,600) = total credits (313,600)
```

### 4. 감사 추적 워크벤치 확인 (Verify Audit Workbench)

```bash
curl -s "http://localhost:8001/api/v1/approval-actions?approval_request=AR-0001" | jq
# 각 행의 action_badge/request_status_badge/request_summary/available_actions 확인

curl -s "http://localhost:8001/api/v1/approval-actions/report?approval_request=AR-0001" | jq
# action_counts, actor_counts, request_status_counts, first_acted_at, last_acted_at 확인
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Expenses]              [Gateway/결재]              [Accounting]
    |                        |                          |
  1. 경비청구 생성 (Draft)    |                          |
     Create Expense Claim    |                          |
    |                        |                          |
  2. 경비청구 제출 ---------> 결재요청 자동 생성          |
     Submit Claim            Auto-create Approval Req   |
    |                        |                          |
    |                   3. 결재 대기 목록 조회            |
    |                      Query Pending Approvals      |
    |                        |                          |
    |                   4. 1차 승인 (팀장)               |
    |                      1st Approval (Manager)       |
    |                        |                          |
    |                   5. 2차 승인 (재무팀장)            |
    |                      2nd Approval (Finance Mgr)   |
    |                        |                          |
    |<-- 승인 완료 ---------<|                          |
    |    Approved             |                          |
    |                        |                          |
    |-- expense_claim.approved ----------------------->|
    |                        |                    6. 자동 분개 생성
    |                        |                       Auto Journal Entry
    |                        |                   (Dr: Expense / Cr: Accrued)
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 결재 템플릿 (Approval Template) 설정과 다단계 결재선 (Multi-level Approval Line)
- 경비청구 제출 → 자동 결재 요청 생성의 이벤트 기반 연계
- 순차 승인 (Sequential Approval) 흐름: 팀장 → 재무팀장
- 최종 승인 시 회계 자동 분개 (Auto Journal Entry) 생성
- 반려 (Rejection) 시나리오와 재청구 흐름
