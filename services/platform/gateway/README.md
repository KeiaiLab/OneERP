# OneERP Gateway 서비스 (Gateway Service)

> 인증, 전자결재, 시스템 설정 및 외부 연동을 관리하는 API 게이트웨이 / API gateway for authentication, e-approval, system settings, and external integrations

## 도메인 개요 (Domain Overview)

Gateway 서비스는 OneERP 시스템의 진입점 (Entry Point)으로, 사용자 인증/인가 (Authentication/Authorization), 전자결재 워크플로우 (Electronic Approval Workflow), 멀티테넌트 관리 (Multi-tenant Management), 시스템 설정 (System Settings)을 담당한다. 또한 외부 시스템 연동 (External Integration) — 국세청 (NTS), 보험 (Insurance), 배송 (Shipping), IoT — 과 ESG/컴플라이언스 (Compliance) 관리, 문서 관리 (Document Management) 등 공통 인프라 기능을 제공한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8001 |

## 엔티티 (Entities) — 61개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Address | addresses | 주소 (Address) |
| Contact | contacts | 연락처 (Contact) |
| IntegrationConnector | integration_connectors | 연동 커넥터 (Integration Connector) |
| WebhookEndpoint | webhook_endpoints | 웹훅 엔드포인트 (Webhook Endpoint) |
| PaymentGateway | payment_gateways | 결제 게이트웨이 (Payment Gateway) |
| BankFeed | bank_feeds | 은행 피드 (Bank Feed) |
| ShippingIntegration | shipping_integrations | 배송 연동 (Shipping Integration) |
| NTSIntegration | nts_integrations | 국세청 연동 (NTS Integration) |
| InsuranceIntegration | insurance_integrations | 보험 연동 (Insurance Integration) |
| DocumentCategory | document_categories | 문서 분류 (Document Category) |
| RetentionPolicy | retention_policies | 보존 정책 (Retention Policy) |
| InternalControl | internal_controls | 내부 통제 (Internal Control) |
| ContractTemplate | contract_templates | 계약 템플릿 (Contract Template) |
| BarcodeConfiguration | barcode_configurations | 바코드 설정 (Barcode Configuration) |
| CustomsTariff | customs_tariffs | 관세 정보 (Customs Tariff) |
| PortalUser | portal_users | 포털 사용자 (Portal User) |
| SupplierPortal | supplier_portals | 공급사 포털 (Supplier Portal) |
| CustomerPortal | customer_portals | 고객 포털 (Customer Portal) |
| IoTDevice | iot_devices | IoT 디바이스 (IoT Device) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Document | documents | 문서 관리 (Document Management) |
| ElectronicApprovalLog | electronic_approval_logs | 전자결재 로그 (E-Approval Log) |
| DigitalSignature | digital_signatures | 전자서명 (Digital Signature) |
| DocumentVersion | document_versions | 문서 버전 (Document Version) |
| ComplianceChecklist | compliance_checklists | 컴플라이언스 체크리스트 (Compliance Checklist) |
| RiskAssessment | risk_assessments | 리스크 평가 (Risk Assessment) |
| ComplianceReport | compliance_reports | 컴플라이언스 보고서 (Compliance Report) |
| Contract | contracts | 계약 (Contract) |
| ContractRenewal | contract_renewals | 계약 갱신 (Contract Renewal) |
| AuditTrail | audit_trails | 감사 추적 (Audit Trail) |
| RegulatorySandbox | regulatory_sandboxes | 규제 샌드박스 (Regulatory Sandbox) |
| DataPrivacyRecord | data_privacy_records | 개인정보 처리 기록 (Data Privacy Record) |
| IoTAlert | iot_alerts | IoT 경보 (IoT Alert) |
| IoTDataPoint | iot_data_points | IoT 데이터 포인트 (IoT Data Point) |
| CarbonEmission | carbon_emissions | 탄소 배출 (Carbon Emission) |
| ESGMetric | esg_metrics | ESG 지표 (ESG Metric) |
| ESGDisclosure | esg_disclosures | ESG 공시 (ESG Disclosure) |
| SustainabilityReport | sustainability_reports | 지속가능성 보고서 (Sustainability Report) |
| WasteManagement | waste_managements | 폐기물 관리 (Waste Management) |
| IntegrationLog | integration_logs | 연동 로그 (Integration Log) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| ApprovalService | 결재선 구성, 승인/반려 처리 | 전자결재 워크플로우 관리 (E-Approval Workflow) |
| ComplianceService | 컴플라이언스 체크, 보고서 생성 | 규정 준수 검증 (Compliance Verification) |
| DashboardService | 대시보드 데이터 집계 | 관리자 대시보드 (Admin Dashboard) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 39개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| POST | /api/v1/auth/* | 인증 (Authentication) |
| GET | /api/v1/me | 현재 사용자 정보 (Current User) |
| CRUD | /api/v1/admin/* | 관리자 기능 (Admin) |
| CRUD | /api/v1/approval-templates | 결재 템플릿 관리 (Approval Templates) |
| CRUD | /api/v1/approval-requests | 결재 요청 관리 (Approval Requests) |
| CRUD | /api/v1/approval-lines | 결재선 관리 (Approval Lines) |
| POST | /api/v1/approval-actions | 결재 승인/반려 (Approval Actions) |
| CRUD | /api/v1/delegation-rules | 결재 위임 규칙 (Delegation Rules) |
| CRUD | /api/v1/business-registrations | 사업자등록 관리 (Business Registrations) |
| CRUD | /api/v1/companies | 회사 관리 (Companies) |
| CRUD | /api/v1/currencies | 통화 관리 (Currencies) |
| CRUD | /api/v1/users | 사용자 관리 (Users) |
| CRUD | /api/v1/roles | 역할 관리 (Roles) |
| CRUD | /api/v1/role-permissions | 역할 권한 관리 (Role Permissions) |
| CRUD | /api/v1/workflow-definitions | 워크플로우 정의 (Workflow Definitions) |
| CRUD | /api/v1/workflow-rules | 워크플로우 규칙 (Workflow Rules) |
| CRUD | /api/v1/notification-templates | 알림 템플릿 (Notification Templates) |
| CRUD | /api/v1/notification-rules | 알림 규칙 (Notification Rules) |
| CRUD | /api/v1/naming-series | 채번 규칙 (Naming Series) |
| CRUD | /api/v1/system-settings | 시스템 설정 (System Settings) |
| CRUD | /api/v1/tenants | 테넌트 관리 (Tenants) |
| GET | /api/v1/dashboard | 대시보드 (Dashboard) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-gateway --directory services/gateway uvicorn app.main:app --port 8001
```

## 테스트 (Testing)

```bash
uv run pytest services/gateway/ -m "not integration and not e2e" -v
```
