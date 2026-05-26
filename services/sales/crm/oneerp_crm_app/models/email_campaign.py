"""이메일 캠페인(EmailCampaign) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class EmailCampaignCreate(BaseModel):
    """이메일 캠페인 생성 요청 스키마."""

    campaign_name: str
    subject: str = ""
    send_date: date | None = None
    recipient_count: int = 0
    open_rate: Decimal = Decimal(0)
    click_rate: Decimal = Decimal(0)


class EmailCampaignUpdate(BaseModel):
    """이메일 캠페인 수정 요청 스키마."""

    campaign_name: str | None = None
    subject: str | None = None
    send_date: date | None = None
    recipient_count: int | None = None
    open_rate: Decimal | None = None
    click_rate: Decimal | None = None


class EmailCampaign(BaseDocument):
    """이메일 캠페인 문서."""

    campaign_name: str = ""
    subject: str = ""
    send_date: date | None = None
    recipient_count: int = 0
    open_rate: Decimal = Decimal(0)
    click_rate: Decimal = Decimal(0)
