# OneERP API 가이드 (API Guide)

## 개요 (Overview)

OneERP는 15개 마이크로서비스 (microservices)로 구성된 ERP 시스템이다.
모든 서비스는 FastAPI 기반 REST API를 제공하며, `oneerp_core` 공통 커널 (common kernel)을 통해
인증 (authentication), 권한 (authorization), 에러 처리 (error handling), CRUD 패턴이 표준화되어 있다.

---

## 인증 (Authentication)

3단계 인증 전략 (3-step authentication strategy)을 지원한다 (`packages/core/oneerp_core/auth.py`):

### 1단계: JWT 토큰 (Step 1: JWT Token — Production)

```
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "********"
}
```

**응답 (Response):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

토큰 전달 방식 (Token delivery methods, choose one):
- **Cookie**: `token=eyJhbGciOiJIUzI1NiIs...` (브라우저 자동 전달 / auto-sent by browser)
- **Bearer Header**: `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`

### 2단계: X-* 헤더 폴백 (Step 2: X-* Header Fallback — Dev/Test)

JWT 없이 헤더로 직접 사용자 정보를 주입할 수 있다:
User info can be injected directly via headers without JWT:

| 헤더 (Header) | 설명 (Description) | 예시 (Example) |
|------|------|------|
| `X-Tenant-Id` | 테넌트 ID (Tenant ID) | `tenant-001` |
| `X-User-Sub` | 사용자 식별자 (User Identifier) | `user-001` |
| `X-User-Roles` | 역할 (Roles, comma-separated) | `admin,manager` |
| `X-User-Tier` | 사용자 티어 (User Tier) | `regular`, `tenant_admin`, `super_admin` |
| `X-User-Permissions` | 권한 (Permissions, comma-separated) | `sales_order:create,sales_order:read` |

### 3단계: Debug 모드 더미 사용자 (Step 3: Debug Mode Dummy User)

`ONEERP_DEBUG=true` 환경에서는 인증 헤더 없이도 Super Admin 권한의 더미 사용자 (dummy user)로 자동 인증된다.

### CurrentUser 구조 (CurrentUser Structure)

인증 후 주입되는 사용자 객체 (user object injected after authentication):

```python
@dataclass(frozen=True)
class CurrentUser:
    sub: str               # 사용자 식별자 (User identifier)
    tenant_id: str         # 테넌트 ID (Tenant ID)
    roles: tuple[str, ...]  # 역할 목록 (Role list)
    permissions: tuple[str, ...] = ()  # 세밀한 권한 목록 (Fine-grained permissions)
    user_tier: str = "regular"         # regular | tenant_admin | super_admin
    is_super_admin: bool = False
```

---

## 멀티테넌트 (Multi-tenant)

- 모든 데이터는 `tenant_id` 필드로 자동 격리 (auto-isolated)된다.
- Repository가 쿼리 시 자동으로 `tenant_id` 필터를 적용한다 (auto-applies tenant filter).
- 개발 환경에서는 `X-Tenant-Id` 헤더로 테넌트를 지정할 수 있다.

---

## 공통 응답 형식 (Common Response Format)

### 목록 조회 (List Response)

