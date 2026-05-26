"""Gateway 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

26개 엔티티를 EntityMeta로 선언한다.
인증/전자결재/Setup 등 커스텀 로직이 있는 엔티티는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.address import Address, AddressCreate, AddressUpdate
from .models.audit_trail import AuditTrail, AuditTrailCreate, AuditTrailUpdate
from .models.bank_feed import BankFeed, BankFeedCreate, BankFeedUpdate
from .models.barcode_configuration import (
    BarcodeConfiguration,
    BarcodeConfigurationCreate,
    BarcodeConfigurationUpdate,
)
from .models.contact import Contact, ContactCreate, ContactUpdate
from .models.contract_template import (
    ContractTemplate,
    ContractTemplateCreate,
    ContractTemplateUpdate,
)
from .models.customer_portal import (
    CustomerPortal,
    CustomerPortalCreate,
    CustomerPortalUpdate,
)
from .models.customs_tariff import (
    CustomsTariff,
    CustomsTariffCreate,
    CustomsTariffUpdate,
)
from .models.data_privacy_record import (
    DataPrivacyRecord,
    DataPrivacyRecordCreate,
    DataPrivacyRecordUpdate,
)
from .models.digital_signature import (
    DigitalSignature,
    DigitalSignatureCreate,
    DigitalSignatureUpdate,
)
from .models.document import Document, DocumentCreate, DocumentUpdate
from .models.document_category import (
    DocumentCategory,
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
)
from .models.document_version import (
    DocumentVersion,
    DocumentVersionCreate,
    DocumentVersionUpdate,
)
from .models.electronic_approval_log import (
    ElectronicApprovalLog,
    ElectronicApprovalLogCreate,
    ElectronicApprovalLogUpdate,
)
from .models.insurance_integration import (
    InsuranceIntegration,
    InsuranceIntegrationCreate,
    InsuranceIntegrationUpdate,
)
from .models.integration_connector import (
    IntegrationConnector,
    IntegrationConnectorCreate,
    IntegrationConnectorUpdate,
)
from .models.integration_log import (
    IntegrationLog,
    IntegrationLogCreate,
    IntegrationLogUpdate,
)
from .models.nts_integration import (
    NTSIntegration,
    NTSIntegrationCreate,
    NTSIntegrationUpdate,
)
from .models.payment_gateway import (
    PaymentGateway,
    PaymentGatewayCreate,
    PaymentGatewayUpdate,
)
from .models.portal_user import PortalUser, PortalUserCreate, PortalUserUpdate
from .models.retention_policy import (
    RetentionPolicy,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)
from .models.shipping_integration import (
    ShippingIntegration,
    ShippingIntegrationCreate,
    ShippingIntegrationUpdate,
)
from .models.supplier_portal import (
    SupplierPortal,
    SupplierPortalCreate,
    SupplierPortalUpdate,
)
from .models.webhook_endpoint import (
    WebhookEndpoint,
    WebhookEndpointCreate,
    WebhookEndpointUpdate,
)

# --- 마스터 데이터 ---

ADDRESS = EntityMeta(
    collection="addresses",
    prefix="ADDR",
    api_path="/api/v1/addresses",
    tag="주소",
    resource="address",
    model=Address,
    create_schema=AddressCreate,
    update_schema=AddressUpdate,
    archetype="master",
    not_found_message="주소를 찾을 수 없습니다",
)

CONTACT = EntityMeta(
    collection="contacts",
    prefix="CONT",
    api_path="/api/v1/contacts",
    tag="연락처",
    resource="contact",
    model=Contact,
    create_schema=ContactCreate,
    update_schema=ContactUpdate,
    archetype="master",
    not_found_message="연락처를 찾을 수 없습니다",
)

INTEGRATION_CONNECTOR = EntityMeta(
    collection="integration_connectors",
    prefix="ICON",
    api_path="/api/v1/integration-connectors",
    tag="연동 커넥터",
    resource="integration_connector",
    model=IntegrationConnector,
    create_schema=IntegrationConnectorCreate,
    update_schema=IntegrationConnectorUpdate,
    archetype="master",
    not_found_message="연동 커넥터를 찾을 수 없습니다",
)

WEBHOOK_ENDPOINT = EntityMeta(
    collection="webhook_endpoints",
    prefix="WHEP",
    api_path="/api/v1/webhook-endpoints",
    tag="웹훅 엔드포인트",
    resource="webhook_endpoint",
    model=WebhookEndpoint,
    create_schema=WebhookEndpointCreate,
    update_schema=WebhookEndpointUpdate,
    archetype="master",
    not_found_message="웹훅 엔드포인트를 찾을 수 없습니다",
)

PAYMENT_GATEWAY = EntityMeta(
    collection="payment_gateways",
    prefix="PGWY",
    api_path="/api/v1/payment-gateways",
    tag="결제 게이트웨이",
    resource="payment_gateway",
    model=PaymentGateway,
    create_schema=PaymentGatewayCreate,
    update_schema=PaymentGatewayUpdate,
    archetype="master",
    not_found_message="결제 게이트웨이를 찾을 수 없습니다",
)

BANK_FEED = EntityMeta(
    collection="bank_feeds",
    prefix="BFED",
    api_path="/api/v1/bank-feeds",
    tag="은행 피드",
    resource="bank_feed",
    model=BankFeed,
    create_schema=BankFeedCreate,
    update_schema=BankFeedUpdate,
    archetype="master",
    not_found_message="은행 피드를 찾을 수 없습니다",
)

SHIPPING_INTEGRATION = EntityMeta(
    collection="shipping_integrations",
    prefix="SHPI",
    api_path="/api/v1/shipping-integrations",
    tag="배송 연동",
    resource="shipping_integration",
    model=ShippingIntegration,
    create_schema=ShippingIntegrationCreate,
    update_schema=ShippingIntegrationUpdate,
    archetype="master",
    not_found_message="배송 연동을 찾을 수 없습니다",
)

NTS_INTEGRATION = EntityMeta(
    collection="nts_integrations",
    prefix="NTS",
    api_path="/api/v1/nts-integrations",
    tag="국세청 연동",
    resource="nts_integration",
    model=NTSIntegration,
    create_schema=NTSIntegrationCreate,
    update_schema=NTSIntegrationUpdate,
    archetype="master",
    not_found_message="국세청 연동을 찾을 수 없습니다",
)

INSURANCE_INTEGRATION = EntityMeta(
    collection="insurance_integrations",
    prefix="INSI",
    api_path="/api/v1/insurance-integrations",
    tag="보험 연동",
    resource="insurance_integration",
    model=InsuranceIntegration,
    create_schema=InsuranceIntegrationCreate,
    update_schema=InsuranceIntegrationUpdate,
    archetype="master",
    not_found_message="보험 연동을 찾을 수 없습니다",
)

DOCUMENT_CATEGORY = EntityMeta(
    collection="document_categories",
    prefix="DCAT",
    api_path="/api/v1/document-categories",
    tag="문서 분류",
    resource="document_category",
    model=DocumentCategory,
    create_schema=DocumentCategoryCreate,
    update_schema=DocumentCategoryUpdate,
    archetype="master",
    not_found_message="문서 분류를 찾을 수 없습니다",
)

RETENTION_POLICY = EntityMeta(
    collection="retention_policies",
    prefix="RETP",
    api_path="/api/v1/retention-policies",
    tag="보존 정책",
    resource="retention_policy",
    model=RetentionPolicy,
    create_schema=RetentionPolicyCreate,
    update_schema=RetentionPolicyUpdate,
    archetype="master",
    not_found_message="보존 정책을 찾을 수 없습니다",
)

CONTRACT_TEMPLATE = EntityMeta(
    collection="contract_templates",
    prefix="CTPL",
    api_path="/api/v1/contract-templates",
    tag="계약 템플릿",
    resource="contract_template",
    model=ContractTemplate,
    create_schema=ContractTemplateCreate,
    update_schema=ContractTemplateUpdate,
    archetype="master",
    not_found_message="계약 템플릿을 찾을 수 없습니다",
)

BARCODE_CONFIGURATION = EntityMeta(
    collection="barcode_configurations",
    prefix="BCFG",
    api_path="/api/v1/barcode-configurations",
    tag="바코드 설정",
    resource="barcode_configuration",
    model=BarcodeConfiguration,
    create_schema=BarcodeConfigurationCreate,
    update_schema=BarcodeConfigurationUpdate,
    archetype="master",
    not_found_message="바코드 설정을 찾을 수 없습니다",
)

CUSTOMS_TARIFF = EntityMeta(
    collection="customs_tariffs",
    prefix="CTAR",
    api_path="/api/v1/customs-tariffs",
    tag="관세 정보",
    resource="customs_tariff",
    model=CustomsTariff,
    create_schema=CustomsTariffCreate,
    update_schema=CustomsTariffUpdate,
    archetype="master",
    not_found_message="관세 정보를 찾을 수 없습니다",
)

PORTAL_USER = EntityMeta(
    collection="portal_users",
    prefix="PUSR",
    api_path="/api/v1/portal-users",
    tag="포털 사용자",
    resource="portal_user",
    model=PortalUser,
    create_schema=PortalUserCreate,
    update_schema=PortalUserUpdate,
    archetype="master",
    not_found_message="포털 사용자를 찾을 수 없습니다",
)

SUPPLIER_PORTAL = EntityMeta(
    collection="supplier_portals",
    prefix="SPRT",
    api_path="/api/v1/supplier-portals",
    tag="공급사 포털",
    resource="supplier_portal",
    model=SupplierPortal,
    create_schema=SupplierPortalCreate,
    update_schema=SupplierPortalUpdate,
    archetype="master",
    not_found_message="공급사 포털을 찾을 수 없습니다",
)

CUSTOMER_PORTAL = EntityMeta(
    collection="customer_portals",
    prefix="CPRT",
    api_path="/api/v1/customer-portals",
    tag="고객 포털",
    resource="customer_portal",
    model=CustomerPortal,
    create_schema=CustomerPortalCreate,
    update_schema=CustomerPortalUpdate,
    archetype="master",
    not_found_message="고객 포털을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

DOCUMENT = EntityMeta(
    collection="documents",
    prefix="DOC",
    api_path="/api/v1/documents",
    tag="문서 관리",
    resource="document",
    model=Document,
    create_schema=DocumentCreate,
    update_schema=DocumentUpdate,
    archetype="transaction",
    not_found_message="문서를 찾을 수 없습니다",
)

ELECTRONIC_APPROVAL_LOG = EntityMeta(
    collection="electronic_approval_logs",
    prefix="EALG",
    api_path="/api/v1/electronic-approval-logs",
    tag="전자결재 로그",
    resource="electronic_approval_log",
    model=ElectronicApprovalLog,
    create_schema=ElectronicApprovalLogCreate,
    update_schema=ElectronicApprovalLogUpdate,
    archetype="transaction",
    not_found_message="전자결재 로그를 찾을 수 없습니다",
)

DIGITAL_SIGNATURE = EntityMeta(
    collection="digital_signatures",
    prefix="DSIG",
    api_path="/api/v1/digital-signatures",
    tag="전자서명",
    resource="digital_signature",
    model=DigitalSignature,
    create_schema=DigitalSignatureCreate,
    update_schema=DigitalSignatureUpdate,
    archetype="transaction",
    not_found_message="전자서명을 찾을 수 없습니다",
)

DOCUMENT_VERSION = EntityMeta(
    collection="document_versions",
    prefix="DVER",
    api_path="/api/v1/document-versions",
    tag="문서 버전",
    resource="document_version",
    model=DocumentVersion,
    create_schema=DocumentVersionCreate,
    update_schema=DocumentVersionUpdate,
    archetype="transaction",
    not_found_message="문서 버전을 찾을 수 없습니다",
)

AUDIT_TRAIL = EntityMeta(
    collection="audit_trails",
    prefix="ATRAIL",
    api_path="/api/v1/audit-trails",
    tag="감사 추적",
    resource="audit_trail",
    model=AuditTrail,
    create_schema=AuditTrailCreate,
    update_schema=AuditTrailUpdate,
    archetype="transaction",
    not_found_message="감사 추적을 찾을 수 없습니다",
)

DATA_PRIVACY_RECORD = EntityMeta(
    collection="data_privacy_records",
    prefix="DPR",
    api_path="/api/v1/data-privacy-records",
    tag="개인정보 처리 기록",
    resource="data_privacy_record",
    model=DataPrivacyRecord,
    create_schema=DataPrivacyRecordCreate,
    update_schema=DataPrivacyRecordUpdate,
    archetype="transaction",
    not_found_message="개인정보 처리 기록을 찾을 수 없습니다",
)

INTEGRATION_LOG = EntityMeta(
    collection="integration_logs",
    prefix="ILOG",
    api_path="/api/v1/integration-logs",
    tag="연동 로그",
    resource="integration_log",
    model=IntegrationLog,
    create_schema=IntegrationLogCreate,
    update_schema=IntegrationLogUpdate,
    archetype="transaction",
    not_found_message="연동 로그를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    ADDRESS,
    CONTACT,
    INTEGRATION_CONNECTOR,
    WEBHOOK_ENDPOINT,
    PAYMENT_GATEWAY,
    BANK_FEED,
    SHIPPING_INTEGRATION,
    NTS_INTEGRATION,
    INSURANCE_INTEGRATION,
    DOCUMENT_CATEGORY,
    CONTRACT_TEMPLATE,
    BARCODE_CONFIGURATION,
    CUSTOMS_TARIFF,
    PORTAL_USER,
    SUPPLIER_PORTAL,
    CUSTOMER_PORTAL,
    # 트랜잭션
    DOCUMENT,
    ELECTRONIC_APPROVAL_LOG,
    DIGITAL_SIGNATURE,
    DOCUMENT_VERSION,
    AUDIT_TRAIL,
    DATA_PRIVACY_RECORD,
    INTEGRATION_LOG,
]
