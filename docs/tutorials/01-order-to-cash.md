# 튜토리얼: Order-to-Cash (판매→수금) / Tutorial: Order-to-Cash

## 개요 (Overview)

판매주문 (Sales Order)에서 수금 (Collection)까지의 전체 흐름을 단계별로 실습한다.
이 시나리오는 Selling, Stock, Accounting 3개 서비스를 횡단하며,
도메인 이벤트 (Domain Event)를 통한 서비스 간 자동 연계를 보여준다.

This tutorial walks through the full Order-to-Cash flow, from creating a Sales Order to collecting payment.
It spans three services — Selling, Stock, and Accounting — demonstrating cross-service automation via domain events.

## 사전 조건 (Prerequisites)

- Selling, Stock, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 고객, 품목, 초기 재고가 준비되어 있어야 한다.
- 수금까지 확인하려면 회계 전표 생성 권한이 있어야 한다.

## 완료 조건 (Completion Criteria)

- 판매주문, 납품서, 매출전표, 수금 흐름이 순서대로 완료된다.
- 재고 차감과 매출 분개가 반영된다.
- 최종 원장과 수금 상태를 확인할 수 있다.

## 다음 단계 (Next Step)

- [구매→지급 튜토리얼](./02-procure-to-pay.md)

## 관련 문서 (Related Docs)

