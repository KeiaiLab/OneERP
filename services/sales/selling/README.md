# OneERP Selling 서비스 (Selling Service)

> 견적, 판매주문, 송장, POS, 구독 등 판매 도메인 전체를 관리하는 서비스 / Manages the entire sales domain including quotations, sales orders, invoices, POS, and subscriptions

## 도메인 개요 (Domain Overview)

Selling 서비스는 견적서 (Quotation) 작성부터 판매주문 (Sales Order), 매출 송장 (Sales Invoice) 발행, 납품 (Delivery)까지의 판매 프로세스를 담당한다. POS 거래 (POS Transaction), 구독/렌탈 (Subscription/Rental) 비즈니스, 마켓플레이스 연동 (Marketplace Integration), 프로모션/쿠폰/로열티 (Promotion/Coupon/Loyalty) 관리 등 다양한 판매 채널과 정책을 지원한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8002 |

## 엔티티 (Entities) — 38개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Customer | customers | 고객 (Customer) |
| CustomerGroup | customer_groups | 고객그룹 (Customer Group) |
| Territory | territories | 영업구역 (Territory) |
| SalesPartner | sales_partners | 판매 파트너 (Sales Partner) |
| PriceList | price_lists | 가격표 (Price List) |
| PricingRule | pricing_rules | 가격규칙 (Pricing Rule) |
| POSProfile | pos_profiles | POS 프로필 (POS Profile) |
| POSPaymentMethod | pos_payment_methods | POS 결제 수단 (POS Payment Method) |
| SalesPerson | sales_persons | 영업 사원 (Sales Person) |
| SalesTeam | sales_teams | 영업 팀 (Sales Team) |
| PromotionalScheme | promotional_schemes | 프로모션 (Promotional Scheme) |
| SalesTarget | sales_targets | 영업 목표 (Sales Target) |
| CouponCode | coupon_codes | 쿠폰 코드 (Coupon Code) |
| LoyaltyProgram | loyalty_programs | 로열티 프로그램 (Loyalty Program) |
| SubscriptionPlan | subscription_plans | 구독 플랜 (Subscription Plan) |
| CommissionPlan | commission_plans | 수수료 플랜 (Commission Plan) |
| ECommerceChannel | e_commerce_channels | 이커머스 채널 (E-Commerce Channel) |
| RentalItem | rental_items | 렌탈 품목 (Rental Item) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| DeliveryNote | delivery_notes | 납품서 (Delivery Note) |
| POSClosingEntry | pos_closing_entries | POS 마감 (POS Closing Entry) |
| Subscription | subscriptions | 구독 (Subscription) |
| SubscriptionInvoice | subscription_invoices | 구독 청구서 (Subscription Invoice) |
| RecurringInvoice | recurring_invoices | 반복 청구서 (Recurring Invoice) |
| SalesCommission | sales_commissions | 판매 수수료 (Sales Commission) |
| DropShipOrder | drop_ship_orders | 직배송 주문 (Drop Ship Order) |
| MarketplaceOrder | marketplace_orders | 마켓플레이스 주문 (Marketplace Order) |
| RentalOrder | rental_orders | 렌탈 주문 (Rental Order) |
| RentalReturn | rental_returns | 렌탈 반납 (Rental Return) |
| ReturnMerchandiseAuthorization | return_merchandise_authorizations | 반품 승인 (RMA) |
| ExportDeclaration | export_declarations | 수출 신고 (Export Declaration) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| PricingRuleService | 가격 규칙 적용, 할인 계산 | 가격 정책 엔진 (Pricing Engine) |
| SalesReturnService | 반품 처리, 재고 반영 | 판매 반품 워크플로우 (Sales Return) |
| BlanketOrderService | 포괄주문 관리, 릴리즈 | 장기 계약 기반 주문 (Blanket Order) |
| SubscriptionService | 구독 생성, 갱신, 청구 | 반복 과금 관리 (Recurring Billing) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 30개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/quotations | 견적서 관리 (Quotations) |
| CRUD | /api/v1/sales-orders | 판매주문 관리 (Sales Orders) |
| CRUD | /api/v1/sales-invoices | 매출 송장 관리 (Sales Invoices) |
| CRUD | /api/v1/sales-returns | 판매 반품 처리 (Sales Returns) |
| CRUD | /api/v1/blanket-orders | 포괄주문 관리 (Blanket Orders) |
| CRUD | /api/v1/pos-transactions | POS 거래 (POS Transactions) |
| CRUD | /api/v1/pos-receipts | POS 영수증 (POS Receipts) |
| GET | /api/v1/sales-analytics | 판매 분석 (Sales Analytics) |

## 이벤트 (Events)

### 발행 (Published)
| EventType | 트리거 (Trigger) |
|-----------|-----------------|
| DELIVERY_NOTE_SUBMITTED | 납품서 제출 시 (On Delivery Note Submit) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-selling --directory services/selling uvicorn app.main:app --port 8002
```

## 테스트 (Testing)

```bash
uv run pytest services/selling/ -m "not integration and not e2e" -v
```
