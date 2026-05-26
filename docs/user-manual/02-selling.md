# 판매 모듈 (Selling Module)

## 개요 (Overview)

판매 모듈은 견적서 (Quotation) 작성부터 판매주문 (Sales Order), 송장 발행 (Invoice), 납품 (Delivery), 수금 (Payment)까지의 영업 프로세스를 관리한다. POS 거래 (POS Transaction), 프로모션 (Promotion) 등도 지원한다.

## 사전 조건 (Prerequisites)

- Selling 서비스와 고객/품목 마스터가 준비되어 있어야 한다.
- 견적, 송장, 수금 흐름을 볼 가격표와 결제 수단이 준비되어 있어야 한다.
- 판매 문서를 제출할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 견적에서 판매주문, 납품, 송장, 수금으로 이어지는 흐름을 설명할 수 있다.
- POS 거래와 프로모션 진입점을 확인할 수 있다.
- 다음 구매 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [구매 모듈](./03-buying.md)

## 주요 기능 (Key Features)

- 고객 관리 (Customer Management)
- 판매 파트너 (Sales Partner)
- 견적서 작성 (Quotation)
- 판매주문 (Sales Order)
- 납품서 (Delivery Note)
- 매출 송장 (Sales Invoice)
- 수금 처리 (Payment Entry)
- 반품 처리 (Sales Return)
- POS 거래 (POS Transaction)
- 프로모션 및 쿠폰 (Promotion & Coupon)

## 업무 흐름 (Workflow)

```
고객 등록       견적서        판매주문       납품서        매출 송장       수금
(Customer) → (Quotation) → (Sales Order) → (Delivery) → (Sales Invoice) → (Payment)
```

## 상세 기능 (Detailed Features)

### 고객 관리 (Customer Management)

#### 생성 (Create)
1. **판매 (Selling) > 고객 (Customer)** 메뉴에서 **"신규 (New)"** 를 클릭한다. (Navigate to Selling > Customer and click "New".)
2. 고객명 (Customer Name), 고객그룹 (Customer Group), 영업구역 (Territory)을 입력한다.
3. 연락처 (Contact), 주소 (Address) 정보를 추가한다.
4. 결제 조건 (Payment Terms), 가격표 (Price List)를 설정한다.
5. **"저장 (Save)"** 을 클릭한다.

### 가격표 (Price List)

#### 생성 및 운영 (Create & Operate)
1. **판매 (Selling) > 가격표 (Price List)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 가격표명, 통화, 고객그룹, 유효기간을 입력하고 품목별 단가와 최소 수량 구간을 설정한다.
3. 목록/상세에는 `summary` 또는 `usage_summary`, `rate_summary`, `status_badge`, `recommended_action`, `available_actions`가 함께 표시된다.
4. `status_badge=expiring_soon` 필터로 만료 임박 가격표만 모아 보고, `recommended_action=review_validity` 가 보이면 유효기간을 먼저 갱신한다.
5. 카탈로그 미리보기 (`open_catalog_preview`)로 고객군/통화/거래일 기준 적용 결과를 확인한 뒤 견적서에서 `price_list_id` 를 선택한다.
6. 고객그룹 기본 가격표, 견적서, POS 프로필이 참조 중인 가격표는 삭제할 수 없으며 `ERR-SELL-044`가 반환된다.

### 판매 파트너 (Sales Partner)

#### 생성 및 운영 (Create & Operate)
1. **판매 (Selling) > 판매 파트너 (Sales Partner)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 파트너명, 영업 구역, 파트너 유형, 수수료율을 입력한다.
3. 고객 상세 또는 판매 파트너 화면에서 고객을 배정한다. 비활성 파트너에는 고객을 배정할 수 없으며 `ERR-SELL-041` 이 반환된다.
4. 판매 파트너 목록/상세에는 `summary`, `status_badge`, `recommended_action`, `available_actions` 가 함께 표시된다.
5. 고객이 다른 파트너로 재배정되어도 기존 판매주문/매출전표에 저장된 스냅샷 기준으로 historical 매출, 미수금, 예상 수수료가 유지된다.
6. 현재 연결 고객이 있거나 제출된 송장 이력이 있으면 삭제할 수 없고, 이 경우 `ERR-SELL-042` 또는 `ERR-SELL-044`가 반환된다.

### 판매 분석 (Sales Analytics)

