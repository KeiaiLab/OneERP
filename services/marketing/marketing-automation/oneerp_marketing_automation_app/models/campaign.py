"""마케팅 캠페인 모델 — 마케팅 캠페인의 기획·실행·성과를 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CampaignCreate(BaseModel):
    """캠페인 생성 요청 스키마."""

    campaign_name: str
    campaign_type: str = "email"  # email/sms/social/display/search/multi_channel
    channel: str = ""
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal = Decimal(0)
    currency: str = "KRW"
    target_audience_id: str = ""
    description: str = ""
    goals: dict = {}


class CampaignUpdate(BaseModel):
    """캠페인 수정 요청 스키마."""

    campaign_name: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal | None = None
    description: str | None = None
    goals: dict | None = None


class Campaign(BaseDocument):
    """캠페인 문서 — 마케팅 캠페인 정보를 저장한다."""

    campaign_name: str = ""
    campaign_type: str = "email"
    channel: str = ""
    status: str = "draft"  # draft/scheduled/running/paused/completed/cancelled
    start_date: date | None = None
    end_date: date | None = None
    budget: Decimal = Decimal(0)
    spent: Decimal = Decimal(0)
    currency: str = "KRW"
    target_audience_id: str = ""
    description: str = ""
    goals: dict = {}
    metrics: dict = {}  # impressions, clicks, conversions, revenue
