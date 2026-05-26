# 튜토리얼: Initial Setup (초기 설정) / Tutorial: Admin Setup Guide

## 개요 (Overview)

OneERP 시스템을 처음 도입할 때 필요한 초기 설정을 단계별로 안내한다.
테넌트 (Tenant) 생성, 회사 (Company) 설정, 계정과목 시드 (Chart of Accounts Seed),
사용자/역할 (User/Role) 생성, 결재선 템플릿 (Approval Template),
채번규칙 (Naming Series) 설정까지 포함한다.

This tutorial guides you through the initial system setup for OneERP —
tenant creation, company configuration, chart of accounts seeding,
user/role setup, approval templates, and naming series configuration.

## 사전 조건 (Prerequisites)

- Gateway 서비스가 로컬에서 기동되어 있어야 한다.
- Super Admin 또는 회사 관리자 권한이 필요하다.
- 테넌트와 회사의 기본 정보를 입력할 준비가 되어 있어야 한다.

## 완료 조건 (Completion Criteria)

- 테넌트, 관리자 사용자, 모듈, 회사, 시드 데이터가 준비된다.
- 결재 템플릿과 채번 규칙이 설정된다.
- 첫 운영을 시작할 수 있는 상태가 된다.

## 다음 단계 (Next Step)

- [시작하기](../user-manual/00-getting-started.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Gateway (포트 8001 / Port 8001) — 테넌트/사용자/회사/결재/넘버링
uv run --package oneerp-gateway --directory services/gateway \
    uvicorn app.main:app --port 8001 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

Debug 모드에서는 Super Admin 권한으로 자동 인증된다.
In debug mode, all requests are auto-authenticated with Super Admin privileges.

---

## Step 1: 테넌트 생성 (Create Tenant)

테넌트 (Tenant)는 멀티테넌트 (Multi-tenant) 환경에서 데이터 격리의 최상위 단위이다.
Admin API (`/api/v1/admin`)는 Super Admin 전용이다.

```bash
curl -s -X POST http://localhost:8001/api/v1/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "테스트 회사",
    "domain": "test-company",
    "plan": "standard",
    "is_active": true
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "tenant_id": "TNT-0001",
  "message": "테넌트가 생성되었습니다"
}
```

### 테넌트 목록 조회 (List Tenants)

```bash
curl -s "http://localhost:8001/api/v1/admin/tenants" | jq
```

---

## Step 2: Company Admin 생성 (Create Tenant Admin User)

테넌트의 관리자 (Company Admin) 사용자를 생성한다.
이 사용자가 이후 모든 테넌트 내 설정을 수행한다.

```bash
curl -s -X POST http://localhost:8001/api/v1/admin/tenants/TNT-0001/admin-user \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@test-company.co.kr",
    "full_name": "테스트 관리자",
    "password": "SecureP@ss123"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "user_id": "USR-0001",
  "message": "Company Admin이 생성되었습니다"
}
```

---

## Step 2A: OIDC 사용자 초대 상태 확인 (Create OIDC Managed User)

관리자가 실제 업무 사용자를 생성하고 OIDC 연동 준비 상태를 확인한다.

```bash
curl -s -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: TNT-0001" \
  -H "X-User-Sub: admin" \
  -H "X-User-Roles: admin" \
  -H "X-User-Tier: tenant_admin" \
  -H "X-User-Permissions: *:*" \
  -d '{
    "username": "oidc-user",
    "email": "oidc.user@test-company.co.kr",
    "full_name": "OIDC 사용자",
    "roles": ["finance_manager"],
    "company_id": "COMP-0001",
    "department_name": "재무팀",
    "auth_provider": "oidc"
  }' | jq
```

생성 후 워크벤치 상세를 조회하면 `auth_summary`, `access_summary`, `status_badge`, `recommended_action`으로 OIDC 연결 여부와 초대 대기 상태를 바로 확인할 수 있다.

```bash
curl -s http://localhost:8001/api/v1/users/USR-0002/summary \
  -H "X-Tenant-Id: TNT-0001" \
  -H "X-User-Sub: admin" \
  -H "X-User-Roles: admin" \
  -H "X-User-Tier: tenant_admin" \
  -H "X-User-Permissions: *:*" | jq
```

---

## Step 3: 테넌트 모듈 설정 (Configure Tenant Modules)

테넌트에서 사용할 모듈을 설정한다. 플랜 (Plan)에 따라 사용 가능한 모듈이 제한된다.

```bash
curl -s -X PUT http://localhost:8001/api/v1/admin/tenants/TNT-0001/modules \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_modules": [
      "selling",
      "buying",
      "stock",
      "accounting",
      "hr",
      "payroll",
      "expenses",
      "manufacturing",
      "assets",
      "projects",
      "quality",
      "crm"
    ]
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "message": "모듈 설정이 변경되었습니다",
  "allowed_modules": ["selling", "buying", "stock", "..."]
}
```

---

## Step 4: 회사 설정 (Configure Company)

테넌트 내에 회사 (Company)를 생성한다.
기본 통화 (Default Currency), 계정과목표 (Chart of Accounts), 회계연도 시작일을 설정한다.
멀티컴퍼니 운영을 위해 회사 코드, 사업자등록번호, 대표자, 주소, 기본 회사 여부도 함께 저장한다.

```bash
curl -s -X POST http://localhost:8001/api/v1/companies \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "테스트 주식회사",
    "abbr": "TST",
    "company_code": "TST-HQ",
    "business_registration_number": "123-45-67890",
    "representative_name": "홍길동",
    "address": "서울시 강남구 테헤란로 1",
    "default_currency": "KRW",
    "country": "한국",
    "chart_of_accounts": "한국 표준 계정과목",
    "fiscal_year_start": "01-01",
    "domain": "제조",
    "is_default": true
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "id": "COMP-0001",
  "message": "회사가 생성되었습니다"
}
```

### 회사 워크벤치 확인 (Review Company Workbench)

회사 목록은 기본 회사 수, 활성 회사 수, 본사/지사 수를 summary 로 보여 주며 각 행마다 `status_badge`, `recommended_action`, `hierarchy_summary`를 제공한다.

```bash
curl -s http://localhost:8001/api/v1/companies | jq
```

```json
{
  "data": [
    {
      "_id": "COMP-0001",
      "status_badge": "default_company",
      "recommended_action": "create_branch_company",
      "hierarchy_summary": {
        "is_default": true,
        "child_company_count": 0
      }
    }
  ],
  "summary": {
    "total_company_count": 1,
    "default_company_count": 1,
    "root_company_count": 1,
    "branch_company_count": 0
  }
}
```

기본 회사는 다른 회사를 기본값으로 전환하기 전에는 삭제할 수 없다. 다중 법인 환경에서 회사 전환기의 기본 컨텍스트가 비지 않도록 막는 안전 장치다.

---

## Step 5: 시드 데이터 실행 (Run Seed Data)

계정과목 (Chart of Accounts), 통화 (Currency), 역할/권한 (Roles/Permissions),
채번규칙 (Naming Series), 데모 데이터를 일괄 생성한다.

```bash
uv run python scripts/seed/run_all.py --tenant TNT-0001
```

### 실행 순서 (Execution Order)

| 순서 (Order) | 시드 (Seed) | 내용 (Content) |
|--------------|-------------|----------------|
| 1 | 통화 (Currencies) | KRW, USD, EUR, JPY 등 |
| 2 | 계정과목표 (Chart of Accounts) | 자산, 부채, 자본, 수익, 비용 계정 |
| 3 | 역할/권한 (Roles/Permissions) | admin, manager, user, finance_manager 등 |
| 4 | 채번규칙 (Naming Series) | SO-, PO-, SINV-, PINV- 등 문서 번호 규칙 |
| 5 | 데모 데이터 (Demo Data) | 샘플 고객, 공급업체, 품목 등 |

### 개별 시드 실행 (Run Individual Seeds)

```bash
# 계정과목만 실행 (Chart of Accounts only)
uv run python -c "from scripts.seed.seed_chart_of_accounts import seed; seed(tenant_id='TNT-0001')"

# 통화만 실행 (Currencies only)
uv run python -c "from scripts.seed.seed_currencies import seed; seed(tenant_id='TNT-0001')"
```

---

## Step 6: 결재선 템플릿 설정 (Configure Approval Templates)

주요 문서 유형별 결재 템플릿 (Approval Template)을 설정한다.

### 경비청구 결재선 (Expense Claim Approval)

```bash
curl -s -X POST http://localhost:8001/api/v1/approval-templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "경비청구 결재",
    "document_type": "expense_claim",
    "approval_lines": [
      {"sequence": 1, "approver_role": "manager", "description": "팀장 승인"},
      {"sequence": 2, "approver_role": "finance_manager", "description": "재무팀장 승인"}
    ]
  }' | jq
```

### 구매 발주 결재선 (Purchase Order Approval)

```bash
curl -s -X POST http://localhost:8001/api/v1/approval-templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "발주서 결재 (1000만원 이상)",
    "document_type": "purchase_order",
    "approval_lines": [
      {"sequence": 1, "approver_role": "manager", "description": "팀장 승인"},
      {"sequence": 2, "approver_role": "director", "description": "본부장 승인"},
      {"sequence": 3, "approver_role": "cfo", "description": "CFO 승인"}
    ]
  }' | jq
```

---

## Step 7: 채번규칙 설정 (Configure Naming Series)

문서별 일련번호 규칙을 설정한다. 시드 데이터로 기본 규칙이 이미 생성되어 있지만,
회사별 커스터마이즈가 필요하면 개별 설정한다.

```bash
curl -s -X POST http://localhost:8001/api/v1/naming-series \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "sales_order",
    "prefix": "SO-",
    "current": 0,
    "digits": 4
  }' | jq
```

### 주요 채번 규칙 (Common Naming Series)

| 문서 유형 (Document Type) | 접두어 (Prefix) | 예시 (Example) |
|---------------------------|----------------|----------------|
| 판매주문 (Sales Order) | SO- | SO-0001 |
| 발주서 (Purchase Order) | PO- | PO-0001 |
| 매출전표 (Sales Invoice) | SINV- | SINV-0001 |
| 매입전표 (Purchase Invoice) | PINV- | PINV-0001 |
| 수금/지급 (Payment Entry) | PE- | PE-0001 |
| 경비청구 (Expense Claim) | EC- | EC-0001 |
| 작업지시 (Work Order) | WO- | WO-0001 |
| 자산 (Asset) | AST- | AST-0001 |

---

## Step 8: 알림 설정 (Configure Notifications)

### 알림 템플릿 생성 (Create Notification Template)

```bash
curl -s -X POST http://localhost:8001/api/v1/notification-templates \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "결재 요청 알림",
    "event_type": "approval_request.created",
    "channel": "email",
    "subject_template": "[OneERP] 결재 요청: {document_type}",
    "body_template": "{approver_name}님, {requester_name}의 {document_type} 결재 요청이 있습니다."
  }' | jq
```

### 알림 규칙 생성 (Create Notification Rule)

```bash
curl -s -X POST http://localhost:8001/api/v1/notification-rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "결재 요청 시 이메일 발송",
    "event_type": "approval_request.created",
    "notification_template": "NTPL-0001",
    "is_active": true
  }' | jq
```

---

## 검증 (Verification)

### 1. 플랫폼 통계 확인 (Check Platform Stats)

```bash
curl -s "http://localhost:8001/api/v1/admin/stats" | jq
```

```json
{
  "total_tenants": 1,
  "active_tenants": 1,
  "total_users": 1,
  "plan_distribution": {
    "starter": 0,
    "standard": 1,
    "enterprise": 0
  }
}
```

### 2. 테넌트 상세 확인 (Verify Tenant Details)

```bash
curl -s "http://localhost:8001/api/v1/admin/tenants/TNT-0001" | jq
```

### 3. 시스템 설정 확인 (Verify System Settings)

```bash
curl -s "http://localhost:8001/api/v1/system-settings" | jq
```

### 4. 서비스 기동 확인 (Verify All Services)

모든 서비스가 정상 기동되었는지 확인한다.

```bash
# 각 서비스 헬스체크 (Health check for each service)
for port in 8001 8002 8003 8004 8005 8006 8007 8008; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r '.status')"
done
```

---

## 테넌트 관리 작업 (Tenant Administration)

### 테넌트 정지 (Suspend Tenant)

```bash
curl -s -X POST http://localhost:8001/api/v1/admin/tenants/TNT-0001/suspend \
  -H "Content-Type: application/json" \
  -d '{"reason": "결제 미납"}' | jq
# 응답 (Response): {"message": "테넌트가 정지되었습니다"}
```

### 테넌트 활성화 (Activate Tenant)

```bash
curl -s -X POST http://localhost:8001/api/v1/admin/tenants/TNT-0001/activate | jq
# 응답 (Response): {"message": "테넌트가 활성화되었습니다"}
```

---

## 전체 설정 순서 다이어그램 (Setup Flow Diagram)

```
[Super Admin]                          [Tenant Admin]
    |                                       |
  1. 테넌트 생성                              |
     Create Tenant                          |
    |                                       |
  2. Admin 사용자 생성                        |
     Create Admin User                     |
    |                                       |
  3. 모듈 설정                               |
     Configure Modules                     |
    |                                       |
    +-------- 여기서부터 Tenant Admin -------->|
                                            |
                                      4. 회사 설정
                                         Configure Company
                                            |
                                      5. 시드 데이터 실행
                                         Run Seed Data
                                         (통화/계정과목/역할/채번)
                                            |
                                      6. 결재선 템플릿 설정
                                         Configure Approval Templates
                                            |
                                      7. 채번규칙 커스터마이즈
                                         Customize Naming Series
                                            |
                                      8. 알림 설정
                                         Configure Notifications
                                            |
                                        설정 완료!
                                        Setup Complete!
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 멀티테넌트 (Multi-tenant) 구조: Super Admin → 테넌트 → Company Admin → 사용자
- 테넌트 생성, 모듈 설정, 정지/활성화 등 플랫폼 관리
- 시드 데이터 (Seed Data) 실행: 통화, 계정과목, 역할, 채번규칙, 데모 데이터
- 회사 (Company) 설정: 기본 통화, 계정과목표, 회계연도
- 결재 템플릿 (Approval Template) 설정: 문서 유형별 다단계 결재선
- 채번규칙 (Naming Series): 문서별 일련번호 접두어/자릿수 설정
- 알림 (Notification) 설정: 이벤트 기반 알림 템플릿 + 규칙
