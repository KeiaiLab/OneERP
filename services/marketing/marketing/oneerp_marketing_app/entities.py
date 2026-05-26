"""마케팅 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

EmailCampaign, SMSCampaign, MarketingList, EventRegistration,
Survey, SurveyResponse, LoyaltyProgram, LoyaltyPoint 엔티티를 EntityMeta로 선언한다.
캠페인 발송 로직은 routes/에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.email_campaign import EmailCampaign, EmailCampaignCreate, EmailCampaignUpdate
from .models.event_registration import (
    EventRegistration,
    EventRegistrationCreate,
    EventRegistrationUpdate,
)
from .models.loyalty import (
    LoyaltyPoint,
    LoyaltyPointCreate,
    LoyaltyPointUpdate,
    LoyaltyProgram,
    LoyaltyProgramCreate,
    LoyaltyProgramUpdate,
)
from .models.marketing_list import MarketingList, MarketingListCreate, MarketingListUpdate
from .models.sms_campaign import SMSCampaign, SMSCampaignCreate, SMSCampaignUpdate
from .models.survey import (
    Survey,
    SurveyCreate,
    SurveyResponse,
    SurveyResponseCreate,
    SurveyResponseUpdate,
    SurveyUpdate,
)

ENTITY_METAS: list[EntityMeta] = [
    # 마스터 데이터
    EntityMeta(
        collection="marketing_lists",
        prefix="ML",
        api_path="/api/v1/marketing/lists",
        tag="마케팅 목록",
        resource="marketing_list",
        model=MarketingList,
        create_schema=MarketingListCreate,
        update_schema=MarketingListUpdate,
        archetype="master",
        not_found_message="마케팅 목록을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="loyalty_programs",
        prefix="LP",
        api_path="/api/v1/marketing/loyalty-programs",
        tag="로열티 프로그램",
        resource="loyalty_program",
        model=LoyaltyProgram,
        create_schema=LoyaltyProgramCreate,
        update_schema=LoyaltyProgramUpdate,
        archetype="master",
        not_found_message="로열티 프로그램을 찾을 수 없습니다",
    ),
    # 트랜잭션 문서
    EntityMeta(
        collection="email_campaigns",
        prefix="EC",
        api_path="/api/v1/marketing/email-campaigns",
        tag="이메일 캠페인",
        resource="email_campaign",
        model=EmailCampaign,
        create_schema=EmailCampaignCreate,
        update_schema=EmailCampaignUpdate,
        archetype="transaction",
        not_found_message="이메일 캠페인을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="sms_campaigns",
        prefix="SC",
        api_path="/api/v1/marketing/sms-campaigns",
        tag="SMS 캠페인",
        resource="sms_campaign",
        model=SMSCampaign,
        create_schema=SMSCampaignCreate,
        update_schema=SMSCampaignUpdate,
        archetype="transaction",
        not_found_message="SMS 캠페인을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="event_registrations",
        prefix="ER",
        api_path="/api/v1/marketing/event-registrations",
        tag="행사 등록",
        resource="event_registration",
        model=EventRegistration,
        create_schema=EventRegistrationCreate,
        update_schema=EventRegistrationUpdate,
        archetype="transaction",
        not_found_message="행사 등록을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="surveys",
        prefix="SVY",
        api_path="/api/v1/marketing/surveys",
        tag="설문조사",
        resource="survey",
        model=Survey,
        create_schema=SurveyCreate,
        update_schema=SurveyUpdate,
        archetype="transaction",
        not_found_message="설문조사를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="survey_responses",
        prefix="SVYR",
        api_path="/api/v1/marketing/survey-responses",
        tag="설문 응답",
        resource="survey_response",
        model=SurveyResponse,
        create_schema=SurveyResponseCreate,
        update_schema=SurveyResponseUpdate,
        archetype="transaction",
        not_found_message="설문 응답을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="loyalty_points",
        prefix="LPT",
        api_path="/api/v1/marketing/loyalty-points",
        tag="포인트 내역",
        resource="loyalty_point",
        model=LoyaltyPoint,
        create_schema=LoyaltyPointCreate,
        update_schema=LoyaltyPointUpdate,
        archetype="transaction",
        not_found_message="포인트 내역을 찾을 수 없습니다",
    ),
]
