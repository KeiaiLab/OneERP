# 재고 모듈 (Stock/Inventory Module)

## 개요 (Overview)

재고 모듈은 품목 마스터 (Item Master), 창고 관리 (Warehouse Management), 재고 입출고 (Stock Entry), 시리얼/배치 추적 (Serial/Batch Tracking), 재고 실사 (Stock Reconciliation) 등 재고 및 물류 업무를 관리한다.

## 사전 조건 (Prerequisites)

- Stock 서비스와 품목/창고 마스터가 준비되어 있어야 한다.
- 입출고와 재고 조정을 볼 권한이 필요하다.
- 구매/판매 모듈과의 연계를 확인할 수 있어야 한다.

## 완료 조건 (Completion Criteria)

- 재고 입고, 출고, 이동, 조정 흐름을 설명할 수 있다.
- 품목별 재고 잔량과 평가 방식을 확인할 수 있다.
- 다음 인사 모듈 문서로 이동할 수 있다.

## 다음 단계 (Next Step)

- [인사 모듈](./05-hr.md)

## 주요 기능 (Key Features)

- 품목 관리 (Item Management)
- 창고 관리 (Warehouse Management)
- 재고 입출고 (Stock Entry: Receipt/Delivery/Transfer)
- 재고 잔고 조회 (Stock Balance Inquiry)
- 재고 조정 (Stock Reconciliation)
- 시리얼번호/배치 관리 (Serial Number/Batch Management)
- 로트/배치 추적 (Lot/Batch Tracking)
- 이동평균 평가 (Moving Average Valuation)

## 업무 흐름 (Workflow)

```
품목 등록       입고           재고 관리        출고
(Item Reg.) → (Receipt)  → (Inventory Mgmt) → (Delivery)
                                ↕
                         재고 조정 (Stock Reconciliation)
```

## 상세 기능 (Detailed Features)

### 품목 관리 (Item Management)

#### 생성 (Create)
1. **재고 (Stock) > 품목 (Item)** 메뉴에서 **"신규 (New)"** 를 클릭한다.
2. 품목 코드 (Item Code)를 직접 입력하거나 자동 채번을 사용하고, 품목명 (Item Name), 품목 그룹 (Item Group)을 입력한다.
3. 단위 (UOM, Unit of Measure), 기본 창고 (Default Warehouse)를 설정한다.
4. 시리얼 추적 (Serial Tracking), 배치 추적 (Batch Tracking) 여부를 선택한다.
5. 재주문점 (Reorder Level)을 설정한다.
6. **"저장 (Save)"** 을 클릭한다.

#### 워크벤치 요약 (Workbench Summary)
1. 품목 목록은 상태 배지 (`reorder_due`, `tracking_required`, `variant_template`, `inventory_ready`)와 함께 재고 요약, 변형 수, 가격 수를 한 줄로 보여준다.
2. 품목 상세의 요약 패널에서 현재고, 최근 재고 이동일, 최저/최고 가격, 변형 품목 수를 확인할 수 있다.
3. 품목에 변형/가격/재고 이력이 연결되어 있으면 삭제 대신 **"재고현황 보기 (View Stock Balance)"**, **"원장 보기 (Open Stock Ledger)"** 액션으로 유도된다.

#### 품목 변형 (Item Variant)
1. 품목 상세에서 **"변형 관리 (Manage Variants)"** 를 클릭한다.
2. 속성 (Attribute: 색상 Color, 크기 Size 등)을 정의한다.
3. 속성 조합별 변형 품목이 자동 생성된다. (Variant items are auto-generated for each attribute combination.)

### 창고 관리 (Warehouse Management)

#### 생성 (Create)
1. **재고 (Stock) > 창고 (Warehouse)** 에서 창고를 등록한다.
2. 창고명 (Warehouse Name), 위치 (Location), 관리자 (Manager)를 입력한다.
3. 적치 위치 (Bin Location)를 설정하여 세밀한 위치 관리가 가능하다. (Set bin locations for granular location tracking.)

### 재고 입출고 (Stock Entry)

#### 입고 (Material Receipt)
1. **재고 (Stock) > 재고 입출고 (Stock Entry)** 에서 **"신규 (New)"** 를 클릭한다.
2. 유형을 **"입고 (Material Receipt)"** 로 선택한다.
3. 대상 창고 (Target Warehouse), 품목 (Item), 수량 (Qty)을 입력한다.
4. **"제출 (Submit)"** 하면 재고가 증가한다. (Stock increases upon submission.)

#### 출고 (Material Issue)
1. 유형을 **"출고 (Material Issue)"** 로 선택한다.
2. 출고 창고 (Source Warehouse), 품목 (Item), 수량 (Qty)을 입력한다.
3. **"제출 (Submit)"** 하면 재고가 감소한다. (Stock decreases upon submission.)

#### 창고 간 이전 (Material Transfer)
1. 유형을 **"이전 (Material Transfer)"** 으로 선택한다.
2. 출발 창고 (Source Warehouse)와 도착 창고 (Target Warehouse)를 선택한다.
3. 이전할 품목 (Item)과 수량 (Qty)을 입력한다.
4. **"제출 (Submit)"** 하면 재고가 이동한다. (Stock is transferred between warehouses.)

### 재고 잔고 조회 (Stock Balance)

1. **재고 (Stock) > 재고 잔고 (Stock Balance)** 에서 현재 재고 현황을 조회한다.
2. 창고별 (Warehouse), 품목별 (Item)로 필터링할 수 있다.
3. 예약 수량 (Reserved Qty), 가용 수량 (Available Qty)을 확인한다.

### 재고 조정 (Stock Reconciliation)

#### 생성 (Create)
1. **재고 (Stock) > 재고 조정 (Stock Reconciliation)** 에서 **"신규 (New)"** 를 클릭한다.
2. 대상 창고 (Warehouse)와 품목 (Item)을 선택한다.
3. 실사 수량 (Physical Count)을 입력한다.
4. 시스템 수량 (System Qty)과의 차이가 자동 계산된다. (Difference from system quantity is auto-calculated.)
5. **"제출 (Submit)"** 하면 차이분만큼 재고가 조정된다.

### 시리얼번호/배치 관리 (Serial Number / Batch Management)

#### 시리얼번호 (Serial Number)
1. 시리얼 추적이 설정된 품목은 입고 시 시리얼번호를 등록한다. (Register serial numbers during receipt for serial-tracked items.)
2. **재고 (Stock) > 시리얼번호 (Serial Number)** 에서 시리얼번호별 이력을 추적한다.

#### 배치 관리 (Batch Management)
1. 배치 추적이 설정된 품목은 입고 시 배치 번호 (Batch No.)를 부여한다.
2. 유효기간 (Expiry Date), 제조일자 (Manufacturing Date)를 입력한다.
3. **재고 (Stock) > 배치 (Batch)** 에서 배치별 재고와 이력을 관리한다.

## 관련 보고서 (Related Reports)

- 재고 잔고 보고서 (Stock Balance Report)
- 재고 원장 (Stock Ledger)
- 품목별 가격 이력 (Item Price History)
- 재주문 보고서 (Reorder Report)

## FAQ

- **Q: 이동평균 평가 (Moving Average Valuation)란 무엇인가요?**
  A: 입고 시마다 평균 단가가 재계산되는 재고 평가 방법입니다. (A valuation method where the average cost is recalculated with each receipt.)

- **Q: 재고 조정 (Stock Reconciliation)은 언제 하나요?**
  A: 정기 실사 또는 시스템 수량과 실물 수량에 차이가 발생했을 때 진행합니다. (During periodic physical counts or when discrepancies are found.)
