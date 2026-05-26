# 제조 모듈 (Manufacturing Module)

## 개요 (Overview)

제조 모듈은 BOM 관리 (Bill of Materials), 공정 경로 (Routing), MRP 실행 (Material Requirements Planning), 생산계획 (Production Planning), 외주 가공 (Subcontracting), OEE 측정 (Overall Equipment Effectiveness), 설계 변경 관리 (Engineering Change Order) 등 제조 업무를 지원한다.

## 사전 조건 (Prerequisites)

- Manufacturing, Stock 서비스와 BOM/품목 마스터가 준비되어 있어야 한다.
- 작업지시와 생산실적 흐름을 볼 권한이 필요하다.
- 재고와 구매 연계를 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- BOM, MRP, 작업지시, 생산실적 흐름을 설명할 수 있다.
- 자재 출고와 완제품 입고의 연결 지점을 확인할 수 있다.
- 다음 프로젝트 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [프로젝트 모듈](./11-projects.md)

## 주요 기능 (Key Features)

- BOM (자재명세서, Bill of Materials)
- 공정 경로 (Routing)
- MRP (자재소요계획, Material Requirements Planning)
- 생산능력 계획 (Capacity Planning)
- 외주 가공 (Subcontracting)
- 설계 변경 (Engineering Change Order, ECO)
- OEE (설비종합효율, Overall Equipment Effectiveness)

## 업무 흐름 (Workflow)

```
BOM 생성       MRP 실행        작업지시 생성       생산 실행        완료
(BOM)     → (MRP Run)    → (Work Order)    → (Production)  → (Complete)
                ↓
        구매 요청 (Purchase Req.)
```

## 상세 기능 (Detailed Features)

### BOM (자재명세서, Bill of Materials)

#### 생성 (Create)
1. **재고 (Stock) > BOM** 에서 **"신규 (New)"** 를 클릭한다.
2. 완제품 (Finished Good)을 선택하고 구성 부품 (Component)과 소요량 (Qty)을 입력한다.
3. **"저장 (Save)"** 한다.

#### BOM 트리 (BOM Tree)
1. **제조 (Manufacturing) > BOM 트리 (BOM Tree)** 에서 다단계 BOM 구조 (Multi-level BOM)를 확인한다.
2. 반제품 (Sub-assembly)이 포함된 경우 하위 BOM까지 전개된다. (Explodes down to sub-assembly BOMs.)

#### BOM 개정 (BOM Revision)
1. 설계 변경 시 **제조 (Manufacturing) > BOM 개정 (BOM Revision)** 에서 변경 이력을 관리한다.
2. 이전 버전 (Previous Version)과의 차이를 비교할 수 있다.

### 공정 경로 (Routing)

1. **제조 (Manufacturing) > 공정 경로 (Routing)** 에서 제품별 제조 공정을 정의한다. (Define manufacturing processes per product.)
2. 공정 순서 (Operation Sequence), 작업장 (Workstation), 표준 시간 (Standard Time)을 설정한다.
3. 작업지시 (Work Order) 생성 시 공정 경로가 자동 적용된다.

### MRP (자재소요계획, Material Requirements Planning)

#### MRP 실행 (Run MRP)
1. **제조 (Manufacturing) > MRP 실행 (MRP Run)** 에서 **"신규 (New)"** 를 클릭한다.
2. 대상 기간 (Planning Period), 품목 범위 (Item Range)를 설정한다.
3. **"MRP 실행 (Run MRP)"** 을 클릭한다.
4. 시스템이 수요 예측 (Demand Forecast), 현재 재고 (Current Stock), BOM을 기반으로 자재 소요량 (Material Requirements)을 계산한다.
5. 결과로 구매 요청 (Purchase Request), 생산 주문 (Production Order)이 제안된다.

#### 수요 예측 (Demand Forecast)
1. **제조 (Manufacturing) > 수요 예측 (Demand Forecast)** 에서 제품별 수요를 예측한다.
2. 과거 판매 데이터 (Historical Sales Data)와 수동 입력 (Manual Input)을 조합한다.

### 생산 계획 (Production Planning)

#### 생산능력 계획 (Capacity Planning)
1. **제조 (Manufacturing) > 생산능력 계획 (Capacity Planning)** 에서 작업장별 가용 능력 (Available Capacity)을 확인한다.
2. 부하율 (Load Factor)을 분석하여 병목 공정 (Bottleneck)을 파악한다.

#### 공급 계획 (Supply Plan)
1. **제조 (Manufacturing) > 공급 계획 (Supply Plan)** 에서 MRP 결과를 기반으로 공급 일정 (Supply Schedule)을 수립한다.

### 외주 가공 (Subcontracting)

#### 생성 (Create)
1. **제조 (Manufacturing) > 외주 가공 주문 (Subcontracting Order)** 에서 **"신규 (New)"** 를 클릭한다.
2. 외주 업체 (Subcontractor), 가공 품목 (Item), 수량 (Qty)을 입력한다.
3. 원자재 지급 (Raw Material Supply) 여부를 설정한다.
4. **"제출 (Submit)"** 하면 외주 발주가 진행된다.

### 설계 변경 (Engineering Change Order, ECO)

1. **제조 (Manufacturing) > 설계 변경 지시 (ECO)** 에서 **"신규 (New)"** 를 클릭한다.
2. 변경 대상 BOM/제품 (Target BOM/Product), 변경 사유 (Reason)를 입력한다.
3. 관련 설계 문서 (Design Documents)를 첨부한다.
4. 승인 (Approval) 후 BOM이 자동 갱신된다.

### 생산 실적 분석 (Production Performance Analysis)

#### OEE (설비종합효율, Overall Equipment Effectiveness)
1. **제조 (Manufacturing) > OEE 지표 (OEE Metrics)** 에서 설비별 가동률 (Availability)/성능률 (Performance)/양품률 (Quality Rate)을 확인한다.
2. 가동률 (Availability) = 가동시간 (Operating Time) / 부하시간 (Loading Time)
3. OEE = 가동률 (Availability) x 성능률 (Performance) x 양품률 (Quality)

#### 생산 차이 분석 (Production Variance Analysis)
1. **제조 (Manufacturing) > 생산 차이 분석 (Production Variance)** 에서 계획 (Plan) 대비 실적 (Actual)을 비교한다.
2. 수량 차이 (Quantity Variance), 능률 차이 (Efficiency Variance), 가격 차이 (Price Variance)를 분석한다.

#### 비가동 관리 (Downtime Management)
1. **제조 (Manufacturing) > 비가동 기록 (Downtime Record)** 에서 설비 정지 시간 (Downtime)과 원인 (Cause)을 기록한다.
2. 비가동 원인별 통계를 분석하여 개선 과제를 도출한다. (Analyze downtime causes to identify improvement opportunities.)

## 관련 보고서 (Related Reports)

- BOM 원가 분석 (BOM Cost Analysis)
- MRP 소요량 보고서 (MRP Requirements Report)
- OEE 트렌드 (OEE Trend)
- 생산 실적 보고서 (Production Performance Report)

## FAQ

- **Q: 다단계 BOM (Multi-level BOM)이란 무엇인가요?**
  A: 완제품을 만들기 위한 반제품(Sub-assembly)의 BOM까지 계층적으로 구성된 자재명세서입니다. (A hierarchical BOM that includes sub-assembly BOMs needed to build the finished product.)

- **Q: MRP 실행 (MRP Run) 주기는 어떻게 설정하나요?**
  A: 일반적으로 주간 또는 일간으로 실행하며, 수요 변동에 따라 조정합니다. (Typically run weekly or daily, adjusted based on demand variability.)
