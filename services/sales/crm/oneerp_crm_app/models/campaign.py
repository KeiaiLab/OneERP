"""캠페인(Campaign) 문서 모델 — CRM 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CampaignCreate(BaseModel):
    """캠페인 생성 요청 스키마."""

    campaign_name: str
    start_date: date | None = None
    end_date: date | None = None
    status: str = "planned"
    description: str = ""


class CampaignUpdate(BaseModel):
    """캠페인 수정 요청 스키마."""

    campaign_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    description: str | None = None


class Campaign(BaseDocument):
    """캠페인 문서 — CRM 캠페인 마스터.

    naming prefix: CMPG
    """

    campaign_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    status: str = "planned"
    description: str = ""