- [회계 모듈](../user-manual/01-accounting.md)
- [구매→지급 튜토리얼](./02-procure-to-pay.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Stock (포트 8004 / Port 8004)
uv run --package oneerp-stock --directory services/stock \
    uvicorn app.main:app --port 8004 --reload

# Selling (포트 8002 / Port 8002)
uv run --package oneerp-selling --directory services/selling \
    uvicorn app.main:app --port 8002 --reload

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

Debug 모드에서는 인증 없이 Super Admin 더미 사용자로 자동 인증된다.
In debug mode, requests are auto-authenticated as a Super Admin dummy user without credentials.

## Step 0: 견적서 발송 + 고객 전자서명 (Quotation Share + Signature)

견적서는 제출 후 고객 전달 패키지(PDF + 메일 발송 정보 + 포털 전자서명 링크)를 생성할 수 있다.

```bash
# 견적서 생성
curl -s -X POST http://localhost:8002/api/v1/quotations \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-0001",
    "customer_name": "테스트 고객",
    "transaction_date": "2026-04-09",
    "valid_till": "2026-04-30",
    "items": [
      {
        "item_code": "ITEM-A",
        "item_name": "테스트 품목 A",
        "qty": 2,
        "rate": 15000
      }
    ]
  }' | jq

# 제출 후 메일 발송 패키지 생성
curl -s -X POST http://localhost:8002/api/v1/quotations/QTN-0001/submit | jq
curl -s -X POST http://localhost:8002/api/v1/quotations/QTN-0001/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "customer@example.com",
    "subject": "견적 확인 요청",
    "message": "PDF와 전자서명 링크를 확인해 주세요."
  }' | jq
```

- `pdf_download_url` 로 제출 견적 PDF를 내려받을 수 있다.
- `portal_sign_url`, `portal_access_token`, `portal_access_expires_at` 이 함께 반환된다.
- 제출된 견적서는 삭제되지 않으며, 취소(Cancel)만 허용된다.

### 기초 데이터 생성 (Create Base Data)

#### 가격표 생성 및 카탈로그 확인 (Create a Price List and Review Catalog)

```bash
curl -s -X POST http://localhost:8002/api/v1/customer-groups \
  -H "Content-Type: application/json" \
  -d '{"group_name": "VIP", "default_price_list": ""}' | jq

curl -s -X POST http://localhost:8002/api/v1/price-lists \
  -H "Content-Type: application/json" \
  -d '{
    "price_list_name": "VIP USD",
    "currency": "USD",
    "selling": true,
    "customer_group": "VIP",
    "valid_from": "2026-04-01",
    "valid_to": "2026-04-30",
    "items": [
      {"item_code": "ITEM-A", "item_name": "테스트 품목 A", "price": "120", "min_qty": "1"},
      {"item_code": "ITEM-A", "item_name": "테스트 품목 A", "price": "110", "min_qty": "20"}
    ]
  }' | jq

curl -s "http://localhost:8002/api/v1/price-lists/catalog?customer_group=VIP&currency=USD&transaction_date=2026-04-09" | jq
curl -s "http://localhost:8002/api/v1/price-lists?status_badge=expiring_soon" | jq '.summary, .data[0].status_badge, .data[0].recommended_action'
```

- 카탈로그는 `is_active=true` 이고 거래일이 유효기간 안에 있는 가격표만 돌려준다.
- 목록/상세의 `usage_summary`, `rate_summary`, `status_badge`, `recommended_action` 으로 고객군 바인딩, 견적 사용량, 볼륨 단가 구간을 즉시 확인할 수 있다.
- `recommended_action=review_validity` 이면 만료 임박 가격표라서 먼저 유효기간을 갱신해야 한다.

#### 판매 분석 대시보드 확인 (Review Sales Analytics Dashboard)

```bash
curl -s "http://localhost:8002/api/v1/sales-analytics?group_by=customer" | jq \
  '.summary, .recommended_action, .charts.sales_trend, .data[0].status_badge'
```

- `summary` 는 제출된 송장 수, 총 매출, 활성 고객 수, stale 견적 수를 Cue 타일형으로 제공한다.
- `charts.sales_trend`, `charts.customer_mix`, `charts.item_mix`, `charts.quotation_pipeline` 으로 월별 추이와 고객/품목 기여도를 한 화면에서 확인한다.
- stale 견적이 남아 있으면 `recommended_action=review_stale_quotations` 가 반환되어 영업 후속 조치를 유도한다.

#### 고객 생성 (Create Customer)

```bash
curl -s -X POST http://localhost:8002/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "테스트 고객",
    "customer_type": "Company",
    "customer_group": "상업",
    "territory": "한국"
  }' | jq
```

**응답 (Response):**
```json
{
  "_id": "CUST-0001",
  "customer_name": "테스트 고객",
  "customer_type": "Company"
}
```

#### 판매 파트너 생성 + 고객 배정 (Create Sales Partner + Assign Customer)

```bash
curl -s -X POST http://localhost:8002/api/v1/sales-partners \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "서울 총판",
    "commission_rate": 7.5,
    "territory": "서울",
    "partner_type": "distributor"
  }' | jq

curl -s -X POST http://localhost:8002/api/v1/sales-partners/SPAR-0001/customers/CUST-0001 | jq
```

- 이후 생성되는 판매주문/매출전표에는 판매 파트너 스냅샷이 함께 저장된다.
- 고객을 다른 파트너로 재배정하더라도 기존 거래의 파트너 실적/수수료 이력은 유지된다.

#### 품목 생성 (Create Item)

```bash
curl -s -X POST http://localhost:8004/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "ITEM-A",
    "item_name": "테스트 품목 A",
    "item_group": "완제품",
    "stock_uom": "EA",
    "standard_rate": 10000,
    "valuation_method": "moving_average"
  }' | jq
```

#### 재고 확보 — 입고전표 생성 + 제출 (Stock Receipt — Create + Submit Stock Entry)

```bash
# 입고전표 생성 (Create stock entry)
curl -s -X POST http://localhost:8004/api/v1/stock-entries \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_type": "Material Receipt",
    "items": [
      {
        "item_code": "ITEM-A",
        "qty": 100,
        "target_warehouse": "WH-001",
        "basic_rate": 10000
      }
    ]
  }' | jq
# 응답에서 _id 확인 (Note the _id from the response, e.g., STE-0001)

# 입고전표 제출 → 재고 반영 (Submit stock entry → updates inventory)
curl -s -X POST http://localhost:8004/api/v1/stock-entries/STE-0001/submit | jq
```

---

## Step 1: 판매주문 생성 (Create Sales Order)

```bash
curl -s -X POST http://localhost:8002/api/v1/sales-orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUST-0001",
    "delivery_date": "2026-04-01",
    "items": [
      {
        "item_code": "ITEM-A",
        "qty": 10,
        "rate": 15000,
        "amount": 150000,
        "warehouse": "WH-001"
      }
    ],
    "total": 150000,
    "grand_total": 165000,
    "tax_total": 15000
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "SO-0001",
  "customer": "CUST-0001",
  "total": 150000,
  "grand_total": 165000
}
```

이 시점에서 판매주문은 **Draft** (docstatus=0) 상태이다. 수정과 삭제가 가능하다.
At this point the Sales Order is in **Draft** state (docstatus=0). It can be edited or deleted.

- 납기일이 거래일보다 빠르거나 품목이 0건이면 생성이 거부된다.

---

## Step 2: 판매주문 제출 (Submit Sales Order)

```bash
curl -s -X POST http://localhost:8002/api/v1/sales-orders/SO-0001/submit | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "SO-0001",
  "docstatus": 1,
  "customer": "CUST-0001"
}
```

**발생하는 이벤트 (Emitted Event):** `sales_order.submitted`

- Stock 서비스가 이벤트를 수신하여 재고 예약 (Stock Reservation)을 자동 생성한다.
- 이후 판매주문은 수정/삭제가 불가하며, 취소 (Cancel)만 가능하다.
- 상세 응답에 `status_badge="submitted"` 가 표시되고, 후속 문서 요약은 아직 0건이다.

---

## Step 3: 납품서 생성 + 제출 (Create + Submit Delivery Note)

판매주문에서 납품서 (Delivery Note)를 생성한다.

```bash
# 판매주문 기준 납품서 초안 생성 (Create delivery note draft)
curl -s -X POST http://localhost:8002/api/v1/sales-orders/SO-0001/delivery-note \
  -H "Content-Type: application/json" \
  -d '{
    "posting_date": "2026-04-01",
    "warehouse": "WH-001",
    "transporter": "대한통운"
  }' | jq
# 응답 (Response): {"id": "DN-0001", "sales_order_ref": "SO-0001", "downstream_summary": {"delivery_note_count": 1, ...}}

# 납품서 제출 (Submit delivery note)
curl -s -X POST http://localhost:8002/api/v1/delivery-notes/DN-0001/submit | jq
# warehouse가 비어 있으면 ERR-SELL-050 으로 제출이 차단된다.
```

**발생하는 이벤트 (Emitted Event):** `delivery_note.submitted`

```bash
# 제출 후 납품서 상세/목록에서 상태 배지와 후속 송장 요약 확인
curl -s http://localhost:8002/api/v1/delivery-notes/DN-0001 | jq '.status_badge, .downstream_summary, .available_actions'
curl -s "http://localhost:8002/api/v1/delivery-notes?status_badge=submitted&sales_order_ref=SO-0001&transporter=대한통운" | jq
```

- Stock 서비스가 이동평균법 (Moving Average)으로 재고를 차감한다.
- Accounting 서비스가 매출 분개 (Revenue Journal Entry)를 준비한다.

### 재고 잔량 확인 (Verify Stock Balance)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=ITEM-A&warehouse=WH-001" | jq
```

기존 100EA - 출고 10EA = 잔량 90EA를 확인한다.
Verify remaining stock: 100EA - 10EA shipped = 90EA remaining.

---

## Step 4: 매출전표 생성 + 제출 (Create + Submit Sales Invoice)

```bash
# 판매주문 기준 매출전표 초안 생성 (Create sales invoice draft from sales order)
curl -s -X POST http://localhost:8002/api/v1/sales-orders/SO-0001/sales-invoice \
  -H "Content-Type: application/json" \
  -d '{
    "posting_date": "2026-04-01",
    "due_date": "2026-05-01",
    "taxes": [
      {
        "tax_type": "VAT",
        "rate": 10,
        "amount": 15000
      }
    ]
  }' | jq