```json
{
  "data": [
    {"_id": "SO-0001", "customer": "고객A", "total": 100000},
    {"_id": "SO-0002", "customer": "고객B", "total": 200000}
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### 생성 응답 (Create Response — 201)

```json
{
  "_id": "SO-0003",
  "customer": "고객C",
  "total": 150000
}
```

### 에러 응답 (Error Response)

```json
{
  "error": "conflict",
  "detail": "초안 상태에서만 수정할 수 있습니다",
  "request_id": "req-abc123"
}
```

| HTTP 상태 (Status) | error 값 (Error Value) | 상황 (Scenario) |
|-----------|----------|------|
| 400 | `bad_request` | 잘못된 요청 (Bad request — validation failure) |
| 401 | `unauthorized` | 인증 실패 (Auth failure — token expired/missing) |
| 403 | `forbidden` | 권한 부족 (Insufficient permissions) |
| 404 | `not_found` | 문서를 찾을 수 없음 (Document not found) |
| 409 | `conflict` | 비즈니스 규칙 위반 (Business rule violation) |

---

## CRUD 엔드포인트 패턴 (CRUD Endpoint Pattern)

모든 엔티티는 `EntityMeta` 기반으로 자동 생성된 CRUD 엔드포인트를 제공한다.
All entities provide auto-generated CRUD endpoints based on `EntityMeta`.
2가지 아키타입 (archetype: `master`, `transaction`)에 따라 지원 액션이 달라진다.

### 공통 엔드포인트 (Common Endpoints — master + transaction)

| 메서드 (Method) | 경로 (Path) | 설명 (Description) | 권한 (Permission) |
|--------|------|------|------|
| `POST` | `/api/v1/{entity}` | 생성 (Create) | `{resource}:create` |
| `GET` | `/api/v1/{entity}` | 목록 조회 (List with pagination) | `{resource}:read` |
| `GET` | `/api/v1/{entity}/{id}` | 상세 조회 (Get by ID) | `{resource}:read` |
| `PUT` | `/api/v1/{entity}/{id}` | 수정 (Update, Draft only) | `{resource}:write` |
| `DELETE` | `/api/v1/{entity}/{id}` | 삭제 (Delete, Draft only, 204) | `{resource}:delete` |

### 트랜잭션 추가 엔드포인트 (Transaction-only Endpoints — archetype: transaction)

| 메서드 (Method) | 경로 (Path) | 설명 (Description) | 권한 (Permission) |
|--------|------|------|------|
| `POST` | `/api/v1/{entity}/{id}/submit` | 제출 (Submit: Draft -> Submitted) | `{resource}:submit` |
| `POST` | `/api/v1/{entity}/{id}/cancel` | 취소 (Cancel: Submitted -> Cancelled) | `{resource}:cancel` |

### DocStatus 상태 머신 (DocStatus State Machine)

```
Draft (0) ──submit──→ Submitted (1) ──cancel──→ Cancelled (2)
    ↕ (수정/삭제 가능 / editable/deletable)  (수정/삭제 불가 / immutable)  (최종 상태 / final state)
```

---

## 권한 (Permissions)

`{resource}:{action}` 형식의 세밀한 권한 제어 시스템 (fine-grained permission system) (`packages/core/oneerp_core/permissions.py`):

### 권한 형식 (Permission Format)

```
sales_order:create    # 판매주문 생성 (Create sales order)
sales_order:read      # 판매주문 조회 (Read sales order)
sales_order:write     # 판매주문 수정 (Update sales order)
sales_order:delete    # 판매주문 삭제 (Delete sales order)
sales_order:submit    # 판매주문 제출 (Submit sales order)
sales_order:cancel    # 판매주문 취소 (Cancel sales order)
sales_order:*         # 판매주문 모든 액션 (All actions on sales order)
*:*                   # 모든 리소스, 모든 액션 (All resources, all actions — Super Admin)
```

### Tier 기반 접근 제어 (Tier-based Access Control)

| Tier | 역할 (Role) | 설명 (Description) |
|------|------|------|
| Tier 1 | Super Admin | 모든 테넌트의 모든 리소스 접근 (Access all resources across all tenants) |
| Tier 2 | Tenant Admin | 해당 테넌트의 관리 기능 접근 (Admin functions within tenant) |
| Tier 3 | Regular | 부여된 권한에 따른 접근 (Access based on assigned permissions) |

### 라우트에 권한 적용 (Applying Permissions to Routes)

```python
# 단일 권한 (Single permission)
@router.post("", dependencies=[Depends(require_permission("sales_order:create"))])

# Super Admin 전용 (Super Admin only)
@router.delete("", dependencies=[Depends(require_super_admin())])

# Tenant Admin 이상 (Tenant Admin or above)
@router.put("", dependencies=[Depends(require_tenant_admin())])

