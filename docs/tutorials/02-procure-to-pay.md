# 튜토리얼: Procure-to-Pay (구매→지급) / Tutorial: Procure-to-Pay

## 개요 (Overview)

자재요청 (Material Request)에서 대금 지급 (Payment)까지의 전체 구매 흐름을 단계별로 실습한다.
이 시나리오는 Buying, Stock, Accounting 3개 서비스를 횡단하며,
도메인 이벤트를 통한 서비스 간 자동 연계를 보여준다.

This tutorial walks through the complete Procure-to-Pay flow — from Material Request to payment.
It spans Buying, Stock, and Accounting services, demonstrating cross-service automation via domain events.

## 사전 조건 (Prerequisites)

- Buying, Stock, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 공급업체와 구매 대상 품목이 준비되어 있어야 한다.
- 입고와 지급까지 보려면 회계/구매 전표 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 자재요청, 발주서, 입고전표, 매입전표 흐름이 완료된다.
- 재고 증가와 매입채무 분개가 반영된다.
- 지급 후 상태를 조회할 수 있다.

## 다음 단계 (Next Step)

- [경비→결재→회계 튜토리얼](./03-expense-approval.md)

## 관련 문서 (Related Docs)

- [회계 모듈](../user-manual/01-accounting.md)
- [경비→결재→회계 튜토리얼](./03-expense-approval.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Buying (포트 8003 / Port 8003)
uv run --package oneerp-buying --directory services/buying \
    uvicorn app.main:app --port 8003 --reload

# Stock (포트 8004 / Port 8004)
uv run --package oneerp-stock --directory services/stock \
    uvicorn app.main:app --port 8004 --reload

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

### 기초 데이터 생성 (Create Base Data)

#### 공급업체 생성 (Create Supplier)

```bash
curl -s -X POST http://localhost:8003/api/v1/suppliers \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "테스트 공급업체",
    "supplier_group": "원자재",
    "supplier_type": "Company",
    "country": "한국"
  }' | jq
```

**응답 (Response):**
```json
{
  "_id": "SUP-0001",
  "id": "SUP-0001",
  "supplier_name": "테스트 공급업체",
  "supplier_group": "원자재",
  "supplied_items": []
}
```

등록 직후 워크벤치 요약을 확인할 때는 아래처럼 `status_badge`, 거래 요약, 권장 액션을 조회한다.

```bash
curl -s "http://localhost:8003/api/v1/suppliers/SUP-0001/summary" | jq
```

#### 품목 생성 (Create Item)

Stock 서비스에 구매 대상 품목이 등록되어 있어야 한다.
The target item must be registered in the Stock service.

```bash
curl -s -X POST http://localhost:8004/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "RAW-A",
    "item_name": "원자재 A",
    "item_group": "원자재",
    "stock_uom": "KG",
    "standard_rate": 5000,
    "valuation_method": "moving_average"
  }' | jq
```

---

## Step 1: 자재요청 생성 + 제출 (Create + Submit Material Request)

현장에서 자재가 필요할 때 자재요청 (Material Request)을 생성한다.
When materials are needed, create a Material Request.

```bash
curl -s -X POST http://localhost:8003/api/v1/material-requests \
  -H "Content-Type: application/json" \
  -d '{
    "material_request_type": "Purchase",
    "required_date": "2026-04-01",
    "items": [
      {
        "item_code": "RAW-A",
        "qty": 500,
        "warehouse": "WH-001",
        "uom": "KG"
      }
    ]
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "id": "MR-2026-00001",
  "budget_status": "within_budget",
  "suggested_supplier_id": "SUP-2026-00001"
}
```

### 자재요청 제출 (Submit Material Request)

```bash
curl -s -X POST http://localhost:8003/api/v1/material-requests/MREQ-0001/submit | jq
```

**발생하는 이벤트 (Emitted Event):** `material_request.submitted`

- Buying 서비스가 예산 한도와 승인 매트릭스를 먼저 검사한다.
- 승인 대상이면 `approval_status=pending`으로 저장되고, 지정된 결재자가 승인할 때까지 발주 생성이 보류된다.
- 이미 자재요청 화면에서 여러 공급업체를 골라 `POST /api/v1/material-requests/MREQ-0001/create-rfq`로 RFQ를 직접 만들 수 있다.

---

## Step 2: 발주서 생성 + 제출 (Create + Submit Purchase Order)

제출된 공급업체 견적에서 발주서 (Purchase Order, PO)를 생성하고, 발주 상세에서 납기/하위문서 진행 상태를 확인한다.

```bash
# 공급업체 견적 제출
curl -s -X POST http://localhost:8003/api/v1/supplier-quotations/SQ-0001/submit | jq

# 공급업체 견적 워크벤치 (best_offer / selected_for_order 확인)
curl -s "http://localhost:8003/api/v1/supplier-quotations?rfq_reference=RFQ-0001&status_badge=best_offer" | jq
curl -s http://localhost:8003/api/v1/supplier-quotations/SQ-0001/summary | jq '{
  status_badge,
  recommended_action,
  summary
}'

# 발주서 생성 (Create PO from quotation)
curl -s -X POST http://localhost:8003/api/v1/purchase-orders/from-quotation/SQ-0001 | jq

# 발주 생성 후 선택된 견적 상태 확인
curl -s http://localhost:8003/api/v1/supplier-quotations/SQ-0001 | jq '{
  status_badge,
  available_actions,
  summary
}'

# 발주서 제출 (Submit PO)
curl -s -X POST http://localhost:8003/api/v1/purchase-orders/PO-0001/submit | jq

# 발주 진행 요약 확인 (납기일/입고·송장 초안 카운트)
curl -s http://localhost:8003/api/v1/purchase-orders/PO-0001 | jq '{
  status_badge,
  next_delivery_date,
  remaining_qty,
  downstream_summary
}'
```

**발생하는 이벤트 (Emitted Event):** `purchase_order.submitted`

- Stock 서비스가 입고 예약 (Inbound Reservation)을 생성한다.

---

## Step 3: 입고전표 생성 + 제출 (Create + Submit Purchase Receipt)

공급업체로부터 물품을 수령하면 입고전표 (Purchase Receipt)를 생성한다.

```bash
# 입고전표 생성 (Create purchase receipt)
curl -s -X POST http://localhost:8003/api/v1/purchase-receipts \
  -H "Content-Type: application/json" \
  -d '{
    "supplier": "SUP-0001",
    "purchase_order": "PO-0001",
    "items": [
      {
        "item_code": "RAW-A",
        "qty": 500,
        "rate": 5000,
        "amount": 2500000,
        "warehouse": "WH-001"
      }
    ]
  }' | jq

# 입고전표 제출 (Submit purchase receipt)
curl -s -X POST http://localhost:8003/api/v1/purchase-receipts/PREC-0001/submit | jq

# 입고 상세에서 검수/송장 진행 요약 확인 (Check inspection + invoice summary)
curl -s http://localhost:8003/api/v1/purchase-receipts/PREC-0001 | jq

# 실제 수령 수량 기준 구매송장 초안 생성 (Create purchase invoice draft from receipt)
curl -s -X POST http://localhost:8003/api/v1/purchase-receipts/PREC-0001/purchase-invoice | jq
```

**발생하는 이벤트 (Emitted Event):** `purchase_receipt.submitted`

- Stock 서비스가 이동평균법 (Moving Average)으로 재고를 증가시킨다.
- Accounting 서비스가 매입채무 (Accounts Payable, AP) 분개를 준비한다.
- 입고 상세/목록의 `status_badge`, `inspection_summary`, `downstream_summary`, `available_actions`로 검수 대기와 후속 송장 초안 수를 즉시 확인할 수 있다.

### 재고 확인 (Verify Stock)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=RAW-A&warehouse=WH-001" | jq
# 재고 500 KG 확인 (Verify 500 KG in stock)
```

---

## Step 4: 매입전표 생성 + 제출 (Create + Submit Purchase Invoice)

```bash
# 매입전표 생성 (Create purchase invoice)
curl -s -X POST http://localhost:8005/api/v1/purchase-invoices \
  -H "Content-Type: application/json" \
  -d '{
    "supplier": "SUP-0001",
    "purchase_order": "PO-0001",
    "purchase_receipt": "PREC-0001",
    "items": [
      {
        "item_code": "RAW-A",
        "qty": 500,
        "rate": 5000,
        "amount": 2500000
      }
    ],
    "total": 2500000,
    "tax_total": 250000,
    "grand_total": 2750000
  }' | jq

