# OneERP Manufacturing 서비스 (Manufacturing Service)

> BOM, 공정 경로, MRP, 생산계획, 설계 변경 등 제조 관리를 담당하는 서비스 / Manages manufacturing including BOM, routing, MRP, production planning, and engineering changes

## 도메인 개요 (Domain Overview)

Manufacturing 서비스는 BOM (Bill of Materials) 관리, 공정 경로 (Routing) 설계, MRP (Material Requirements Planning) 실행, 수요 예측 (Demand Forecast), 공급/생산능력 계획 (Supply/Capacity Planning), 외주 가공 (Subcontracting), 공정 손실/부산물 (Process Loss/By-Product) 관리, OEE (Overall Equipment Effectiveness) 측정, 설계 변경 관리 (ECO: Engineering Change Order), 생산 차이 분석 (Production Variance Analysis) 등 제조 업무 전반을 담당한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8013 |

## 엔티티 (Entities) — 15개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Routing | routings | 공정 경로 (Routing) |
| BOMRevision | bom_revisions | BOM 개정 (BOM Revision) |
| BOMTree | bom_trees | BOM 트리 (BOM Tree) |
| EngineeringDocument | engineering_documents | 설계 문서 (Engineering Document) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| DemandForecast | demand_forecasts | 수요 예측 (Demand Forecast) |
| SupplyPlan | supply_plans | 공급 계획 (Supply Plan) |
| CapacityPlan | capacity_plans | 생산능력 계획 (Capacity Plan) |
| MRPRun | mrp_runs | MRP 실행 (MRP Run) |
| SubcontractingOrder | subcontracting_orders | 외주 가공 주문 (Subcontracting Order) |
| ProcessLoss | process_losses | 공정 손실 (Process Loss) |
| ByProduct | by_products | 부산물 (By-Product) |
| DowntimeEntry | downtime_entries | 비가동 기록 (Downtime Entry) |
| OeeMetric | oee_metrics | OEE 지표 (OEE Metric) |
| EngineeringChangeOrder | engineering_change_orders | 설계 변경 지시 (Engineering Change Order) |
| ProductionVarianceAnalysis | production_variance_analyses | 생산 차이 분석 (Production Variance Analysis) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| BomExplosionService | BOM 전개, 자재 소요량 계산 | BOM 전개 엔진 (BOM Explosion Engine) |
| MRPService | MRP 실행, 계획 주문 생성 | 자재 소요량 계획 (Material Requirements Planning) |
| CapacityPlanningService | 부하 계산, 병목 분석 | 생산능력 계획 (Capacity Planning) |
| WorkOrderService | 작업지시 생성, 진행 관리 | 생산 실행 관리 (Production Execution) |
| ProductionTrackingService | 생산 실적 추적, 실적 대비 분석 | 생산 추적 (Production Tracking) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 15개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-manufacturing --directory services/manufacturing uvicorn app.main:app --port 8013
```

## 테스트 (Testing)

```bash
uv run pytest services/manufacturing/ -m "not integration and not e2e" -v
```
