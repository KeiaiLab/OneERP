# 튜토리얼: CRM Pipeline (영업 파이프라인) / Tutorial: CRM Pipeline

## 개요 (Overview)

리드 (Lead) 등록에서 기회 (Opportunity) 전환, 견적 (Quotation) 생성,
수주 확정 (Won), SLA 관리까지의 전체 영업 파이프라인 흐름을 단계별로 실습한다.
이 시나리오는 CRM 서비스의 `PipelineService`와 `SLAService`를 활용한다.

This tutorial covers the full CRM Pipeline flow — from lead registration
through opportunity conversion, quotation creation, deal closure,
and SLA management.

## 사전 조건 (Prerequisites)

- CRM, Selling 서비스가 로컬에서 기동되어 있어야 한다.
- 고객과 견적 마스터가 준비되어 있어야 한다.
- 리드 전환과 수주 흐름을 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 리드, 기회, 견적, 수주, SLA 흐름이 완료된다.
- 다음 관리자 설정 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [관리자 설정 튜토리얼](./10-admin-setup.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# CRM (포트 8013 / Port 8013)
uv run --package oneerp-crm --directory services/crm \
    uvicorn app.main:app --port 8013 --reload

# Selling (포트 8002 / Port 8002) — 수주 확정 시 판매주문 연계
uv run --package oneerp-selling --directory services/selling \
    uvicorn app.main:app --port 8002 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

---

## Step 1: 리드 등록 (Register Lead)

잠재 고객을 리드로 등록한다.

```bash
curl -s -X POST http://localhost:8013/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{
    "lead_name": "ABC 전자",
    "company_name": "ABC전자 주식회사",
    "email": "kim@abc-electronics.co.kr",
    "phone": "02-1234-5678",
    "source": "웹사이트 문의",
    "interested_item": "AI CRM",
    "lead_score": 88
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "id": "LEAD-0001",
  "message": "리드가 생성되었습니다"
}
```

### Step 1-1: 리드 워크벤치 점검 (Inspect Lead Workbench)

```bash
curl -s "http://localhost:8013/api/v1/leads?status=qualified&score_grade=hot" | jq
curl -s "http://localhost:8013/api/v1/leads/LEAD-0001/summary" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "summary": {
    "qualified_count": 1,
    "high_score_count": 1,
    "stale_follow_up_count": 0
  },
  "data": [
    {
      "_id": "LEAD-0001",
      "status_badge": "qualified_hot",
      "recommended_action": "convert_to_opportunity"
    }
  ]
}
```

```json
{
  "lead_name": "ABC 전자",
  "score_summary": {
    "lead_score": 88.0,
    "score_grade": "hot"
  },
  "activity_summary": {
    "activity_count": 0
  },
  "conversion_summary": {
    "can_convert_to_opportunity": false
  }
}
```

---

## Step 2: 리드 → 기회 전환 (Convert Lead to Opportunity)

`PipelineService.convert_lead_to_opportunity()` — 리드를 기회로 전환한다.
리드 상태가 `converted`로 변경되고 새로운 Opportunity가 생성된다.

```bash
curl -s -X POST http://localhost:8013/api/v1/leads/LEAD-0001/convert \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_type": "sales",
    "expected_amount": 50000000,
    "probability": 30,
    "close_date": "2026-06-30"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "lead_id": "LEAD-0001",
  "opportunity_id": "OPP-0001",
  "status": "open"
}
```

이미 전환된 리드를 다시 전환하면 에러가 발생한다.

---

## Step 3: 기회 → 견적 전환 (Convert Opportunity to Quotation)

`PipelineService.convert_opportunity_to_quotation()` — 기회를 견적으로 전환한다.
기회 상태가 `quotation`으로 변경되고 Quotation 문서가 생성된다.

```bash
curl -s -X POST http://localhost:8013/api/v1/opportunities/OPP-0001/quotation \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-0001",
    "items": [
      {"item_code": "ITEM-A", "qty": 100, "rate": 15000, "amount": 1500000},
      {"item_code": "ITEM-B", "qty": 50, "rate": 30000, "amount": 1500000}
    ],
    "valid_till": "2026-05-31"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "opportunity_id": "OPP-0001",
  "quotation_id": "QTN-0001"
}
```

### 단계 전환 규칙 (Stage Transition Rules)

유효한 전환만 허용된다:
- `open` -> `quotation`, `won`, `lost`
- `quotation` -> `won`, `lost`
- 이외의 전환은 `ValueError` 발생

---

## Step 4: 수주 확정 (Mark as Won)

`PipelineService.mark_won()` — 기회를 성사(Won)로 표시한다.

```bash
curl -s -X POST http://localhost:8013/api/v1/opportunities/OPP-0001/won | jq
```

### 기대 결과 (Expected Result)

```json
{
  "opportunity_id": "OPP-0001",
  "previous_stage": "quotation",
  "new_stage": "won"
}
```

수주 확정 후 Selling 서비스에서 판매주문 (Sales Order)을 생성하여 O2C 흐름으로 이어진다.

### 실패 처리 (Mark as Lost)

`PipelineService.mark_lost()` — 실패 사유와 경쟁사를 기록할 수 있다.

```bash
curl -s -X POST http://localhost:8013/api/v1/opportunities/OPP-0002/lost \
  -H "Content-Type: application/json" \
  -d '{
    "lost_reason": "가격 경쟁력 부족",
    "competitor": "XYZ솔루션"
  }' | jq
```

---

## Step 5: 파이프라인 현황 조회 (View Pipeline Summary)

`PipelineService.get_pipeline_summary()` — 단계별 건수 + 금액을 집계한다.

```bash
curl -s "http://localhost:8013/api/v1/pipeline/summary" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "stages": [
    {"stage": "open", "count": 0, "total_amount": 0},
    {"stage": "quotation", "count": 0, "total_amount": 0},
    {"stage": "won", "count": 1, "total_amount": 50000000},
    {"stage": "lost", "count": 0, "total_amount": 0}
  ]
}
```

---

## Step 6: 전환율 확인 (Check Conversion Metrics)

`PipelineService.get_conversion_metrics()` — 리드→기회, 기회→성사 전환율을 계산한다.

```bash
curl -s "http://localhost:8013/api/v1/pipeline/metrics" | jq
```

### 기대 결과 (Expected Result)

```json
{
  "total_leads": 1,
  "converted_leads": 1,
  "lead_to_opportunity_rate": 100.0,
  "total_opportunities": 1,
  "won_opportunities": 1,
  "opportunity_to_won_rate": 100.0
}
```

---

## Step 7: SLA 관리 (SLA Management)

### SLA 정의 (Define SLA)

고객 이슈에 대한 응답/해결 시간 SLA를 정의한다.

```bash
curl -s -X POST http://localhost:8013/api/v1/service-level-agreements \
  -H "Content-Type: application/json" \
  -d '{
    "sla_name": "일반 이슈 SLA",
    "entity_type": "issue",
    "priority": "medium",
    "resolution_time": 24,
    "is_active": true
  }' | jq
```

### 이슈 등록 + SLA 평가 (Create Issue + Evaluate SLA)

```bash
# 이슈 등록 (Create issue)
curl -s -X POST http://localhost:8013/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "주문 배송 지연 문의",
    "customer": "CUST-0001",
    "priority": "medium",
    "status": "open"
  }' | jq
# 응답 (Response): {"_id": "ISS-0001", ...}

# SLA 평가 (Evaluate SLA)
curl -s -X POST http://localhost:8013/api/v1/sla/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "ISS-0001",
    "entity_type": "issue"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "entity_id": "ISS-0001",
  "matched": true,
  "sla_id": "SLA-0001",
  "is_fulfilled": true,
  "elapsed_hours": 0.5,
  "fulfillment_id": "SLAF-0001"
}
```

### SLA 위반 조회 (Check SLA Violations)

`SLAService.check_violations()` — 미해결 이슈 중 SLA 위반 건을 조회한다.

```bash
curl -s "http://localhost:8013/api/v1/sla/violations" | jq
```

### SLA 이행률 (SLA Fulfillment Rate)

```bash
curl -s "http://localhost:8013/api/v1/sla/fulfillment-rate" | jq
```

```json
{
  "total": 1,
  "fulfilled": 1,
  "breached": 0,
  "fulfillment_rate": 100.0
}
```

---

## 검증 (Verification)

### 1. 리드 상태 확인 (Verify Lead Status)

```bash
curl -s "http://localhost:8013/api/v1/leads/LEAD-0001" | jq '.status'
# 기대값 (Expected): "converted"
```

### 2. 기회 상태 확인 (Verify Opportunity Status)

```bash
curl -s "http://localhost:8013/api/v1/opportunities/OPP-0001" | jq '.status'
# 기대값 (Expected): "won"
```

### 3. 파이프라인 금액 확인 (Verify Pipeline Amount)

```bash
curl -s "http://localhost:8013/api/v1/pipeline/summary" | jq '.stages[] | select(.stage=="won") | .total_amount'
# 기대값 (Expected): 50000000
```

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[CRM]                                      [Selling]
    |                                           |
  1. 리드 등록 (Lead)                            |
     Register Lead                              |
    |                                           |
  2. 리드 -> 기회 전환                            |
     Convert Lead to Opportunity                |
     status: open                               |
    |                                           |
  3. 기회 -> 견적 전환                            |
     Convert to Quotation                       |
     status: quotation                          |
    |                                           |
  4. 수주 확정 (Won) ----------------------->  판매주문 생성
     Mark Won                                   Create Sales Order
     status: won                                -> O2C 흐름으로 연계
    |                                           |
  5. 파이프라인 현황 조회                         |
     Pipeline Summary                           |
    |                                           |
  6. 전환율 확인                                 |
     Conversion Metrics                         |
    |                                           |
  7. SLA 관리                                   |
     SLA Evaluation / Violations                |
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 영업 파이프라인 (Pipeline) 흐름: 리드 (Lead) -> 기회 (Opportunity) -> 견적 (Quotation) -> 수주 (Won)
- 단계 전환 규칙 (Stage Transition Rules) — 유효한 전환만 허용
- 실패 처리 (Lost) — 실패 사유, 경쟁사 기록
- 파이프라인 집계 (Pipeline Summary) — 단계별 건수 + 금액
- 전환율 (Conversion Metrics) — 리드→기회, 기회→성사 비율
- SLA 관리 — 매칭, 이행 여부 판정, 위반 조회, 이행률 계산, 에스컬레이션
