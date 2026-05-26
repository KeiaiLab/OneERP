"""마케팅 리스트(MarketingList) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class MarketingListCreate(BaseModel):
    """마케팅 리스트 생성 요청 스키마."""

    list_name: str
    description: str = ""
    member_count: int = 0
    is_active: bool = True


class MarketingListUpdate(BaseModel):
    """마케팅 리스트 수정 요청 스키마."""

    list_name: str | None = None
    description: str | None = None
    member_count: int | None = None
    is_active: bool | None = None


class MarketingList(BaseDocument):
    """마케팅 리스트 문서."""

    list_name: str = ""
    description: str = ""
    member_count: int = 0
    is_active: bool = True
