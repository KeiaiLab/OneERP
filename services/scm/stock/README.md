# OneERP Stock 서비스 (Stock Service)

> 품목, 창고, 재고 입출고, BOM, 생산계획, WMS를 관리하는 재고/물류 서비스 / Manages items, warehouses, stock entries, BOM, production planning, and WMS

## 도메인 개요 (Domain Overview)

Stock 서비스는 품목 마스터 관리 (Item Master), 창고/적치 위치 관리 (Warehouse/Bin Location), 재고 입출고 (Stock Entry), 재고 실사 (Stock Reconciliation), BOM/작업지시/생산계획 (BOM/Work Order/Production Plan), 시리얼번호/배치 추적 (Serial No./Batch Tracking), 피킹/패킹/출하 (Pick/Pack/Ship) 등 재고 및 물류 전반을 담당한다. 재고 원장 (Stock Ledger)을 통해 실시간 재고 수량을 추적한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8004 |

## 엔티티 (Entities) — 40개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| BinLocation | bin_locations | 적치 위치 (Bin Location) |
| PutawayRule | putaway_rules | 적치 규칙 (Putaway Rule) |
| Carrier | carriers | 운송사 (Carrier) |
| Route | routes | 운송 경로 (Route) |
| SafetyStockRule | safety_stock_rules | 안전재고 규칙 (Safety Stock Rule) |
| UomConversion | uom_conversions | 단위 변환 (UoM Conversion) |
| ItemAttribute | item_attributes | 품목 속성 (Item Attribute) |
| HazardousMaterial | hazardous_materials | 위험물 (Hazardous Material) |
| FreightCost | freight_costs | 화물 운송비 (Freight Cost) |
| ReorderLevel | reorder_levels | 리오더 규칙 (Reorder Level) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| WavePicking | wave_pickings | 웨이브 피킹 (Wave Picking) |
| Shipment | shipments | 출하 (Shipment) |
| TrackingUpdate | tracking_updates | 배송 추적 업데이트 (Tracking Update) |
| SerialBatchBundle | serial_batch_bundles | 시리얼/배치 번들 (Serial/Batch Bundle) |
| CycleCount | cycle_counts | 순환 재고 조사 (Cycle Count) |
| InventoryCountSheet | inventory_count_sheets | 재고 실사 시트 (Inventory Count Sheet) |
| ScrapEntry | scrap_entries | 폐기 처리 (Scrap Entry) |
| LandedCostVoucherTMS | landed_cost_voucher_tms | 운송비 배부 (Landed Cost Voucher TMS) |
| AtpCheck | atp_checks | ATP 조회 (Available-to-Promise Check) |

### 시스템 원장 (System Ledger)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| StockLedgerEntry | stock_ledger_entries | 재고 원장 (Stock Ledger Entry) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| StockLedgerService | 원장 기록, 잔고 계산 | 재고 원장 관리 (Stock Ledger Management) |
| StockReservationService | 예약/해제 | 재고 예약 관리 (Stock Reservation) |
| WMSService | 입고/피킹/적치 제어 | 창고 관리 시스템 (Warehouse Management System) |
| PickPackService | 피킹/패킹 지시 생성 | 출하 프로세스 (Pick & Pack Process) |
| ItemVariantService | 변형 품목 생성 | 품목 변형 관리 (Item Variant Management) |
| ReceiptHandler | 입고 처리, 품질 검사 연동 | 입고 워크플로우 (Receipt Workflow) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 20개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/items | 품목 관리 (Items) |
| CRUD | /api/v1/item-groups | 품목 그룹 관리 (Item Groups) |
| CRUD | /api/v1/item-variants | 품목 변형 관리 (Item Variants) |
| CRUD | /api/v1/item-prices | 품목 가격 관리 (Item Prices) |
| CRUD | /api/v1/warehouses | 창고 관리 (Warehouses) |
| CRUD | /api/v1/stock-entries | 재고 입출고 (Stock Entries) |
| CRUD | /api/v1/stock-balances | 재고 잔고 조회 (Stock Balances) |
| CRUD | /api/v1/stock-reconciliations | 재고 조정 (Stock Reconciliations) |
| CRUD | /api/v1/batches | 배치 관리 (Batches) |
| CRUD | /api/v1/serial-nos | 시리얼번호 관리 (Serial Numbers) |
| CRUD | /api/v1/boms | BOM 관리 (BOMs) |
| CRUD | /api/v1/work-orders | 작업지시 관리 (Work Orders) |
| CRUD | /api/v1/production-plans | 생산계획 관리 (Production Plans) |
| CRUD | /api/v1/job-cards | 작업카드 관리 (Job Cards) |
| CRUD | /api/v1/workstations | 작업장 관리 (Workstations) |
| CRUD | /api/v1/operations | 공정 관리 (Operations) |
| CRUD | /api/v1/production-costs | 생산원가 관리 (Production Costs) |
| CRUD | /api/v1/pick-lists | 피킹 리스트 (Pick Lists) |
| CRUD | /api/v1/packing-slips | 패킹 슬립 (Packing Slips) |

## 이벤트 (Events)

### 구독 (Subscribed)
| EventType | 핸들러 (Handler) |
|-----------|-----------------|
| 재고 관련 이벤트 (Stock Events) | events/handlers.py |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-stock --directory services/stock uvicorn app.main:app --port 8004
```

## 테스트 (Testing)

```bash
uv run pytest services/stock/ -m "not integration and not e2e" -v
```