# OR 조건 (OR condition — any one permission suffices)
@router.get("", dependencies=[Depends(require_any_of("report:read", "admin:read"))])
```

---

## 페이지네이션 (Pagination)

모든 목록 조회 API는 페이지네이션을 지원한다.
All list APIs support pagination.

### 요청 (Request)

```
GET /api/v1/sales-orders?page=2&page_size=10
```

| 파라미터 (Parameter) | 기본값 (Default) | 최대값 (Max) | 설명 (Description) |
|----------|--------|--------|------|
| `page` | 1 | - | 페이지 번호 (Page number, starts at 1) |
| `page_size` | 20 (EntityMeta 설정에 따라 다름) | 100 | 페이지당 항목 수 (Items per page) |

### 응답 (Response)

```json
{
  "data": [...],
  "total": 42,
  "page": 2,
  "page_size": 10
}
```

---

## 서비스별 포트 및 Base URL (Service Ports and Base URLs)

| 서비스 (Service) | 패키지명 (Package) | 포트 (Port) | 설명 (Description) |
|--------|----------|------|------|
| gateway | `oneerp-gateway` | 8001 | 인증 (Auth), 전자결재 (Approval), 시스템 설정 (System Settings) |
| selling | `oneerp-selling` | 8002 | 판매 (Sales), 견적 (Quotation), POS |
| buying | `oneerp-buying` | 8003 | 구매 (Purchasing), 발주 (Purchase Order), 공급업체 (Supplier) |
| stock | `oneerp-stock` | 8004 | 재고 (Inventory), 창고 (Warehouse), 생산 (Manufacturing) |
| accounting | `oneerp-accounting` | 8005 | 회계 (Accounting), 분개 (Journal Entry), 세금 (Tax) |
| hr | `oneerp-hr` | 8006 | 인사 (HR), 근태 (Attendance), 평가 (Appraisal) |
| payroll | `oneerp-payroll` | 8007 | 급여 (Payroll), 급여명세 (Salary Slip) |
| expenses | `oneerp-expenses` | 8008 | 경비 (Expenses), 법인카드 (Corporate Card) |
| crm | `oneerp-crm` | 8009 | CRM, 리드 (Lead), 기회 (Opportunity) |
| assets | `oneerp-assets` | 8010 | 자산 (Assets), 감가상각 (Depreciation) |
| projects | `oneerp-projects` | 8011 | 프로젝트 (Projects), 타임시트 (Timesheet) |
| quality | `oneerp-quality` | 8012 | 품질검사 (Quality Inspection), 불량관리 (Defect Management) |

### 서비스 실행 방법 (How to Run Services)

```bash
uv run --package oneerp-{서비스명} --directory services/{서비스명} \
    uvicorn app.main:app --port {포트} --reload
```

### Swagger UI 접근 (Access Swagger UI)

각 서비스의 Swagger UI는 `http://localhost:{포트}/docs`에서 확인할 수 있다.
Each service's Swagger UI is available at `http://localhost:{port}/docs`.

---

## 헬스체크 (Health Check)

모든 서비스는 공통 헬스체크 엔드포인트 (common health check endpoint)를 제공한다.

```
GET /health
```

**응답 (Response):**

```json
{
  "status": "ok"
}
```

---

## 추적 ID (Request Tracking ID)

모든 요청에 `X-Request-Id` 헤더가 자동 부여된다.
Every request is automatically assigned an `X-Request-Id` header.
에러 응답의 `request_id` 필드에 동일한 값이 포함되어 로그 추적 (log tracing)에 활용할 수 있다.

---

## 이벤트 흐름 (Event Flow — 28 EventTypes)

서비스 간 비동기 통신 (async inter-service communication)은 NATS JetStream 기반 도메인 이벤트 (domain events)로 처리된다.
모든 이벤트는 `EventEnvelope`로 감싸져 발행되며, 하위 호환성 (backward compatibility)을 유지한다.

### EventEnvelope 구조 (EventEnvelope Structure)

```json
{
  "event_id": "uuid-...",
  "event": {
    "event_type": "sales_order.submitted",
    "doc_id": "SO-0001",
    "tenant_id": "tenant-001",
    "data": {},
    "triggered_by": "user-001"
  },
  "source_service": "selling",
  "timestamp": "2026-03-23T10:00:00Z",
  "schema_version": 1
}
```

### 전체 이벤트 목록 (Full Event List)

#### Selling 도메인 (Selling Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `sales_order.submitted` | 판매주문 제출 (Sales order submitted) | stock (재고 예약), accounting (분개 준비) |
| `sales_order.cancelled` | 판매주문 취소 (Sales order cancelled) | stock (예약 해제) |
| `quotation.submitted` | 견적 제출 (Quotation submitted) | - |
| `delivery_note.submitted` | 납품서 제출 (Delivery note submitted) | stock (재고 차감), accounting (매출 분개) |
| `sales_invoice.submitted` | 매출전표 제출 (Sales invoice submitted) | accounting (AR 분개) |

