# OneERP Buying 서비스 (Buying Service)

> 구매요청, 발주, 입고, 공급업체 관리 등 구매 프로세스를 관리하는 서비스 / Manages the procurement process including purchase requests, purchase orders, receipts, and supplier management

## 도메인 개요 (Domain Overview)

Buying 서비스는 자재요청 (Material Request)부터 견적요청 (RFQ), 공급업체 견적 비교, 발주 (Purchase Order), 구매 송장 (Purchase Invoice), 입고 검수 (Purchase Receipt)까지의 조달 프로세스 (Procurement Process)를 담당한다. 공급업체 평가 (Supplier Scorecard), 구매 승인 매트릭스 (Buyer Approval Matrix), 수입 신고 (Import Declaration), 운송비 배부 (Landed Cost) 등 글로벌 구매 업무를 지원한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8003 |

## 엔티티 (Entities) — 14개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Supplier | suppliers | 공급업체 (Supplier) |
| SupplierGroup | supplier_groups | 공급업체그룹 (Supplier Group) |
| SupplierScorecard | supplier_scorecards | 공급업체평가 (Supplier Scorecard) |
| BuyerApprovalMatrix | buyer_approval_matrices | 구매승인매트릭스 (Buyer Approval Matrix) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ImportDeclaration | import_declarations | 수입 신고 (Import Declaration) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| PurchaseProcessService | 구매 프로세스 실행 | 구매 워크플로우 통합 관리 (Purchase Workflow) |
| ProcurementFlow | 조달 흐름 제어 | MR -> RFQ -> PO 자동 연결 (Procurement Flow) |
| BuyerApprovalService | 승인 매트릭스 검증 | 금액별 구매 승인 (Approval by Amount) |
| LandedCostService | 운송비 배부 계산 | 구매 원가에 부대비용 배분 (Landed Cost Allocation) |
| PurchaseReturnService | 구매 반품 처리 | 반품/교환 워크플로우 (Purchase Return) |
| SupplierScorecardService | 공급업체 평가 | 납기, 품질, 가격 종합 평가 (Supplier Evaluation) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 5개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/purchase-orders | 발주 관리 (Purchase Orders) |
| CRUD | /api/v1/purchase-invoices | 구매 송장 관리 (Purchase Invoices) |
| CRUD | /api/v1/purchase-receipts | 입고 관리 (Purchase Receipts) |
| CRUD | /api/v1/material-requests | 자재요청 관리 (Material Requests) |
| CRUD | /api/v1/supplier-quotations | 공급업체 견적 관리 (Supplier Quotations) |
| CRUD | /api/v1/purchase-returns | 구매 반품 처리 (Purchase Returns) |
| CRUD | /api/v1/request-for-quotations | 견적요청 관리 (RFQ) |
| CRUD | /api/v1/landed-cost-vouchers | 운송비 배부 전표 (Landed Cost Vouchers) |
| GET | /api/v1/purchase-analytics | 구매 분석 (Purchase Analytics) |

## 이벤트 (Events)

### 구독 (Subscribed)
| EventType | 핸들러 (Handler) |
|-----------|-----------------|
| 구매 관련 이벤트 (Purchase Events) | events/handlers.py |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-buying --directory services/buying uvicorn app.main:app --port 8003
```

## 테스트 (Testing)

```bash
uv run pytest services/buying/ -m "not integration and not e2e" -v
```
