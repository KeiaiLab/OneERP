"""이커머스 채널(ECommerceChannel) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ECommerceChannelCreate(BaseModel):
    """이커머스 채널 생성 요청 스키마."""

    channel_name: str
    platform: str = ""
    api_endpoint: str = ""
    is_active: bool = True


class ECommerceChannelUpdate(BaseModel):
    """이커머스 채널 수정 요청 스키마."""

    channel_name: str | None = None
    platform: str | None = None
    api_endpoint: str | None = None
    is_active: bool | None = None


class ECommerceChannel(BaseDocument):
    """이커머스 채널 문서."""

    channel_name: str = ""
    platform: str = ""
    api_endpoint: str = ""
    is_active: bool = True
