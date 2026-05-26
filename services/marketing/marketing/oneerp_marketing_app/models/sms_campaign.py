"""SMS 캠페인 모델 — SMS 마케팅 캠페인을 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class SMSCampaignCreate(BaseModel):
    """SMS 캠페인 생성 요청 스키마."""

    name: str
    marketing_list_id: str
    message: str
    scheduled_date: datetime | None = None
    company: str = ""


class SMSCampaignUpdate(BaseModel):
    """SMS 캠페인 수정 요청 스키마."""

    name: str | None = None
    message: str | None = None
    scheduled_date: datetime | None = None
    status: str | None = None


class SMSCampaign(BaseDocument):
    """SMS 캠페인 문서 — SMS 캠페인 상세 정보를 저장한다."""

    name: str = ""
    marketing_list_id: str = ""
    message: str = ""
    scheduled_date: datetime | None = None
    sent_count: int = 0
    delivery_count: int = 0
    status: str = "draft"  # draft/scheduled/sent/completed
    company: str = ""
