# 구매 모듈 (Buying Module)

## 개요 (Overview)

구매 모듈은 자재요청 (Material Request)부터 발주 (Purchase Order), 입고 (Receipt), 구매 송장 (Purchase Invoice), 지급 (Payment)까지의 조달 프로세스를 관리한다. 공급업체 관리 (Supplier Management), 견적 비교 (Quotation Comparison), 운송비 배부 (Landed Cost) 등을 지원한다.

## 사전 조건 (Prerequisites)

- Buying, Stock, Accounting 서비스와 공급업체/품목 마스터가 준비되어 있어야 한다.
- 입고와 지급 흐름을 볼 구매 문서 권한이 필요하다.
- 재고와 회계 연계를 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 자재요청, 발주서, 입고전표, 구매 송장, 지급 흐름을 설명할 수 있다.
- 재고 증가와 매입채무 분개를 확인할 수 있다.
- 다음 재고 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [재고 모듈](./04-stock.md)

## 주요 기능 (Key Features)

- 공급업체 관리 (Supplier Management)
- 자재요청 (Material Request)
- 견적요청 (Request for Quotation, RFQ)
- 공급업체 견적 (Supplier Quotation)
- 발주 (Purchase Order, PO)
- 입고 (Purchase Receipt)
- 구매 송장 (Purchase Invoice)
- 구매 반품 (Purchase Return)
- 운송비 배부 (Landed Cost Voucher)

## 업무 흐름 (Workflow)

```
자재요청          견적요청       공급업체 견적       발주          입고          구매 송장       지급
(Material Req.) → (RFQ)    → (Supplier Quot.) → (PO)     → (Receipt)  → (Purchase Inv.) → (Payment)
```

## 상세 기능 (Detailed Features)

### 공급업체 관리 (Supplier Management)

#### 생성 (Create)
1. **구매 (Buying) > 공급업체 (Supplier)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 업체명 (Supplier Name), 사업자등록번호 (Business Registration No.), 대표자 (Representative)를 입력한다.
3. 연락처 (Contact), 주소 (Address), 은행 정보 (Bank Info)를 입력한다.
4. 공급 가능 품목 (Supplied Items), 납기 조건 (Delivery Terms)을 설정한다.
5. **"저장 (Save)"** 을 클릭한다.
6. 목록과 상세의 워크벤치 카드에서 `status_badge`, 거래 요약, 최신 공급업체 평가, 권장 액션을 즉시 확인한다.
7. 제출된 발주/입고/매입송장/평가 이력이 있으면 삭제할 수 없고, 기존 이력은 보존한 채 비활성화하여 신규 거래만 막는다.

### 자재요청 (Material Request)

#### 생성 (Create)
1. **구매 (Buying) > 자재요청 (Material Request)** 에서 **"신규 (New)"** 를 클릭한다.
2. 요청 유형 (Request Type: 구매 Purchase/이전 Transfer/제조 Manufacture)을 선택한다.
3. 필요한 품목 (Item), 품목 그룹 (Item Group), 수량 (Qty), 납기일 (Required By Date), 예상 단가 (Estimated Unit Cost), 예산 한도 (Budget Limit)를 입력한다.
4. 저장 시 품목별 구매 가격 규칙과 공급업체 평가를 참고해 추천 공급업체 (Suggested Supplier)가 자동 제안된다.
5. **"제출 (Submit)"** 하면 예산과 승인 매트릭스를 먼저 검사한다.
6. 승인 대상이면 상태가 **승인 대기 (Pending Approval)** 로 바뀌고, 지정된 결재자가 승인한 뒤에만 구매주문 초안이 생성된다.
7. 제출된 자재요청은 취소할 수 있지만 삭제할 수 없다.

### 견적요청 (Request for Quotation, RFQ)

#### 생성 (Create)
1. 자재요청 (Material Request)에서 **"견적요청 생성 (Create RFQ)"** 을 클릭한다.
2. 견적을 받을 공급업체 (Suppliers)들을 선택한다.
3. **"발송 (Send)"** 하면 자재요청 품목이 복사된 RFQ가 생성되고 공급업체에게 견적 요청이 전달된다.

### 공급업체 견적 (Supplier Quotation)

1. 공급업체가 회신한 견적을 **구매 (Buying) > 공급업체 견적 (Supplier Quotation)** 에 등록할 때 RFQ 번호(`rfq_reference`)를 함께 기록한다.
2. 목록/상세는 `summary(item_count/total_qty/submitted_quote_count/rfq_supplier_count/comparison_rank/linked_purchase_order_count/is_lowest_quote)`, `status_badge(best_offer/selected_for_order/competing_quote/draft/cancelled)`, `recommended_action`, `available_actions`를 함께 보여준다.
3. `GET /api/v1/supplier-quotations?rfq_reference=RFQ-0001&status_badge=best_offer` 로 동일 RFQ의 최저가 견적만 모아 보고, `GET /api/v1/supplier-quotations/SQ-0001/summary` 카드에서 비교 순위와 후속 액션을 바로 확인한다.
4. 여러 견적을 비교하여 최적의 공급업체를 선택한다. (Compare multiple quotations to select the best supplier.)
5. 선택된 견적에서 **"발주 생성 (Create Purchase Order)"** 을 클릭하면 상세 `status_badge`가 `selected_for_order`로 바뀌고 `open_purchase_order` 액션이 활성화된다.
6. 제출된 공급업체 견적은 비교 이력 보존을 위해 삭제할 수 없고, 필요하면 취소 후 새 견적을 등록한다.