# 응답 (Response): {"id": "SINV-0001", "sales_order_ref": "SO-0001", "downstream_summary": {"sales_invoice_count": 1, ...}}

# 판매주문 상세에서 관련 문서 요약 확인
curl -s http://localhost:8002/api/v1/sales-orders/SO-0001 | jq
```

**기대 결과 (Expected Result):**

- 판매주문 상세 응답에 `downstream_refs.delivery_note_ids = ["DN-0001"]`, `downstream_refs.sales_invoice_ids = ["SINV-0001"]` 가 저장된다.
- `downstream_summary.delivery_note_count = 1`, `downstream_summary.sales_invoice_count = 1` 로 후속 문서 건수가 즉시 보인다.

```bash
# 매출전표 제출 (Submit sales invoice)
curl -s -X POST http://localhost:8002/api/v1/sales-invoices/SINV-0001/submit | jq

# 제출 후 송장 상세/목록에서 상태·수금·전자세금계산서 요약 확인
curl -s http://localhost:8002/api/v1/sales-invoices/SINV-0001 | jq '.status_badge, .payment_summary, .etax_summary, .available_actions'
curl -s "http://localhost:8002/api/v1/sales-invoices?customer_id=CUST-0001&status_badge=submitted_unpaid&transmission_status=pending" | jq
```

**발생하는 이벤트 (Emitted Event):** `sales_invoice.submitted`

Accounting 서비스가 자동 분개 (Auto Journal Entry)를 생성한다:

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 매출채권 (Accounts Receivable, AR) | 165,000 | - |
| 대변 | 매출 (Revenue) | - | 150,000 |
| 대변 | 부가세 예수금 (VAT Payable) | - | 15,000 |

- `etax_invoice_ref` 가 없던 송장은 전자세금계산서 초안이 자동 생성되어 `etax_summary.transmission_status = "pending"` 으로 표시된다.
- `payment_summary` 에서 총액/미수금/수금액을 즉시 확인할 수 있으므로, 이후 수금 단계에서 별도 화면 이동 없이 청구 상태를 확인할 수 있다.

---

## Step 5: 수금 처리 (Receive Payment)

```bash
# 수금 전표 생성 (Create payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries \
  -H "Content-Type: application/json" \
  -d '{
    "payment_type": "Receive",
    "party_type": "Customer",
    "party": "CUST-0001",
    "paid_amount": 165000,
    "received_amount": 165000,
    "reference_doctype": "Sales Invoice",
    "reference_name": "SINV-0001",
    "mode_of_payment": "은행이체"
  }' | jq
