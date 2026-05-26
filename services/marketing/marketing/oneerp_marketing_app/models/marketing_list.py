"""마케팅 대상 목록 모델 — 캠페인 발송 대상을 관리한다."""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class MarketingListMember(BaseModel):
    """마케팅 목록 구성원."""

    contact_type: str = ""  # customer/lead/manual
    contact_id: str = ""
    email: str = ""
    phone: str = ""
    opt_in: bool = True  # 수신동의 여부 (한국 정보통신망법)


class MarketingListCreate(BaseModel):
    """마케팅 대상 목록 생성 요청 스키마."""

    name: str
    source_type: str = "manual"  # customer/lead/manual
    filter_criteria: dict[str, Any] = {}
    members: list[MarketingListMember] = []
    company: str = ""


class MarketingListUpdate(BaseModel):
    """마케팅 대상 목록 수정 요청 스키마."""

    name: str | None = None
    source_type: str | None = None
    filter_criteria: dict[str, Any] | None = None
    members: list[MarketingListMember] | None = None


class MarketingList(BaseDocument):
    """마케팅 대상 목록 문서 — 캠페인 발송 대상 목록을 저장한다."""

    name: str = ""
    source_type: str = "manual"
    filter_criteria: dict[str, Any] = {}
    members: list[MarketingListMember] = []
    member_count: int = 0
    company: str = ""
