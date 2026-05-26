"""마케팅자동화 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용."""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.audience_segment import AudienceSegment, AudienceSegmentCreate, AudienceSegmentUpdate
from .models.automation_workflow import (
    AutomationWorkflow,
    AutomationWorkflowCreate,
    AutomationWorkflowUpdate,
)
from .models.campaign import Campaign, CampaignCreate, CampaignUpdate
from .models.campaign_analytics import (
    CampaignAnalytics,
    CampaignAnalyticsCreate,
    CampaignAnalyticsUpdate,
)
from .models.email_template import EmailTemplate, EmailTemplateCreate, EmailTemplateUpdate

ENTITY_METAS: list[EntityMeta] = [
    EntityMeta(
        collection="campaigns",
        prefix="MKC",
        api_path="/api/v1/marketing/campaigns",
        tag="캠페인",
        resource="campaign",
        model=Campaign,
        create_schema=CampaignCreate,
        update_schema=CampaignUpdate,
        archetype="transaction",
        not_found_message="캠페인을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="audience_segments",
        prefix="SEG",
        api_path="/api/v1/marketing/segments",
        tag="오디언스세그먼트",
        resource="audience_segment",
        model=AudienceSegment,
        create_schema=AudienceSegmentCreate,
        update_schema=AudienceSegmentUpdate,
        archetype="master",
        not_found_message="오디언스 세그먼트를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="email_templates",
        prefix="ETPL",
        api_path="/api/v1/marketing/email-templates",
        tag="이메일템플릿",
        resource="email_template",
        model=EmailTemplate,
        create_schema=EmailTemplateCreate,
        update_schema=EmailTemplateUpdate,
        archetype="master",
        not_found_message="이메일 템플릿을 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="automation_workflows",
        prefix="AWF",
        api_path="/api/v1/marketing/workflows",
        tag="자동화워크플로우",
        resource="automation_workflow",
        model=AutomationWorkflow,
        create_schema=AutomationWorkflowCreate,
        update_schema=AutomationWorkflowUpdate,
        archetype="master",
        not_found_message="자동화 워크플로우를 찾을 수 없습니다",
    ),
    EntityMeta(
        collection="campaign_analytics",
        prefix="MKA",
        api_path="/api/v1/marketing/analytics",
        tag="캠페인분석",
        resource="campaign_analytics",
        model=CampaignAnalytics,
        create_schema=CampaignAnalyticsCreate,
        update_schema=CampaignAnalyticsUpdate,
        archetype="transaction",
        not_found_message="캠페인 분석 데이터를 찾을 수 없습니다",
    ),
]