### 발주 (Purchase Order, PO)

#### 생성 (Create)
1. **구매 (Buying) > 발주 (Purchase Order)** 에서 **"신규 (New)"** 를 클릭하거나 견적에서 전환한다.
2. 품목 (Item), 수량 (Qty), 단가 (Rate), 납기일 (Delivery Date)을 확인한다. 견적에서 전환한 초안은 `valid_till` 값을 각 라인의 기본 납기일로 복사한다.
3. 구매승인매트릭스 (Purchase Approval Matrix)에 따라 승인 (Approval)이 필요할 수 있다.
4. **"제출 (Submit)"** 하면 발주가 확정된다.
5. 발주 상세/목록에는 `status_badge`, `remaining_qty`, `next_delivery_date`, `downstream_summary`가 함께 표시되어 입고/송장 진행 상태를 바로 확인할 수 있다.

### 입고 (Purchase Receipt)

#### 생성 (Create)
1. 발주 (Purchase Order)에서 **"입고 생성 (Create Receipt)"** 을 클릭한다.
2. 실제 입고 수량 (Received Qty)을 입력한다 (부분 입고 Partial Receipt 가능). 발주를 참조한 라인은 발주 잔량을 초과해 제출할 수 없다.
3. 품질 검사 (Quality Inspection)가 필요한 경우 라인에 `inspection_required=true` 를 지정한다.
4. **"제출 (Submit)"** 하면 재고 (Stock)가 증가하고 incoming 품질검사 초안이 자동 생성된다.
5. 제출 후 상세/목록에는 `status_badge`, `inspection_summary`, `downstream_summary`, `available_actions`가 함께 표시되어 검수 대기와 후속 구매송장 진행을 즉시 확인할 수 있다.
6. 제출된 입고에서는 **"구매 송장 생성 (Create Purchase Invoice)"** 으로 실제 수령 수량 기준의 송장 초안을 만들 수 있다.
7. 제출된 입고전표는 삭제할 수 없다. 검수 결과와 후속 조정은 품질/구매반품 프로세스로 처리한다.

### 구매 송장 (Purchase Invoice)

#### 생성 (Create)
1. 발주 (Purchase Order) 또는 입고 (Receipt)에서 **"구매 송장 생성 (Create Purchase Invoice)"** 을 클릭한다.
2. 청구 금액 (Amount)을 확인한다.
3. **"제출 (Submit)"** 하면 매입채무 (Accounts Payable)가 생성되고 회계 분개 (Journal Entry)가 자동 처리된다.
4. 상세/목록의 `status_badge`, `payment_summary`, `etax_summary`, `matching_summary`, `available_actions`로 지급 상태, 전자세금계산서 전송 상태, 발주-입고-송장 3-way 매칭 결과를 즉시 확인할 수 있다.
5. 입고 또는 발주 기준 수량/금액과 다르면 제출 단계에서 `ERR-BUY-054`가 발생하며, 참조 문서를 기준으로 송장을 수정해야 한다.

### 구매 반품 (Purchase Return)

#### 생성 (Create)
1. **구매 (Buying) > 구매반품 (Purchase Return)** 에서 원래 발주 (PO)/입고 (Receipt)를 선택한다.
2. 반품 품목 (Item), 수량 (Qty), 사유 (Reason)를 입력한다.
3. **"제출 (Submit)"** 하면 재고가 차감되고 매입채무 (AP)가 조정된다.

### 운송비 배부 (Landed Cost Voucher)

#### 생성 (Create)
1. **구매 (Buying) > 운송비 배부 전표 (Landed Cost Voucher)** 에서 **"신규 (New)"** 를 클릭한다.
2. 배부 대상 입고 전표 (Purchase Receipt)를 선택한다.
3. 운송비 (Freight), 관세 (Customs Duty) 등 부대비용 (Additional Costs)을 입력한다.
4. 배부 기준 (Allocation Method: 금액비례 By Amount/수량비례 By Quantity)을 선택한다.
5. **"제출 (Submit)"** 하면 품목별 원가 (Item Cost)가 조정된다.

## 관련 보고서 (Related Reports)

- 구매 분석 (Purchase Analytics) — 기간별 (Period)/공급업체별 (Supplier)/품목별 (Item) 구매 분석
  - KPI: 제출된 구매주문/구매송장 건수, 발주금액, 매입금액, 활성 공급업체 수, 미지급 overdue 건수
  - 차트: `purchase_trend`, `supplier_mix`, `item_mix`, `payable_pipeline`
  - 권장 액션: `review_overdue_payables`, `review_open_purchase_orders`, `review_top_suppliers`
- 공급업체 평가표 (Supplier Scorecard) — 납기 준수율 (Delivery Compliance), 품질 (Quality), 가격 (Pricing) 평가

## FAQ

- **Q: 부분 입고 (Partial Receipt)가 가능한가요?**
  A: 네, 발주 수량의 일부만 입고할 수 있습니다. 미입고분은 추후 입고합니다. (Yes, you can receive partial quantities.)

- **Q: 운송비 배부 (Landed Cost)는 언제 하나요?**
  A: 입고 완료 후, 구매 송장 제출 전에 진행하는 것을 권장합니다. (Recommended after receipt, before purchase invoice submission.)