# 매입전표 제출 (Submit purchase invoice)
curl -s -X POST http://localhost:8005/api/v1/purchase-invoices/PINV-0001/submit | jq

# 구매송장 워크벤치 확인
curl -s http://localhost:8005/api/v1/purchase-invoices/PINV-0001 | jq '{
  status_badge,
  payment_summary,
  etax_summary,
  matching_summary,
  available_actions
}'
```

**발생하는 이벤트 (Emitted Event):** `purchase_invoice.submitted`

Accounting 서비스가 자동 분개 (Auto Journal Entry)를 생성한다:

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 재고자산 (Inventory) | 2,500,000 | - |
| 차변 | 부가세 대급금 (Input VAT) | 250,000 | - |
| 대변 | 매입채무 (Accounts Payable, AP) | - | 2,750,000 |

입고/발주 참조 수량 또는 금액이 다르면 `ERR-BUY-054`로 제출이 차단되므로, 참조 문서 기준으로 수량·단가를 맞춘 뒤 다시 제출한다.

---

## Step 5: 대금 지급 (Make Payment)

```bash
# 지급 전표 생성 (Create payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries \
  -H "Content-Type: application/json" \
  -d '{
    "payment_type": "Pay",
    "party_type": "Supplier",
    "party": "SUP-0001",
    "paid_amount": 2750000,
    "received_amount": 2750000,
    "reference_doctype": "Purchase Invoice",
    "reference_name": "PINV-0001",
    "mode_of_payment": "은행이체"
  }' | jq

