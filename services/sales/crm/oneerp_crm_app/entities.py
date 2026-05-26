"""CRM 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

27개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티(리드, 기회, 이슈 등)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from .models.call_log import CallLog, CallLogCreate, CallLogUpdate
from .models.competitor_profile import (
    CompetitorProfile,
    CompetitorProfileCreate,
    CompetitorProfileUpdate,
)
from .models.contract_renewal import (
    ContractRenewal,
    ContractRenewalCreate,
    ContractRenewalUpdate,
)
from .models.customer_segment import (
    CustomerSegment,
    CustomerSegmentCreate,
    CustomerSegmentUpdate,
)
from .models.email_campaign import (
    EmailCampaign,
    EmailCampaignCreate,
    EmailCampaignUpdate,
)
from .models.event_registration import (
    EventRegistration,
    EventRegistrationCreate,
    EventRegistrationUpdate,
)
from .models.faq import Faq, FaqCreate, FaqUpdate
from .models.general_contract import Contract, ContractCreate, ContractUpdate
from .models.knowledge_article import (
    KnowledgeArticle,
    KnowledgeArticleCreate,
    KnowledgeArticleUpdate,
)
from .models.knowledge_category import (
    KnowledgeCategory,
    KnowledgeCategoryCreate,
    KnowledgeCategoryUpdate,
)
from .models.lead_scoring import LeadScoring, LeadScoringCreate, LeadScoringUpdate
from .models.loyalty_point import LoyaltyPoint, LoyaltyPointCreate, LoyaltyPointUpdate
from .models.marketing_automation_rule import (
    MarketingAutomationRule,
    MarketingAutomationRuleCreate,
    MarketingAutomationRuleUpdate,
)
from .models.marketing_list import (
    MarketingList,
    MarketingListCreate,
    MarketingListUpdate,
)
from .models.newsletter import Newsletter, NewsletterCreate, NewsletterUpdate
from .models.prospect import Prospect, ProspectCreate, ProspectUpdate
from .models.service_contract import (
    ServiceContract,
    ServiceContractCreate,
    ServiceContractUpdate,
)
from .models.service_order import ServiceOrder, ServiceOrderCreate, ServiceOrderUpdate
from .models.service_technician import (
    ServiceTechnician,
    ServiceTechnicianCreate,
    ServiceTechnicianUpdate,
)
from .models.service_visit import ServiceVisit, ServiceVisitCreate, ServiceVisitUpdate
from .models.sms_campaign import SmsCampaign, SmsCampaignCreate, SmsCampaignUpdate
from .models.survey import Survey, SurveyCreate, SurveyUpdate
from .models.survey_response import (
    SurveyResponse,
    SurveyResponseCreate,
    SurveyResponseUpdate,
)
from .models.territory_management import (
    TerritoryManagement,
    TerritoryManagementCreate,
    TerritoryManagementUpdate,
)
from .models.warranty_claim import (
    WarrantyClaim,
    WarrantyClaimCreate,
    WarrantyClaimUpdate,
)
from .models.warranty_period import (
    WarrantyPeriod,
    WarrantyPeriodCreate,
    WarrantyPeriodUpdate,
)

# --- 마스터 데이터 ---

PROSPECT = EntityMeta(
    collection="prospects",
    prefix="PRSP",
    api_path="/api/v1/prospects",
    tag="잠재고객",
    resource="prospect",
    model=Prospect,
    create_schema=ProspectCreate,
    update_schema=ProspectUpdate,
    archetype="master",
    not_found_message="잠재 고객을 찾을 수 없습니다",
)

SERVICE_CONTRACT = EntityMeta(
    collection="service_contracts",
    prefix="SCTR",
    api_path="/api/v1/service-contracts",
    tag="서비스계약",
    resource="service_contract",
    model=ServiceContract,
    create_schema=ServiceContractCreate,
    update_schema=ServiceContractUpdate,
    archetype="master",
    not_found_message="서비스 계약을 찾을 수 없습니다",
)

SURVEY = EntityMeta(
    collection="surveys",
    prefix="SURV",
    api_path="/api/v1/surveys",
    tag="설문조사",
    resource="survey",
    model=Survey,
    create_schema=SurveyCreate,
    update_schema=SurveyUpdate,
    archetype="master",
    not_found_message="설문조사를 찾을 수 없습니다",
)

FAQ = EntityMeta(
    collection="faqs",
    prefix="FAQ",
    api_path="/api/v1/faqs",
    tag="FAQ",
    resource="faq",
    model=Faq,
    create_schema=FaqCreate,
    update_schema=FaqUpdate,
    archetype="master",
    not_found_message="FAQ를 찾을 수 없습니다",
)

KNOWLEDGE_ARTICLE = EntityMeta(
    collection="knowledge_articles",
    prefix="KART",
    api_path="/api/v1/knowledge-articles",
    tag="지식베이스문서",
    resource="knowledge_article",
    model=KnowledgeArticle,
    create_schema=KnowledgeArticleCreate,
    update_schema=KnowledgeArticleUpdate,
    archetype="master",
    not_found_message="지식 베이스 문서를 찾을 수 없습니다",
)

KNOWLEDGE_CATEGORY = EntityMeta(
    collection="knowledge_categories",
    prefix="KCAT",
    api_path="/api/v1/knowledge-categories",
    tag="지식분류",
    resource="knowledge_category",
    model=KnowledgeCategory,
    create_schema=KnowledgeCategoryCreate,
    update_schema=KnowledgeCategoryUpdate,
    archetype="master",
    not_found_message="지식 분류를 찾을 수 없습니다",
)

CUSTOMER_SEGMENT = EntityMeta(
    collection="customer_segments",
    prefix="CSEG",
    api_path="/api/v1/customer-segments",
    tag="고객세그먼트",
    resource="customer_segment",
    model=CustomerSegment,
    create_schema=CustomerSegmentCreate,
    update_schema=CustomerSegmentUpdate,
    archetype="master",
    not_found_message="고객 세그먼트를 찾을 수 없습니다",
)

COMPETITOR_PROFILE = EntityMeta(
    collection="competitor_profiles",
    prefix="CPROF",
    api_path="/api/v1/competitor-profiles",
    tag="경쟁사프로필",
    resource="competitor_profile",
    model=CompetitorProfile,
    create_schema=CompetitorProfileCreate,
    update_schema=CompetitorProfileUpdate,
    archetype="master",
    not_found_message="경쟁사 프로필을 찾을 수 없습니다",
)

SERVICE_TECHNICIAN = EntityMeta(
    collection="service_technicians",
    prefix="STCH",
    api_path="/api/v1/service-technicians",
    tag="서비스기사",
    resource="service_technician",
    model=ServiceTechnician,
    create_schema=ServiceTechnicianCreate,
    update_schema=ServiceTechnicianUpdate,
    archetype="master",
    not_found_message="서비스 기사를 찾을 수 없습니다",
)

WARRANTY_PERIOD = EntityMeta(
    collection="warranty_periods",
    prefix="WPRD",
    api_path="/api/v1/warranty-periods",
    tag="보증기간",
    resource="warranty_period",
    model=WarrantyPeriod,
    create_schema=WarrantyPeriodCreate,
    update_schema=WarrantyPeriodUpdate,
    archetype="master",
    not_found_message="보증 기간을 찾을 수 없습니다",
)

MARKETING_LIST = EntityMeta(
    collection="marketing_lists",
    prefix="MKTL",
    api_path="/api/v1/marketing-lists",
    tag="마케팅리스트",
    resource="marketing_list",
    model=MarketingList,
    create_schema=MarketingListCreate,
    update_schema=MarketingListUpdate,
    archetype="master",
    not_found_message="마케팅 리스트를 찾을 수 없습니다",
)

MARKETING_AUTOMATION_RULE = EntityMeta(
    collection="marketing_automation_rules",
    prefix="MARR",
    api_path="/api/v1/marketing-automation-rules",
    tag="마케팅자동화규칙",
    resource="marketing_automation_rule",
    model=MarketingAutomationRule,
    create_schema=MarketingAutomationRuleCreate,
    update_schema=MarketingAutomationRuleUpdate,
    archetype="master",
    not_found_message="마케팅 자동화 규칙을 찾을 수 없습니다",
)

TERRITORY_MANAGEMENT = EntityMeta(
    collection="territory_managements",
    prefix="TRMG",
    api_path="/api/v1/territory-managements",
    tag="영역관리",
    resource="territory_management",
    model=TerritoryManagement,
    create_schema=TerritoryManagementCreate,
    update_schema=TerritoryManagementUpdate,
    archetype="master",
    not_found_message="영역 관리를 찾을 수 없습니다",
)

CONTRACT = EntityMeta(
    collection="contracts",
    prefix="CNTR",
    api_path="/api/v1/contracts",
    tag="계약",
    resource="contract",
    model=Contract,
    create_schema=ContractCreate,
    update_schema=ContractUpdate,
    archetype="transaction",
    not_found_message="계약을 찾을 수 없습니다",
)

CONTRACT_RENEWAL = EntityMeta(
    collection="contract_renewals",
    prefix="CRNW",
    api_path="/api/v1/contract-renewals",
    tag="계약 갱신",
    resource="contract_renewal",
    model=ContractRenewal,
    create_schema=ContractRenewalCreate,
    update_schema=ContractRenewalUpdate,
    archetype="transaction",
    not_found_message="계약 갱신을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

SERVICE_ORDER = EntityMeta(
    collection="service_orders",
    prefix="SORD",
    api_path="/api/v1/service-orders",
    tag="서비스주문",
    resource="service_order",
    model=ServiceOrder,
    create_schema=ServiceOrderCreate,
    update_schema=ServiceOrderUpdate,
    archetype="transaction",
    not_found_message="서비스 주문을 찾을 수 없습니다",
)

SERVICE_VISIT = EntityMeta(
    collection="service_visits",
    prefix="SVIS",
    api_path="/api/v1/service-visits",
    tag="서비스방문",
    resource="service_visit",
    model=ServiceVisit,
    create_schema=ServiceVisitCreate,
    update_schema=ServiceVisitUpdate,
    archetype="transaction",
    not_found_message="서비스 방문을 찾을 수 없습니다",
)

WARRANTY_CLAIM = EntityMeta(
    collection="warranty_claims",
    prefix="WCLM",
    api_path="/api/v1/warranty-claims",
    tag="보증클레임",
    resource="warranty_claim",
    model=WarrantyClaim,
    create_schema=WarrantyClaimCreate,
    update_schema=WarrantyClaimUpdate,
    archetype="transaction",
    not_found_message="보증 클레임을 찾을 수 없습니다",
)

EVENT_REGISTRATION = EntityMeta(
    collection="event_registrations",
    prefix="EVRG",
    api_path="/api/v1/event-registrations",
    tag="이벤트등록",
    resource="event_registration",
    model=EventRegistration,
    create_schema=EventRegistrationCreate,
    update_schema=EventRegistrationUpdate,
    archetype="transaction",
    not_found_message="이벤트 등록을 찾을 수 없습니다",
)

EMAIL_CAMPAIGN = EntityMeta(
    collection="email_campaigns",
    prefix="ECMP",
    api_path="/api/v1/email-campaigns",
    tag="이메일캠페인",
    resource="email_campaign",
    model=EmailCampaign,
    create_schema=EmailCampaignCreate,
    update_schema=EmailCampaignUpdate,
    archetype="transaction",
    not_found_message="이메일 캠페인을 찾을 수 없습니다",
)

SMS_CAMPAIGN = EntityMeta(
    collection="sms_campaigns",
    prefix="SCMP",
    api_path="/api/v1/sms-campaigns",
    tag="SMS캠페인",
    resource="sms_campaign",
    model=SmsCampaign,
    create_schema=SmsCampaignCreate,
    update_schema=SmsCampaignUpdate,
    archetype="transaction",
    not_found_message="SMS 캠페인을 찾을 수 없습니다",
)

APPOINTMENT = EntityMeta(
    collection="appointments",
    prefix="APPT",
    api_path="/api/v1/appointments",
    tag="약속/미팅",
    resource="appointment",
    model=Appointment,
    create_schema=AppointmentCreate,
    update_schema=AppointmentUpdate,
    archetype="transaction",
    not_found_message="약속/미팅을 찾을 수 없습니다",
)

NEWSLETTER = EntityMeta(
    collection="newsletters",
    prefix="NWSL",
    api_path="/api/v1/newsletters",
    tag="뉴스레터",
    resource="newsletter",
    model=Newsletter,
    create_schema=NewsletterCreate,
    update_schema=NewsletterUpdate,
    archetype="transaction",
    not_found_message="뉴스레터를 찾을 수 없습니다",
)

CALL_LOG = EntityMeta(
    collection="call_logs",
    prefix="CLOG",
    api_path="/api/v1/call-logs",
    tag="통화기록",
    resource="call_log",
    model=CallLog,
    create_schema=CallLogCreate,
    update_schema=CallLogUpdate,
    archetype="transaction",
    not_found_message="통화 기록을 찾을 수 없습니다",
)

LEAD_SCORING = EntityMeta(
    collection="lead_scorings",
    prefix="LSCR",
    api_path="/api/v1/lead-scorings",
    tag="리드스코어링",
    resource="lead_scoring",
    model=LeadScoring,
    create_schema=LeadScoringCreate,
    update_schema=LeadScoringUpdate,
    archetype="transaction",
    not_found_message="리드 스코어링을 찾을 수 없습니다",
)

LOYALTY_POINT = EntityMeta(
    collection="loyalty_points",
    prefix="LYPT",
    api_path="/api/v1/loyalty-points",
    tag="로열티포인트",
    resource="loyalty_point",
    model=LoyaltyPoint,
    create_schema=LoyaltyPointCreate,
    update_schema=LoyaltyPointUpdate,
    archetype="transaction",
    not_found_message="로열티 포인트를 찾을 수 없습니다",
)

SURVEY_RESPONSE = EntityMeta(
    collection="survey_responses",
    prefix="SVRS",
    api_path="/api/v1/survey-responses",
    tag="설문응답",
    resource="survey_response",
    model=SurveyResponse,
    create_schema=SurveyResponseCreate,
    update_schema=SurveyResponseUpdate,
    archetype="transaction",
    not_found_message="설문 응답을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    PROSPECT,
    SERVICE_CONTRACT,
    SURVEY,
    FAQ,
    KNOWLEDGE_ARTICLE,
    KNOWLEDGE_CATEGORY,
    CUSTOMER_SEGMENT,
    COMPETITOR_PROFILE,
    SERVICE_TECHNICIAN,
    WARRANTY_PERIOD,
    MARKETING_LIST,
    MARKETING_AUTOMATION_RULE,
    TERRITORY_MANAGEMENT,
    CONTRACT,
    CONTRACT_RENEWAL,
    # 트랜잭션
    SERVICE_ORDER,
    SERVICE_VISIT,
    WARRANTY_CLAIM,
    EVENT_REGISTRATION,
    EMAIL_CAMPAIGN,
    SMS_CAMPAIGN,
    APPOINTMENT,
    NEWSLETTER,
    CALL_LOG,
    LEAD_SCORING,
    LOYALTY_POINT,
    SURVEY_RESPONSE,
]
