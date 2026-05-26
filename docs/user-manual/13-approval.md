# 전자결재 모듈 (Approval Workflow Module)

## 개요 (Overview)

전자결재 모듈은 기업 내 각종 문서의 승인 프로세스 (Approval Process)를 전자적으로 처리한다. 결재 템플릿 설정 (Approval Template), 결재선 구성 (Approval Line), 승인/반려/위임/전결 (Approve/Reject/Delegate/Pre-approve) 등의 기능을 제공한다.

## 사전 조건 (Prerequisites)

- 승인 대상 문서와 결재 템플릿이 준비되어 있어야 한다.
- 결재자 역할과 위임 규칙이 설정되어 있어야 한다.
- 승인 요청을 확인할 수 있는 권한이 있어야 한다.

## 완료 조건 (Completion Criteria)

- 결재 요청 생성, 승인, 반려, 위임 흐름을 이해한다.
- 결재 현황과 이력을 조회할 수 있다.
- 다음 단계 문서로 연결할 수 있다.

## 다음 단계 (Next Step)

- [관리자 모듈](./14-admin.md)

## 관련 튜토리얼 (Related Tutorials)

- [경비→결재→회계 튜토리얼](../tutorials/03-expense-approval.md)

## 주요 기능 (Key Features)

- 결재 템플릿 (Approval Template)
- 결재선 마스터 (Approval Line Master)
- 결재 요청 (Approval Request)
- 승인 (Approve) / 반려 (Reject)
- 결재 위임 (Delegation)
- 워크플로우 규칙 (Workflow Rules)
- 알림 설정 (Notification Settings)

## 업무 흐름 (Workflow)

```
문서 제출           결재 요청 생성        결재자 승인        최종 승인
(Doc Submit)   → (Approval Req.)   → (Approver Review) → (Final Approval)
                                          ↓
                                    반려 (Reject) → 수정 후 재제출
                                                    (Revise & Resubmit)
```

## 상세 기능 (Detailed Features)

### 결재 템플릿 (Approval Template)

#### 설정 (Setup)
1. **관리 (Administration) > 결재 템플릿 (Approval Template)** 에서 **"프리셋 (Preset)"** 또는 **"신규 (New)"** 를 선택한다.
2. 프리셋을 사용할 경우 품의서 (`general-proposal`), 지출결의서 (`expense-claim`), 구매요청 (`purchase-request`) 중 하나를 선택한다.
3. 템플릿명 (Template Name), 적용 대상 문서 유형 (Document Type), 사용 여부 (`is_active`)를 확인한다.
4. 양식 필드 (Form Fields)를 검토하거나 필요한 입력 필드를 추가한다.
   - 동일한 `field_key`는 한 번만 사용할 수 있다.
   - ERP 문서 자동 채움이 필요하면 데이터 바인딩 (Data Binding) 대상 필드를 정의한다.
5. 결재 단계 (Approval Steps)를 추가한다:
   - 각 단계의 결재자 (Approver: 역할 Role 또는 특정 사용자 Specific User)를 지정한다.
   - 순차 승인 (Sequential) 또는 병렬 승인 (Parallel)을 설정한다.
6. `condition` 필드에 금액/부서 메모를 남겨 워크벤치에서 조건 힌트를 볼 수 있다. 실제 조건부 분기 엔진은 P2 범위다.
7. 필요한 경우 **"복제 (Clone)"** 로 기존 양식을 복사해 부서별 변형 양식을 만든다.
8. **"저장 (Save)"** 을 클릭한다.
9. 결재선 마스터(Approval Line)가 연결된 템플릿은 참조를 해제하기 전까지 삭제할 수 없다.

### 결재선 마스터 (Approval Line Master)

1. **관리 (Administration) > 결재선 (Approval Line)** 에서 템플릿별 결재선을 관리한다.
2. 같은 `template + sequence`에 여러 라인을 두면 합의 단계가 되며, 모든 라인은 `approval_type=consensus`여야 한다.
3. 같은 단계에는 동일한 결재자 또는 결재자 역할을 중복 등록할 수 없다.
4. 목록 상단 `summary`에서 템플릿 수, 단계 수, 합의 단계 수, 전결 가능 단계 수, 조건 메모가 있는 단계 수를 한 번에 확인한다.
5. 각 행/상세의 `approval_mode_badge`, `step_summary`, `available_actions`로 합의 단계와 전결 가능 단계를 즉시 확인한다.

### 결재 요청 (Approval Request)

#### 생성 (Create)
1. 각 모듈에서 문서를 **"제출 (Submit)"** 하면 결재 요청이 자동 생성된다. (Approval requests are auto-created when documents are submitted.)
2. 결재 템플릿 (Approval Template)에 따라 결재선 (Approval Line)이 자동 구성된다.
3. 첫 번째 결재자 (First Approver)에게 알림 (Notification)이 발송된다.

