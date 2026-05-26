"""캠페인 분석 모델 — 캠페인 성과 데이터와 이벤트를 기록한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class CampaignAnalyticsCreate(BaseModel):
    """캠페인 분석 생성 요청 스키마."""

    campaign_id: str
    event_type: str = "impression"  # impression/click/open/conversion/bounce/unsubscribe
    recipient_id: str = ""
    channel: str = ""
    metadata: dict = {}


class CampaignAnalyticsUpdate(BaseModel):
    """캠페인 분석 수정 요청 스키마."""

    metadata: dict | None = None


class CampaignAnalytics(BaseDocument):
    """캠페인 분석 문서 — 캠페인 이벤트 데이터를 저장한다."""

    campaign_id: str = ""
    event_type: str = "impression"
    recipient_id: str = ""
    channel: str = ""
    metadata: dict = {}
    event_at: datetime | None = None
    revenue_attributed: Decimal = Decimal(0)
