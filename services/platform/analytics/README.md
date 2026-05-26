# OneERP Analytics 서비스 (Analytics Service)

> 대시보드, KPI, 커스텀 보고서 등 비즈니스 분석을 담당하는 서비스 / Manages business intelligence including dashboards, KPIs, and custom reports

## 도메인 개요 (Domain Overview)

Analytics 서비스는 경영진 대시보드 (Executive Dashboard), KPI 정의/스냅샷 (KPI Definition/Snapshot) 관리, 커스텀 보고서 (Custom Report) 작성, 대시보드 위젯 (Dashboard Widget) 구성, 데이터 소스 (Data Source) 연결 등 비즈니스 인텔리전스 (Business Intelligence) 기능을 제공한다. 각 도메인 서비스의 데이터를 수집/집계하여 경영 의사결정을 지원한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8014 |

## 엔티티 (Entities) — 6개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Dashboard | dashboards | 대시보드 (Dashboard) |
| KPIDefinition | kpi_definitions | KPI 정의 (KPI Definition) |
| DataSource | data_sources | 데이터 소스 (Data Source) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| CustomReport | custom_reports | 커스텀 보고서 (Custom Report) |
| DashboardWidget | dashboard_widgets | 대시보드 위젯 (Dashboard Widget) |
| KPISnapshot | kpi_snapshots | KPI 스냅샷 (KPI Snapshot) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| DataAggregationService | 데이터 수집, 집계, 캐싱 | 데이터 집계 엔진 (Data Aggregation Engine) |
| KPIEngineService | KPI 계산, 임계값 판정 | KPI 계산 엔진 (KPI Engine) |
| ReportBuilderService | 보고서 생성, 필터 적용 | 보고서 빌더 (Report Builder) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 6개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-analytics --directory services/analytics uvicorn app.main:app --port 8014
```

## 테스트 (Testing)

```bash
uv run pytest services/analytics/ -m "not integration and not e2e" -v
```