#### 대시보드 및 차트 (Dashboard & Charts)
1. **판매 (Selling) > 판매 분석 (Sales Analytics)** 메뉴를 연다.
2. `group_by` 를 기간/고객/품목 중 하나로 선택해 랭킹 테이블을 바꾼다.
3. 상단 `summary` 카드에서 제출된 송장 수, 총 매출, 활성 고객 수, stale 견적 수를 확인한다.
4. `charts.sales_trend`, `charts.customer_mix`, `charts.item_mix`, `charts.quotation_pipeline` 으로 월별 추이, 고객/품목 기여도, 견적 파이프라인 상태를 한 번에 본다.
5. stale 견적이 남아 있으면 `recommended_action=review_stale_quotations` 가 표시되며, 고객 랭킹 상위 행은 `status_badge=top_customer` 와 함께 `open_customer`, `open_sales_invoices`, `review_margin` 액션을 제공한다.

### 견적서 (Quotation)

#### 생성 (Create)
1. **판매 (Selling) > 견적서 (Quotation)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 고객 (Customer)을 선택한다.
3. 품목 (Item)을 추가하고 수량 (Qty), 단가 (Rate)를 입력한다. 가격표 (Price List)에 따라 단가가 자동 적용된다.
4. 할인 (Discount), 세금 (Tax)이 자동 계산된다.
5. **"저장 (Save)"** 후 고객에게 견적서를 발송한다. (Save and send the quotation to the customer.)
6. 제출된 견적서에서만 **PDF 다운로드**, **메일 발송**, **고객 전자서명 링크**를 사용할 수 있다. 메일 발송 시 `portal_access_token`과 만료 시각이 함께 생성된다.
7. 제출된 견적서는 삭제할 수 없으며, 이력이 필요하면 **"취소 (Cancel)"** 로 상태만 종료한다.
8. 고객이 수락하면 **"판매주문으로 전환 (Convert to Sales Order)"** 을 클릭한다.

### 판매주문 (Sales Order)

#### 생성 (Create)
1. **판매 (Selling) > 판매주문 (Sales Order)** 메뉴에서 **"신규 (New)"** 를 클릭하거나, 견적서에서 전환한다. (Click "New" or convert from a Quotation.)
2. 납기일 (Delivery Date), 결제 조건 (Payment Terms)을 확인한다. 납기일은 거래일보다 빠를 수 없고, 품목은 최소 1건 이상이어야 한다.
3. **"제출 (Submit)"** 하면 판매주문이 확정된다. (Submit to confirm the Sales Order.)
4. 제출된 판매주문에서는 **"납품서 생성 (Create Delivery Note)"** 과 **"송장 생성 (Create Invoice)"** 버튼으로 후속 문서 초안을 바로 만든다.
5. 생성된 초안에는 고객/품목/수량/단가가 자동 복사되며, 판매주문 상세와 목록에는 **상태 배지 (Status Badge)** 와 **관련 문서 요약 (Downstream Summary)** 이 함께 표시된다.

### 납품서 (Delivery Note)

#### 생성 (Create)
1. 판매주문 (Sales Order)에서 **"납품서 생성 (Create Delivery Note)"** 을 클릭한다.
2. 제출된 판매주문 기준으로 고객, 품목, 수량, 단가가 미리 채워진 초안이 열린다.
3. 모든 납품 품목에 창고 (Warehouse)를 지정한 뒤 **"제출 (Submit)"** 한다. 창고가 비어 있으면 `ERR-SELL-050`으로 제출이 막힌다.
4. 제출 후 상세/목록에는 상태 배지 (`draft`/`submitted`/`cancelled`)와 후속 송장 요약 (`sales_invoice_count`)이 함께 표시되어, 출하 완료 후 청구 진행 상황을 즉시 확인할 수 있다.
5. 제출 시 재고가 차감된다. (Stock is deducted upon submission.)

### 매출 송장 (Sales Invoice)

