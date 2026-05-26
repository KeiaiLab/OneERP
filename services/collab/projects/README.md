# OneERP Projects 서비스 (Projects Service)

> 프로젝트, 태스크, 타임시트, 원가, 수익인식 등 프로젝트 관리를 담당하는 서비스 / Manages projects, tasks, timesheets, cost tracking, and revenue recognition

## 도메인 개요 (Domain Overview)

Projects 서비스는 프로젝트 (Project) 생성/관리, 태스크 분해 (Task Decomposition/WBS), 마일스톤 (Milestone) 추적, 타임시트 (Timesheet) 기록, 자원 할당 (Resource Allocation), 프로젝트 원가 관리 (Project Cost Management), 프로젝트별 수익 인식 (Revenue Recognition), 프로젝트 청구 (Project Billing), 리스크 관리 (Risk Management) 등 프로젝트 기반 업무 전반을 담당한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8011 |

## 엔티티 (Entities) — 12개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ProjectTemplate | project_templates | 프로젝트템플릿 (Project Template) |
| TaskTemplate | task_templates | 태스크템플릿 (Task Template) |
| WbsElement | wbs_elements | WBS요소 (WBS Element) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ResourceAllocation | resource_allocations | 자원할당 (Resource Allocation) |
| ProjectBilling | project_billings | 프로젝트청구 (Project Billing) |
| ProjectRisk | project_risks | 프로젝트리스크 (Project Risk) |
| ProjectRevenueRecognition | project_revenue_recognitions | 프로젝트수익인식 (Project Revenue Recognition) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| ProjectCostService | 프로젝트 원가 집계, 분석 | 프로젝트별 원가 관리 (Project Cost Management) |
| ProjectBillingService | 청구서 생성, 마일스톤 기반 청구 | 프로젝트 청구 관리 (Project Billing) |
| RevenueRecognitionService | 수익 인식 일정 생성 | 프로젝트 수익 인식 (Revenue Recognition) |
| TimesheetService | 타임시트 기록, 집계 | 시간 기록 관리 (Timesheet Management) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 7개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/projects | 프로젝트 관리 (Projects) |
| CRUD | /api/v1/tasks | 태스크 관리 (Tasks) |
| CRUD | /api/v1/timesheets | 타임시트 관리 (Timesheets) |
| CRUD | /api/v1/milestones | 마일스톤 관리 (Milestones) |
| CRUD | /api/v1/activity-types | 활동유형 관리 (Activity Types) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-projects --directory services/projects uvicorn app.main:app --port 8011
```

## 테스트 (Testing)

```bash
uv run pytest services/projects/ -m "not integration and not e2e" -v
```
