# OneERP CRM 서비스 (CRM Service)

> 리드, 기회, 캠페인, 고객 서비스, SLA 등 고객 관계 관리를 담당하는 서비스 / Manages customer relationship management including leads, opportunities, campaigns, customer service, and SLA

## 도메인 개요 (Domain Overview)

CRM 서비스는 잠재고객 (Lead) 관리부터 영업 기회 (Opportunity) 추적, 마케팅 캠페인 (Marketing Campaign) — 이메일/SMS — 고객 이슈 (Issue) 관리, SLA 모니터링 (Service Level Agreement), 필드 서비스 (Field Service), 보증 클레임 (Warranty Claim), 지식베이스 (Knowledge Base), 설문조사 (Survey)까지 고객 관계 관리 전 영역을 담당한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8009 |

## 엔티티 (Entities) — 36개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Prospect | prospects | 잠재고객 (Prospect) |
| ServiceContract | service_contracts | 서비스계약 (Service Contract) |
| Survey | surveys | 설문조사 (Survey) |
| Faq | faqs | FAQ |
| KnowledgeArticle | knowledge_articles | 지식베이스문서 (Knowledge Article) |
| KnowledgeCategory | knowledge_categories | 지식분류 (Knowledge Category) |
| CustomerSegment | customer_segments | 고객세그먼트 (Customer Segment) |
| CompetitorProfile | competitor_profiles | 경쟁사프로필 (Competitor Profile) |
| ServiceTechnician | service_technicians | 서비스기사 (Service Technician) |
| WarrantyPeriod | warranty_periods | 보증기간 (Warranty Period) |
| MarketingList | marketing_lists | 마케팅리스트 (Marketing List) |
| MarketingAutomationRule | marketing_automation_rules | 마케팅자동화규칙 (Marketing Automation Rule) |
| TerritoryManagement | territory_managements | 영역관리 (Territory Management) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| ServiceOrder | service_orders | 서비스주문 (Service Order) |
| ServiceVisit | service_visits | 서비스방문 (Service Visit) |
| WarrantyClaim | warranty_claims | 보증클레임 (Warranty Claim) |
| EventRegistration | event_registrations | 이벤트등록 (Event Registration) |
| EmailCampaign | email_campaigns | 이메일캠페인 (Email Campaign) |
| SmsCampaign | sms_campaigns | SMS캠페인 (SMS Campaign) |
| Appointment | appointments | 약속/미팅 (Appointment) |
| Newsletter | newsletters | 뉴스레터 (Newsletter) |
| CallLog | call_logs | 통화기록 (Call Log) |
| LeadScoring | lead_scorings | 리드스코어링 (Lead Scoring) |
| LoyaltyPoint | loyalty_points | 로열티포인트 (Loyalty Point) |
| SurveyResponse | survey_responses | 설문응답 (Survey Response) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| PipelineService | 파이프라인 단계 관리, 전환 | 영업 파이프라인 관리 (Sales Pipeline) |
| CampaignService | 캠페인 생성, 실행, 성과 분석 | 마케팅 캠페인 관리 (Marketing Campaign) |
| SLAService | SLA 기준 설정, 위반 감지 | 서비스 수준 관리 (SLA Management) |
| FieldService | 현장 서비스 배정, 방문 관리 | 필드 서비스 관리 (Field Service Management) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 25개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/leads | 리드 관리 (Leads) |
| CRUD | /api/v1/opportunities | 영업 기회 관리 (Opportunities) |
| CRUD | /api/v1/issues | 고객 이슈 관리 (Issues) |
| CRUD | /api/v1/issue-types | 이슈 유형 관리 (Issue Types) |
| CRUD | /api/v1/activities | 활동 관리 (Activities) |
| CRUD | /api/v1/campaigns | 캠페인 관리 (Campaigns) |
| CRUD | /api/v1/sales-pipelines | 영업 파이프라인 (Sales Pipelines) |
| CRUD | /api/v1/service-level-agreements | SLA 관리 (Service Level Agreements) |
| CRUD | /api/v1/sla-fulfillments | SLA 이행 관리 (SLA Fulfillments) |
| CRUD | /api/v1/knowledge-bases | 지식베이스 관리 (Knowledge Bases) |
| CRUD | /api/v1/services | 서비스 관리 (Services) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-crm --directory services/crm uvicorn app.main:app --port 8009
```

## 테스트 (Testing)

```bash
uv run pytest services/crm/ -m "not integration and not e2e" -v
```