#### 생성 (Create)
1. 판매주문 (Sales Order) 또는 납품서 (Delivery Note)에서 **"송장 생성 (Create Invoice)"** 을 클릭한다.
2. 판매주문 기준으로 생성한 초안이면 `sales_order_ref` 가 자동 연결되고 품목/단가가 그대로 복사된다.
3. 청구 금액 (Amount), 세금 (Tax), 결제기한 (Due Date)을 확인한다.
4. **"제출 (Submit)"** 하면 매출채권 (Accounts Receivable)이 생성되고 회계 분개 (Journal Entry)가 자동 처리된다.
5. 제출 시 `etax_invoice_ref` 가 비어 있으면 전자세금계산서 초안이 자동으로 연결된다.
6. 상세/목록에는 상태 배지 (`draft`/`submitted_unpaid`/`submitted_partial`/`submitted_paid`/`cancelled`), 수금 요약 (`grand_total`, `outstanding_amount`, `collected_amount`), 전자세금계산서 요약 (`transmission_status`, `nts_confirmation_no`)과 후속 액션 (`register_payment`, `open_accounts_receivable`, `open_etax_invoice`)이 함께 표시된다.

### 수금 처리 (Payment Entry)

#### 생성 (Create)
1. **판매 (Selling) > 결제 입력 (Payment Entry)** 에서 **"신규 (New)"** 를 클릭한다.
2. 고객 (Customer)과 결제 수단 (Payment Method: 계좌이체 Bank Transfer/카드 Card 등)을 선택한다.
3. 결제 금액 (Amount)을 입력하고 해당 송장 (Invoice)을 매칭한다.
4. **"제출 (Submit)"** 하면 매출채권 (AR)이 감소한다.

### 반품 처리 (Sales Return)

#### 생성 (Create)
1. **판매 (Selling) > 판매반품 (Sales Return)** 에서 **"신규 (New)"** 를 클릭한다.
2. 원래 판매주문 (Sales Order)/송장 (Invoice)을 선택한다.
3. 반품 품목 (Item)과 수량 (Qty), 사유 (Reason)를 입력한다.
4. **"제출 (Submit)"** 하면 재고가 복원되고 대변 메모 (Credit Note)가 생성된다.

### POS 거래 (POS Transaction)

1. **판매 (Selling) > POS 거래 (POS Transaction)** 에서 POS 세션 (Session)을 시작한다. (Start a POS session.)
2. 품목 (Item)을 스캔하거나 검색하여 추가한다. (Scan or search items to add.)
3. 결제 수단 (Payment Method)을 선택하고 결제를 완료한다. (Select payment method and complete payment.)
4. 영수증 (Receipt)이 자동 발행된다.
5. 영업 종료 후 **"POS 마감 (POS Closing)"** 에서 정산한다. (Settle at end of day via POS Closing.)

### 프로모션 및 쿠폰 (Promotion & Coupon)

1. **판매 (Selling) > 프로모션 (Promotion)** 에서 프로모션 규칙 (Promotion Rules)을 설정한다.
2. **판매 (Selling) > 쿠폰 코드 (Coupon Code)** 에서 쿠폰을 생성한다.
3. 판매주문 (Sales Order)/POS 거래 시 자동으로 할인 (Discount)이 적용된다.

## 관련 보고서 (Related Reports)

- 판매 분석 (Sales Analytics) — KPI 카드 + 월별 추이 + 고객/품목 믹스 + 견적 파이프라인 차트
- 영업 목표 대비 실적 (Sales Target vs. Actual)

## FAQ

- **Q: 견적서 (Quotation)의 유효기간이 지나면 어떻게 되나요?**
  A: 유효기간 만료 후에도 판매주문으로 전환할 수 있지만, 가격 재확인을 권장합니다. (You can still convert after expiry, but price re-verification is recommended.)

- **Q: 고객에게 보낼 PDF와 전자서명 링크는 어디서 확인하나요?**
  A: 제출된 견적서에서 메일 발송을 실행하면 `pdf_download_url`, `portal_sign_url`, `portal_access_token`, 만료 시각이 함께 생성됩니다. 고객이 링크에서 서명하면 견적서 상세의 서명 상태가 `signed` 로 갱신됩니다.

- **Q: 제출한 견적서를 삭제할 수 있나요?**
  A: 아닙니다. 제출된 견적서는 고객 전달/전자서명/주문 전환 이력을 보존해야 하므로 삭제 대신 취소(Cancel)만 허용됩니다.

- **Q: 부분 납품 (Partial Delivery)이 가능한가요?**
  A: 네, 판매주문 수량의 일부만 납품할 수 있습니다. 미납분은 추후 납품합니다. (Yes, you can deliver partial quantities. Remaining items can be delivered later.)