# 지급 전표 제출 (Submit payment entry)
curl -s -X POST http://localhost:8005/api/v1/payment-entries/PE-0002/submit | jq
```

**발생하는 이벤트 (Emitted Event):** `payment_entry.submitted`

- 매입채무 (AP) outstanding에서 2,750,000원이 차감된다.
- 분개 (Journal Entry): 차변 (Debit) 매입채무 2,750,000 / 대변 (Credit) 은행 2,750,000

---

## 검증 (Verification)

### 1. 재고 잔량 확인 (Verify Stock Balance)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=RAW-A" | jq '.data[-1].qty_after_transaction'
# 기대값 (Expected): 500
```

### 2. 매입채무 잔액 0 확인 (Verify AP Balance is Zero)

```bash
curl -s "http://localhost:8005/api/v1/accounts-payable?supplier=SUP-0001" | jq '.data[0].outstanding_amount'
# 기대값 (Expected): 0
curl -s "http://localhost:8005/api/v1/accounts-payable?supplier=SUP-0001&as_of_date=2026-04-25" | jq '.summary.supplier_breakdown[0]'
# 기대값 (Expected): status_badge=settled, recommended_action=none
```

### 3. 분개 차대변 일치 확인 (Verify Debit/Credit Balance)

```bash
curl -s "http://localhost:8005/api/v1/journal-entries?reference=PINV-0001" | jq
# 차변 합계 = 대변 합계 확인 (Verify total debits = total credits)
```

### 4. 구매 분석 워크벤치 확인 (Verify Purchase Analytics Workbench)

```bash
curl -s "http://localhost:8003/api/v1/purchase-analytics?group_by=supplier&status_badge=payment_due" | jq '{
  summary,
  recommended_action,
  first_row: .data[0],
  charts
}'
# 기대값 (Expected):
# - summary.overdue_payable_count >= 1
# - first_row.status_badge = "payment_due"
# - charts.purchase_trend / supplier_mix / item_mix / payable_pipeline 존재
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Buying]                     [Stock]                [Accounting]
    |                          |                        |
  1. 자재요청 (MREQ)           |                        |
     Material Request          |                        |
    |                          |                        |
  2. 발주서 생성+제출 -------> 입고 예약                 |
     Create+Submit PO          Inbound Reservation      |
    |                          |                        |
  3. 입고전표 생성+제출 -----> 재고 증가 (이동평균)       |
     Create+Submit PR          Add Stock (MA)     ----> AP 분개 준비
    |                          |                        Prepare AP JE
    |                          |                        |
    |                          |               4. 매입전표 생성+제출
    |                          |                  Create+Submit PI
    |                          |                  (Dr: Inventory+VAT / Cr: AP)
    |                          |                        |
    |                          |               5. 지급 전표 생성+제출
    |                          |                  Create+Submit Payment
    |                          |                  (Dr: AP / Cr: Bank)
    |                          |                        |
    |                          |                   AP 잔액 = 0
    |                          |                   AP Balance = 0
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 자재요청 (Material Request) → 발주서 (PO) → 입고전표 (Purchase Receipt) → 매입전표 (Purchase Invoice) → 지급 (Payment)의 전체 흐름
- 3-way matching: 발주서, 입고전표, 매입전표 간 수량/금액 대조
- 이동평균법 (Moving Average) 기반 재고 평가 (Valuation)
- 매입채무 (AP) 분개 (Journal Entry)와 대금 지급 처리