# 응답 (Response): {"_id": "PE-0001", ...}

# 수금 전표 제출 (Submit payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries/PE-0001/submit | jq
```

**발생하는 이벤트 (Emitted Event):** `payment_entry.submitted`

- 매출채권 (AR) outstanding에서 165,000원이 차감된다.
- 분개 (Journal Entry): 차변 (Debit) 은행 165,000 / 대변 (Credit) 매출채권 165,000

### 5-A. 수금 전 고객별 미수금 우선순위 확인 (Review Collection Priority Before Payment)

```bash
curl -s "http://localhost:8005/api/v1/accounts-receivable?voucher_no=SINV-0001&as_of_date=2026-04-20" | jq
# customer_breakdown / collection_status / recommended_action 확인
```

- `summary.customer_breakdown`에서 고객별 총 미수금, 연체 금액, 최근 독촉 단계가 보인다.
- 라인 상세(`/api/v1/accounts-receivable/{doc_id}`)에서는 `available_actions`와 `dunning_summary`를 확인할 수 있다.
- `recommended_action`이 `create_dunning` 또는 `call_customer`이면 수금 담당자가 먼저 독촉/콜백 액션을 진행한다.

---

## 검증 (Verification)

### 1. 재고 잔량 확인 (Verify Stock Balance)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=ITEM-A" | jq '.data[-1].qty_after_transaction'
# 기대값 (Expected): 90
```

### 2. 분개 차대변 일치 확인 (Verify Debit/Credit Balance)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=SINV-0001" | jq
# 차변 합계 = 대변 합계 확인 (Verify total debits = total credits)
```

### 3. 매출채권 잔액 0 확인 (Verify AR Balance is Zero)

```bash
curl -s "http://localhost:8005/api/v1/accounts-receivable?customer=CUST-0001" | jq '.data[0].outstanding'
# 기대값 (Expected): 0
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Selling]                    [Stock]                [Accounting]
    |                          |                        |
  1. 판매주문 생성 (Draft)      |                        |
     Create Sales Order        |                        |
    |                          |                        |
  2. 판매주문 제출 -----------> 재고 예약                 |
     Submit SO                 Stock Reservation        |
    |                          |                        |
  3. 납품서 생성+제출 --------> 재고 차감 (이동평균)      |
     Create+Submit DN          Deduct Stock (MA)  ----> 매출 분개 준비
    |                          |                        Prepare Revenue JE
    |                          |                        |
  4. 매출전표 생성+제출 --------------------------> AR 분개 생성
     Create+Submit SI                               Create AR JE
    |                          |                  (Dr: AR / Cr: Revenue+VAT)
    |                          |                        |
    |                          |               5. 수금 전표 생성+제출
    |                          |                  Create+Submit Payment
    |                          |                  (Dr: Bank / Cr: AR)
    |                          |                        |
    |                          |                   AR 잔액 = 0
    |                          |                   AR Balance = 0
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 판매주문 (Sales Order) → 납품서 (Delivery Note) → 매출전표 (Sales Invoice) → 수금 (Payment)의 전체 흐름
- 판매 파트너 상세에서 `summary`, `status_badge`, `recommended_action` 으로 대리점 실적과 미수 리스크를 바로 확인하는 흐름
- 문서 제출 (Submit) 시 발생하는 도메인 이벤트 (Domain Event)와 서비스 간 자동 연계
- 분개 (Journal Entry)의 차변/대변 (Debit/Credit) 원리
- 이동평균법 (Moving Average) 기반 재고 평가
