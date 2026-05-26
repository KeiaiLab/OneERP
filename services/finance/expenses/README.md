# OneERP Expenses 서비스 (Expenses Service)

> 경비 청구, 법인카드 관리, 출장 신청 등 경비 관리를 담당하는 서비스 / Manages expense claims, corporate card management, and travel requests

## 도메인 개요 (Domain Overview)

Expenses 서비스는 직원 경비 청구 (Expense Claim) — 승인/반려 워크플로우 (Approval/Rejection Workflow) 포함 — 법인카드 (Corporate Card) 등록 및 거래 내역 관리, 출장 신청/정산 (Travel Request/Settlement) 등 기업 경비 관리 전반을 담당한다. 모든 엔티티가 커스텀 로직 (승인/반려, 법인카드 거래 연동 등)을 포함하여 커스텀 라우터로 관리된다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8008 |

## 엔티티 (Entities) — 5개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ExpenseType | expense_types | 경비유형 (Expense Type) |
| CorporateCard | corporate_cards | 법인카드 (Corporate Card) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ExpenseClaim | expense_claims | 경비청구 (Expense Claim) |
| CorporateCardTransaction | corporate_card_transactions | 법인카드거래 (Corporate Card Transaction) |
| TravelRequest | travel_requests | 출장신청 (Travel Request) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| ExpenseService | 경비 청구 생성, 승인/반려, 정산 | 경비 워크플로우 관리 (Expense Workflow) |

## API 엔드포인트 (API Endpoints)

### 커스텀 라우트 (Custom Routes)
모든 엔티티가 커스텀 라우터로 관리 (All entities managed via custom routes)

| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/expense-claims | 경비 청구 (Expense Claims) — 승인/반려 포함 |
| CRUD | /api/v1/expense-types | 경비유형 관리 (Expense Types) |
| CRUD | /api/v1/corporate-cards | 법인카드 관리 (Corporate Cards) |
| CRUD | /api/v1/corporate-card-transactions | 법인카드 거래 관리 (Corporate Card Transactions) |
| CRUD | /api/v1/travel-requests | 출장 신청 관리 (Travel Requests) |

## 이벤트 (Events)

### 구독 (Subscribed)
| EventType | 핸들러 (Handler) |
|-----------|-----------------|
| 경비 관련 이벤트 (Expense Events) | events/handlers.py |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-expenses --directory services/expenses uvicorn app.main:app --port 8008
```

## 테스트 (Testing)

```bash
uv run pytest services/expenses/ -m "not integration and not e2e" -v
```