#### 현황 확인 (Status Review)
1. **관리 (Administration) > 결재 요청 (Approval Request)** 에서 전체 결재 현황을 확인한다.
2. 상단 요약 카드에서 상태별 건수, `waiting_on_me_count`, 내가 기안한 건수, 합의 결재 대기 건수를 한 번에 확인한다.
3. 각 행의 상태 배지 (`pending_approval`, `consensus_pending`, `approved`, `rejected`, `cancelled`)와 현재 단계 요약에서 지금 누구 차례인지 확인한다.
4. 결재 이력 (Approval History)에서 결재 요청/원본문서/행위 유형/처리자/기간으로 필터링하고 `action_badge`, `request_status_badge`, 위임 대상, `request_summary`로 단계별 승인/반려/위임/전결 문맥을 즉시 확인한다.
5. 감사 추적 리포트 (Audit Report)에서 행위별 건수, 결재자별 처리 건수, 요청 상태 분포, 최초/최종 처리 시각을 함께 검토한다.

### 결재 처리 (Approval Processing)

#### 승인 (Approve)
1. 결재자 (Approver)는 대시보드 (Dashboard) 또는 알림 (Notification)에서 결재 대기 문서를 확인한다.
2. 대기함 목록에서 `available_actions`에 노출된 승인/반려/위임/전결 버튼 중 가능한 액션만 선택할 수 있다.
3. 문서 내용을 검토한다. (Review the document.)
4. **"승인 (Approve)"** 을 클릭하고 의견 (Comment)을 입력한다 (선택 Optional).
5. 다음 결재자 (Next Approver)에게 자동으로 넘어간다.
6. 최종 승인되면 문서 상태가 **"승인완료 (Approved)"** 로 변경된다.

#### 반려 (Reject)
1. 문서 내용에 문제가 있으면 **"반려 (Reject)"** 를 클릭한다.
2. 반려 사유 (Rejection Reason)를 반드시 입력한다. (Rejection reason is mandatory.)
3. 요청자 (Requester)에게 반려 알림이 발송된다.
4. 요청자는 내용을 수정하여 다시 제출 (Resubmit)할 수 있다.

### 결재 위임 (Delegation)

#### 위임 규칙 설정 (Setup Delegation Rules)
1. **관리 (Administration) > 결재 위임 규칙 (Delegation Rules)** 에서 **"신규 (New)"** 를 클릭한다.
2. 위임자 (Delegator: 원래 결재자 Original Approver)와 수임자 (Delegate: 대리 결재자 Acting Approver)를 지정한다.
3. 위임 기간 (Delegation Period: 시작일 Start~종료일 End)을 설정한다.
4. 위임 대상 문서 유형 (Document Types)을 선택한다 (전체 All 또는 특정 유형 Specific Types).
5. **"저장 (Save)"** 을 클릭한다.

#### 위임 사용 예 (Delegation Examples)
- 출장 (Business Trip)/휴가 (Leave) 중 결재를 위임한다.
- 위임 기간이 지나면 자동으로 원래 결재자로 복원된다. (Delegation automatically reverts after the period ends.)
- 만료 3일 이내 규칙은 `expiring_soon` 배지와 함께 표시되며, 상세의 `recommended_action=extend_rule`을 따라 기간을 연장한다.
- 같은 위임자에게 기간/문서 범위가 겹치는 활성 규칙은 저장되지 않으므로, 부서별 예외는 문서 유형을 분리해서 등록한다.

### 워크플로우 규칙 (Workflow Rules)

1. **관리 (Administration) > 워크플로우 규칙 (Workflow Rules)** 에서 문서 유형별 워크플로우를 설정한다.
2. 상태 전환 조건 (State Transition Conditions)을 정의한다.
3. 각 상태에서 가능한 액션 (Available Actions)을 설정한다.

### 알림 설정 (Notification Settings)

#### 알림 템플릿 (Notification Template)
1. **관리 (Administration) > 알림 템플릿 (Notification Template)** 에서 결재 관련 알림 메시지를 설정한다.
2. 이메일 (Email), 인앱 알림 (In-app Notification) 내용을 정의한다.

#### 알림 규칙 (Notification Rules)
1. **관리 (Administration) > 알림 규칙 (Notification Rules)** 에서 알림 발송 조건을 설정한다.
2. 예 (Example): 결재 대기 (Pending Approval) 3일 초과 시 리마인더 (Reminder) 발송

## 관련 보고서 (Related Reports)

- 결재 현황 보고서 (Approval Status Report)
- 결재 처리 시간 분석 (Approval Processing Time)
- 위임 현황 (Delegation Status)

## FAQ

- **Q: 결재선 (Approval Line)을 임의로 변경할 수 있나요?**
  A: 결재 템플릿에 따라 자동 구성되며, 관리자라면 결재선 마스터에서 템플릿별 `sequence`, 합의 단계, 전결 가능 역할을 조정할 수 있습니다. 워크벤치 요약으로 합의/전결 단계를 먼저 확인한 뒤 수정하세요.

- **Q: 전결 (Pre-approve)이란 무엇인가요?**
  A: 특정 조건(예: 일정 금액 이하)에서 상위 결재를 생략하고 즉시 승인되는 것입니다. (Automatic approval without upper-level review when certain conditions are met, e.g., below a threshold amount.)
