# 고객관계관리 모듈 (CRM Module)

## 개요 (Overview)

CRM 모듈은 리드 관리 (Lead Management), 영업 기회 추적 (Opportunity Tracking), 마케팅 캠페인 (Marketing Campaign), 고객 이슈 관리 (Issue Management), SLA 모니터링 (SLA Monitoring), 필드 서비스 (Field Service) 등 고객 관계 관리 전반을 지원한다.

## 사전 조건 (Prerequisites)

- CRM 서비스와 고객/연락처 마스터가 준비되어 있어야 한다.
- Selling 서비스와의 연계가 준비되어 있어야 한다.
- 리드와 기회 흐름을 볼 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 리드, 기회, 캠페인, SLA 흐름을 설명할 수 있다.
- 고객 전환이 판매 문서와 연결되는 지점을 확인할 수 있다.
- 다음 자산 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [자산 모듈](./09-assets.md)

## 주요 기능 (Key Features)

- 리드 관리 (Lead Management)
- 영업 기회 (Opportunity)
- 마케팅 캠페인 (Campaign)
- 고객 이슈 관리 (Issue Management)
- SLA 관리 (SLA Management)
- 필드 서비스 (Field Service)
- 보증 클레임 (Warranty Claim)

## 업무 흐름 (Workflow)

```
리드 등록       리드 추적        기회 전환          견적/판매주문
(Lead Reg.) → (Lead Track) → (Opportunity)  → (Quotation/Sales Order)
```

## 상세 기능 (Detailed Features)

### 리드 관리 (Lead Management)

#### 생성 (Create)
1. **CRM > 리드 (Lead)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 리드 소스 (Lead Source: 웹사이트 Website, 전화 Phone, 소개 Referral 등)를 선택한다.
3. 연락처 정보 (Contact Info: 이름 Name, 회사명 Company, 이메일 Email, 전화번호 Phone)를 입력한다.
4. 관심 품목/서비스 (Interested Item/Service)와 후속 담당자 (Owner)를 기록한다.
5. **"저장 (Save)"** 을 클릭한다.
6. 동일 이메일 리드가 이미 존재하면 새 문서를 만들지 않고 기존 리드를 병합/갱신해야 한다. (Duplicate email leads are blocked to keep one source of truth.)

#### 추적 (Track)
1. 리드 목록에서 상태별 (Status: 신규 New/연락중 Contacted/적격 Qualified/부적격 Unqualified)로 필터링한다.
2. 리드 워크벤치 상단에서 적격 리드 수, 고득점 리드 수, 후속 조치가 지연된 리드 수를 확인한다.
3. 각 리드 행의 상태 배지 (예: `qualified_hot`, `contacted_active`)와 권장 액션을 확인한다.
4. 리드에 활동 (Activity: 전화 Call, 이메일 Email, 미팅 Meeting)을 기록하면 상세 요약에 최신 활동 유형과 담당자 수가 표시된다.
5. 적격 리드는 **"기회로 전환 (Convert to Opportunity)"** 을 클릭하여 영업 기회를 생성한다.

### 영업 기회 (Opportunity)

1. **CRM > 기회 (Opportunity)** 에서 영업 파이프라인 (Sales Pipeline)을 관리한다.
2. 기회별 예상 금액 (Expected Amount), 확률 (Probability), 마감 예정일 (Expected Close Date)을 입력한다.
3. 파이프라인 단계 (Pipeline Stage: 발굴 Prospecting/제안 Proposal/협상 Negotiation/수주 Won)를 진행한다.
4. 수주 시 **견적서 (Quotation)** 또는 **판매주문 (Sales Order)** 을 생성한다.

### 마케팅 캠페인 (Marketing Campaign)

#### 캠페인 설정 (Campaign Setup)
1. **CRM > 캠페인 (Campaign)** 에서 **"신규 (New)"** 를 클릭한다.
2. 캠페인명 (Campaign Name), 유형 (Type), 기간 (Period), 예산 (Budget)을 입력한다.
3. 대상 마케팅 리스트 (Target Marketing List)를 선택한다.

#### 이메일 캠페인 (Email Campaign)
1. **CRM > 이메일 캠페인 (Email Campaign)** 에서 이메일 발송 캠페인을 설정한다.
2. 템플릿 (Template)을 선택하고 발송 일정 (Schedule)을 설정한다.
3. 발송 후 열람률 (Open Rate), 클릭률 (Click Rate)을 추적한다.

#### SMS 캠페인 (SMS Campaign)
1. **CRM > SMS 캠페인 (SMS Campaign)** 에서 SMS 발송을 설정한다.
2. 수신 동의 (Opt-in)가 확인된 대상에게만 발송된다.

### 고객 이슈 관리 (Issue Management)

#### 접수 (Create)
1. **CRM > 이슈 (Issue)** 에서 **"신규 (New)"** 를 클릭한다.
2. 고객 (Customer), 이슈 유형 (Issue Type), 우선순위 (Priority)를 선택한다.
3. 이슈 내용 (Description)을 상세히 기록한다.
4. **"제출 (Submit)"** 하면 담당자 (Assignee)에게 배정된다.

#### 처리 (Resolve)
1. 담당자는 이슈를 확인하고 처리 상태 (Status)를 갱신한다.
2. 코멘트 (Comment)를 추가하여 처리 경과를 기록한다.
3. 해결 후 **"종료 (Close)"** 처리한다.

### SLA 관리 (SLA Management)

1. **CRM > SLA** 에서 서비스 수준 목표 (Service Level Agreement)를 정의한다.
2. 이슈 유형 (Issue Type)/우선순위 (Priority)별 응답 시간 (Response Time), 해결 시간 (Resolution Time)을 설정한다.
3. SLA 이행 현황을 모니터링한다. (Monitor SLA compliance.)
4. 위반 시 자동으로 에스컬레이션 (Escalation)이 실행된다.

### 필드 서비스 (Field Service)

1. **CRM > 서비스주문 (Service Order)** 에서 현장 서비스를 요청한다. (Request on-site service.)
2. **CRM > 서비스방문 (Service Visit)** 에서 방문 일정을 관리한다. (Manage visit schedules.)
3. 서비스기사 (Technician)를 배정하고 방문 결과 (Visit Result)를 기록한다.

### 보증 클레임 (Warranty Claim)

1. **CRM > 보증클레임 (Warranty Claim)** 에서 고객 보증 요청을 접수한다. (Register customer warranty requests.)
2. 보증기간 (Warranty Period) 내 여부를 확인한다.
3. 처리 방법 (Resolution: 수리 Repair/교환 Replace/환불 Refund)을 결정한다.

## 관련 보고서 (Related Reports)

- 리드 전환율 (Lead Conversion Rate)
- 영업 파이프라인 (Sales Pipeline Report)
- 캠페인 ROI (Campaign ROI)
- SLA 이행 현황 (SLA Compliance Report)

## FAQ

- **Q: 리드 (Lead)와 기회 (Opportunity)의 차이는 무엇인가요?**
  A: 리드는 잠재 고객, 기회는 구체적인 영업 건입니다. 리드가 적격 판정되면 기회로 전환합니다. (Lead is a potential customer; Opportunity is a specific sales deal. Convert a qualified lead to an opportunity.)

- **Q: SLA 위반 시 어떻게 되나요?**
  A: 자동으로 상위 관리자에게 에스컬레이션 알림이 발송됩니다. (An escalation notification is automatically sent to upper management.)
