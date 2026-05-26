"""전자상거래 채널 모델 — 마켓플레이스 연동 채널을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ECommerceChannelCreate(BaseModel):
    """전자상거래 채널 생성 요청 스키마."""

    channel_code: str
    channel_name: str
    platform: str  # naver/coupang/11st/gmarket/auction/custom
    sync_frequency: str = "1h"
    is_active: bool = True
    warehouse_id: str = ""
    price_list_id: str = ""


class ECommerceChannelUpdate(BaseModel):
    """전자상거래 채널 수정 요청 스키마."""

    channel_name: str | None = None
    platform: str | None = None
    sync_frequency: str | None = None
    is_active: bool | None = None
    warehouse_id: str | None = None
    price_list_id: str | None = None


class ECommerceChannel(BaseDocument):
    """전자상거래 채널 문서 — 마켓플레이스 연동 채널 정보를 저장한다."""

    channel_code: str = ""
    channel_name: str = ""
    platform: str = ""
    sync_frequency: str = "1h"
    is_active: bool = True
    warehouse_id: str = ""
    price_list_id: str = ""
