"""SMS 캠페인(SmsCampaign) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SmsCampaignCreate(BaseModel):
    """SMS 캠페인 생성 요청 스키마."""

    campaign_name: str
    message: str = ""
    send_date: date | None = None
    recipient_count: int = 0
    delivery_rate: Decimal = Decimal(0)


class SmsCampaignUpdate(BaseModel):
    """SMS 캠페인 수정 요청 스키마."""

    campaign_name: str | None = None
    message: str | None = None
    send_date: date | None = None
    recipient_count: int | None = None
    delivery_rate: Decimal | None = None


class SmsCampaign(BaseDocument):
    """SMS 캠페인 문서."""

    campaign_name: str = ""
    message: str = ""
    send_date: date | None = None
    recipient_count: int = 0
    delivery_rate: Decimal = Decimal(0)