#### Buying 도메인 (Buying Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `purchase_order.submitted` | 발주서 제출 (Purchase order submitted) | stock (입고 예약) |
| `purchase_order.cancelled` | 발주서 취소 (Purchase order cancelled) | stock (예약 해제) |
| `purchase_receipt.submitted` | 입고전표 제출 (Purchase receipt submitted) | stock (재고 증가), accounting (AP 분개) |
| `purchase_receipt.completed` | 입고 완료 (Purchase receipt completed) | quality (품질검사 트리거) |
| `purchase_invoice.submitted` | 매입전표 제출 (Purchase invoice submitted) | accounting (AP 분개) |
| `material_request.submitted` | 자재요청 제출 (Material request submitted) | buying (발주 생성 트리거) |

#### Stock 도메인 (Stock Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `stock_entry.submitted` | 재고이동 제출 (Stock entry submitted) | accounting (재고평가 분개) |
| `stock_reconciliation.submitted` | 재고실사 제출 (Stock reconciliation submitted) | accounting (재고조정 분개) |
| `stock.reserved` | 재고 예약 완료 (Stock reserved) | selling (예약 확인) |
| `stock.delivered` | 출고 완료 (Stock delivered) | selling (납품 확인) |
| `stock.received` | 입고 완료 (Stock received) | buying (입고 확인) |

#### Accounting 도메인 (Accounting Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `journal_entry.submitted` | 분개 제출 (Journal entry submitted) | - |
| `payment_entry.submitted` | 지급/수금 제출 (Payment entry submitted) | selling (AR 차감), buying (AP 차감) |

#### HR 도메인 (HR Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `employee.created` | 직원 등록 (Employee created) | payroll (급여 구조 초기화) |
| `leave_application.approved` | 휴가 승인 (Leave application approved) | hr (잔여휴가 차감) |

#### Payroll 도메인 (Payroll Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `payroll_entry.submitted` | 급여처리 제출 (Payroll entry submitted) | accounting (급여 분개) |
| `salary_slip.submitted` | 급여명세 제출 (Salary slip submitted) | - |

#### Expenses 도메인 (Expenses Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `expense_claim.submitted` | 경비청구 제출 (Expense claim submitted) | gateway (결재 요청) |
| `expense_claim.approved` | 경비청구 승인 (Expense claim approved) | accounting (경비 분개) |

#### Approval 도메인 (Approval Domain)

| EventType | 발행 시점 (Triggered When) | 구독 서비스 (Subscribers) |
|-----------|-----------|-------------|
| `approval_request.approved` | 결재 승인 (Approval approved) | 원본 서비스 (Source service — status update) |
| `approval_request.rejected` | 결재 반려 (Approval rejected) | 원본 서비스 (Source service — status update) |
| `approval.approved` | 결재 완료 (Approval completed) | - |
| `approval.rejected` | 결재 반려 (Approval rejected) | - |

### 이벤트 흐름도 (Event Flow Diagram — Order-to-Cash Example)

```
[Selling]                    [Stock]                [Accounting]
    │                          │                        │
    ├─ sales_order.submitted ─→│ 재고 예약 (Reserve)    │
    │                          ├─ stock.reserved ──────→│
    │                          │                        │
    ├─ delivery_note.submitted→│ 재고 차감 (Deduct)     │
    │                          ├─ stock.delivered ─────→│ 매출 분개 (Revenue JE)
    │                          │                        │
    ├─ sales_invoice.submitted─────────────────────────→│ AR 분개 (AR JE)
    │                          │                        │
    │                          │         payment_entry ←│ 수금 처리 (Payment)
    │← AR 차감 (AR Reduction) ←────────────────────────←│
```

---

## 추가 참고 (Additional References)

- OpenAPI 스키마 (OpenAPI Schema): 각 서비스의 `/openapi.json`에서 자동 생성된 스키마 확인
- ReDoc: 각 서비스의 `/redoc`에서 읽기 편한 문서 (readable docs) 확인
- CORS: `ONEERP_CORS_ORIGINS` 환경변수로 허용 오리진 (allowed origins) 설정
