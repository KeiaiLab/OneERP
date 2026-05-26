# OneERP Assets 서비스 (Assets Service)

> 자산 등록, 감가상각, 유지보수, 차량 관리 등 고정자산 관리를 담당하는 서비스 / Manages fixed assets including asset registration, depreciation, maintenance, and fleet management

## 도메인 개요 (Domain Overview)

Assets 서비스는 고정자산 (Fixed Asset) 등록/분류, 감가상각 (Depreciation) 계산 — 정액법/정률법 (Straight-Line/Declining Balance) 등 — 자산 이동/처분/재평가/손상 (Movement/Disposal/Revaluation/Impairment), 유지보수 (Maintenance) 계획/실행, 차량 관리 (Fleet Management) — 배정/운행일지/연료/유지보수 — 등 기업 자산 관리 전반을 담당한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8010 |

## 엔티티 (Entities) — 24개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Vehicle | vehicles | 차량 (Vehicle) |
| AssetInsurance | asset_insurances | 자산보험 (Asset Insurance) |
| MaintenanceSchedule | maintenance_schedules | 유지보수일정 (Maintenance Schedule) |
| AssetMaintenancePlan | asset_maintenance_plans | 자산유지보수계획 (Asset Maintenance Plan) |
| SparePart | spare_parts | 예비부품 (Spare Part) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| AssetRepair | asset_repairs | 자산수리 (Asset Repair) |
| AssetValueAdjustment | asset_value_adjustments | 자산가치조정 (Asset Value Adjustment) |
| AssetRevaluation | asset_revaluations | 자산재평가 (Asset Revaluation) |
| AssetImpairment | asset_impairments | 자산손상 (Asset Impairment) |
| MaintenanceRequest | maintenance_requests | 유지보수요청 (Maintenance Request) |
| MaintenanceVisit | maintenance_visits | 유지보수방문 (Maintenance Visit) |
| VehicleAssignment | vehicle_assignments | 차량배정 (Vehicle Assignment) |
| VehicleMaintenance | vehicle_maintenances | 차량유지보수 (Vehicle Maintenance) |
| MaintenanceLog | maintenance_logs | 유지보수로그 (Maintenance Log) |
| EquipmentDowntime | equipment_downtimes | 장비비가동 (Equipment Downtime) |
| DepreciationComparison | depreciation_comparisons | 감가상각비교 (Depreciation Comparison) |
| VehicleLog | vehicle_logs | 차량운행일지 (Vehicle Log) |
| FuelEntry | fuel_entries | 연료입력 (Fuel Entry) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| AssetLifecycleService | 자산 등록, 이동, 처분 | 자산 수명주기 관리 (Asset Lifecycle Management) |
| DepreciationService | 감가상각 계산, 일괄 처리 | 감가상각 엔진 (Depreciation Engine) |
| FleetService | 차량 배정, 운행 관리, 비용 분석 | 차량 관리 (Fleet Management) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 18개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/assets | 자산 관리 (Assets) |
| CRUD | /api/v1/asset-categories | 자산 분류 관리 (Asset Categories) |
| CRUD | /api/v1/asset-disposals | 자산 처분 관리 (Asset Disposals) |
| CRUD | /api/v1/asset-movements | 자산 이동 관리 (Asset Movements) |
| CRUD | /api/v1/asset-audits | 자산 실사 관리 (Asset Audits) |
| CRUD | /api/v1/depreciation-entries | 감가상각 분개 (Depreciation Entries) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-assets --directory services/assets uvicorn app.main:app --port 8010
```

## 테스트 (Testing)

```bash
uv run pytest services/assets/ -m "not integration and not e2e" -v
```
