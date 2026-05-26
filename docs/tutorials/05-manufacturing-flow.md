# 튜토리얼: Manufacturing Flow (BOM→MRP→생산) / Tutorial: Manufacturing Flow

## 개요 (Overview)

BOM(Bill of Materials) 등록에서 MRP 실행, 작업지시 (Work Order) 생성,
자재 출고, 생산실적 보고, 완제품 입고까지의 전체 제조 흐름을 단계별로 실습한다.
이 시나리오는 Manufacturing, Stock 서비스를 횡단하며,
BOM 전개 (Explosion)와 MRP 기반 자동 발주/작업지시 생성을 보여준다.

This tutorial walks through the complete manufacturing flow — from BOM registration
through MRP execution, Work Order creation, material issuance,
production reporting, to finished goods receipt.

## 사전 조건 (Prerequisites)

- Manufacturing, Stock 서비스가 로컬에서 기동되어 있어야 한다.
- 원자재와 완제품 품목, 창고 재고가 준비되어 있어야 한다.
- BOM과 MRP 결과를 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- BOM, MRP, 작업지시, 생산실적 흐름이 완료된다.
- 자재 소요와 생산 결과를 확인할 수 있다.
- 다음 자산 생애주기 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [자산 생애주기 튜토리얼](./06-asset-lifecycle.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Manufacturing (포트 8009 / Port 8009)
uv run --package oneerp-manufacturing --directory services/manufacturing \
    uvicorn app.main:app --port 8009 --reload

# Stock (포트 8004 / Port 8004)
uv run --package oneerp-stock --directory services/stock \
    uvicorn app.main:app --port 8004 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

### 기초 데이터 생성 (Create Base Data)

#### 원자재 등록 (Register Raw Materials)

```bash
# 원자재 A (Raw Material A)
curl -s -X POST http://localhost:8004/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "RM-STEEL",
    "item_name": "강판",
    "item_group": "원자재",
    "stock_uom": "KG",
    "standard_rate": 3000,
    "valuation_method": "moving_average"
  }' | jq

# 원자재 B (Raw Material B)
curl -s -X POST http://localhost:8004/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "RM-BOLT",
    "item_name": "볼트 M10",
    "item_group": "원자재",
    "stock_uom": "EA",
    "standard_rate": 500,
    "valuation_method": "moving_average"
  }' | jq
```

#### 완제품 등록 (Register Finished Good)

```bash
curl -s -X POST http://localhost:8004/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "FG-BRACKET",
    "item_name": "브래킷 조립체",
    "item_group": "완제품",
    "stock_uom": "EA",
    "standard_rate": 25000,
    "valuation_method": "moving_average"
  }' | jq
```

#### 원자재 재고 확보 (Stock Raw Materials)

```bash
curl -s -X POST http://localhost:8004/api/v1/stock-entries \
  -H "Content-Type: application/json" \
  -d '{
    "stock_entry_type": "Material Receipt",
    "items": [
      {"item_code": "RM-STEEL", "qty": 500, "target_warehouse": "WH-001", "basic_rate": 3000},
      {"item_code": "RM-BOLT", "qty": 2000, "target_warehouse": "WH-001", "basic_rate": 500}
    ]
  }' | jq
# 입고전표 제출 (Submit)
curl -s -X POST http://localhost:8004/api/v1/stock-entries/STE-0001/submit | jq
```

---

## Step 1: BOM 등록 (Register BOM)

완제품 (Finished Good)의 자재명세서 (Bill of Materials)를 등록한다.
브래킷 1EA 생산에 강판 2KG + 볼트 4EA가 필요하다.

Register the Bill of Materials for the finished good.
One bracket requires 2KG of steel plate + 4 bolts.

```bash
curl -s -X POST http://localhost:8009/api/v1/boms \
  -H "Content-Type: application/json" \
  -d '{
    "item_code": "FG-BRACKET",
    "bom_name": "브래킷 조립체 BOM",
    "quantity": 1,
    "items": [
      {"item_code": "RM-STEEL", "qty": 2, "uom": "KG", "unit_price": 3000},
      {"item_code": "RM-BOLT", "qty": 4, "uom": "EA", "unit_price": 500}
    ]
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "BOM-0001",
  "item_code": "FG-BRACKET",
  "bom_name": "브래킷 조립체 BOM"
}
```

### BOM 원가 확인 (Verify BOM Cost)

`BOMExplosionService.calculate_cost()` — BOM 전개 후 단가를 곱하여 총원가를 산출한다.

```bash
curl -s "http://localhost:8009/api/v1/boms/BOM-0001/cost?qty=1" | jq
```

**기대 결과 (Expected):** 강판 2KG x 3,000 + 볼트 4EA x 500 = **8,000원/EA**

---

## Step 2: 수요예측 + MRP 실행 (Demand Forecast + Run MRP)

수요예측 (Demand Forecast)을 등록하고 MRP를 실행한다.
`MRPService.run_mrp()` — 수요예측 기반으로 BOM 전개 -> 재고 확인 -> 부족분 산출.

```bash
# 수요예측 생성 (Create demand forecast)
curl -s -X POST http://localhost:8009/api/v1/demand-forecasts \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_name": "2026년 4월 수요",
    "period": "2026-04",
    "items": [
      {"item_code": "FG-BRACKET", "qty": 100}
    ]
  }' | jq

# MRP 실행 (Run MRP)
curl -s -X POST http://localhost:8009/api/v1/mrp/run \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_id": "FCST-0001"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "mrp_id": "MRP-0001",
  "forecast_id": "FCST-0001",
  "purchase_request_count": 0,
  "work_order_count": 1,
  "work_orders": [
    {"item_code": "FG-BRACKET", "qty": 100, "bom_id": "BOM-0001", "type": "manufacture"}
  ]
}
```

MRP 로직:
- BOM이 있는 품목 (FG-BRACKET) → 작업지시 (Work Order) 생성 추천
- BOM이 없는 품목 → 구매요청 (Purchase Request) 생성 추천
- 현재 재고가 충분하면 부족분 = 0 → 생성 불필요

---

## Step 3: 작업지시 생성 (Create Work Order)

`WorkOrderService.create_work_order()` — BOM 조회 후 작업지시를 생성한다.
필요 자재를 BOM 수량 x 생산 수량으로 자동 계산한다.

```bash
curl -s -X POST http://localhost:8009/api/v1/work-orders \
  -H "Content-Type: application/json" \
  -d '{
    "bom_id": "BOM-0001",
    "qty": 100,
    "planned_start": "2026-04-01"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "WO-0001",
  "bom_id": "BOM-0001",
  "item_code": "FG-BRACKET",
  "planned_qty": 100,
  "produced_qty": 0,
  "status": "draft",
  "required_materials": [
    {"item_code": "RM-STEEL", "required_qty": 200, "uom": "KG"},
    {"item_code": "RM-BOLT", "required_qty": 400, "uom": "EA"}
  ]
}
```

필요 자재가 BOM x 생산 수량으로 자동 계산된다:
- 강판: 2KG x 100 = 200KG
- 볼트: 4EA x 100 = 400EA

---

## Step 4: 자재 출고 (Issue Materials)

`WorkOrderService.issue_materials()` — 작업지시에 필요한 자재를 재고에서 차감한다.
재고 부족 시 `ValueError`가 발생한다.

```bash
curl -s -X POST http://localhost:8009/api/v1/work-orders/WO-0001/issue-materials | jq
```

### 기대 결과 (Expected Result)

```json
{
  "work_order_id": "WO-0001",
  "issued_items": [
    {"item_code": "RM-STEEL", "issued_qty": 200},
    {"item_code": "RM-BOLT", "issued_qty": 400}
  ]
}
```

작업지시 상태가 `in_progress`로 변경된다.

### 재고 확인 (Verify Stock)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=RM-STEEL" | jq
# 강판 (Steel): 500 - 200 = 300KG 잔량 (remaining)
```

---

## Step 5: 생산실적 보고 (Report Production)

`WorkOrderService.report_production()` — 생산 수량과 공정 손실 (Process Loss)을 보고한다.
부산물 (By-product)도 기록할 수 있다.

```bash
curl -s -X POST http://localhost:8009/api/v1/work-orders/WO-0001/report-production \
  -H "Content-Type: application/json" \
  -d '{
    "produced_qty": 98,
    "process_loss_qty": 2,
    "by_products": [
      {"item_code": "SCRAP-STEEL", "qty": 5}
    ]
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "work_order_id": "WO-0001",
  "produced_qty": 98,
  "process_loss_qty": 2,
  "by_product_count": 1
}
```

---

## Step 6: 작업지시 완료 — 완제품 입고 (Complete Work Order — Receive Finished Goods)

`WorkOrderService.complete_work_order()` — 작업지시를 완료하고 완제품을 재고에 입고한다.
생산 수량이 0이면 완료할 수 없다.

```bash
curl -s -X POST http://localhost:8009/api/v1/work-orders/WO-0001/complete | jq
```

### 기대 결과 (Expected Result)

```json
{
  "work_order_id": "WO-0001",
  "item_code": "FG-BRACKET",
  "produced_qty": 98,
  "status": "completed"
}
```

### 완제품 재고 확인 (Verify Finished Goods Stock)

```bash
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=FG-BRACKET" | jq
# 기대값 (Expected): 98EA
```

---

## 검증 (Verification)

### 1. 작업지시 진행률 확인 (Check Work Order Progress)

`ProductionTrackingService.get_progress()` — 진행률을 계산한다.

```bash
curl -s "http://localhost:8009/api/v1/work-orders/WO-0001/progress" | jq
# 기대값 (Expected): progress_pct = 98.0 (98/100 * 100)
```

### 2. 차이 분석 (Variance Analysis)

`ProductionTrackingService.analyze_variance()` — 계획 대비 실적 차이를 분석한다.

```bash
curl -s "http://localhost:8009/api/v1/work-orders/WO-0001/variance" | jq
# 기대값 (Expected): variance = -2, variance_percentage = -2.0%
```

### 3. 재고 잔량 확인 (Verify Stock Balances)

```bash
# 원자재 (Raw Materials)
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=RM-STEEL" | jq
# 강판 300KG (500 - 200)

curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=RM-BOLT" | jq
# 볼트 1600EA (2000 - 400)

# 완제품 (Finished Goods)
curl -s "http://localhost:8004/api/v1/stock-ledgers?item_code=FG-BRACKET" | jq
# 브래킷 98EA
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Manufacturing]                              [Stock]
    |                                          |
  1. BOM 등록                                  |
     Register BOM                              |
    |                                          |
  2. 수요예측 + MRP 실행                        |
     Forecast + Run MRP                        |
     -> BOM 전개 (Explosion)                    |
     -> 재고 확인 -> 부족분 산출                 |
    |                                          |
  3. 작업지시 생성 (Draft)                      |
     Create Work Order                         |
     -> 필요 자재 자동 계산                      |
    |                                          |
  4. 자재 출고 ---------------------------->  재고 차감
     Issue Materials                          Deduct Stock
     -> status: in_progress                    |
    |                                          |
  5. 생산실적 보고                              |
     Report Production                         |
     -> 부산물/공정손실 기록                     |
    |                                          |
  6. 작업지시 완료 -------------------------> 완제품 입고
     Complete Work Order                      Receive FG
     -> status: completed                      |
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- BOM (Bill of Materials) 등록과 원가 계산 (Cost Calculation)
- MRP (Material Requirements Planning) 실행 — 수요예측 -> BOM 전개 -> 재고 확인 -> 부족분 산출
- MRP 의사결정: BOM 존재 여부로 제조 (Manufacture) vs 구매 (Purchase) 판별
- 작업지시 (Work Order) 생애주기: Draft -> In Progress -> Completed
- 자재 출고 (Material Issue), 생산실적 (Production Report), 완제품 입고 (FG Receipt) 흐름
- 차이 분석 (Variance Analysis) — 계획 대비 실적 비교
