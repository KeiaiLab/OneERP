"""리드(Lead) 문서 모델 — CRM 잠재 고객."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LeadStatus(StrEnum):
    """리드 상태."""

    OPEN = "open"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadCreate(BaseModel):
    """리드 생성 요청 스키마."""

    lead_name: str
    company_name: str = ""
    email: str = ""
    phone: str = ""
    source: str = ""
    interested_item: str = ""
    assigned_to: str = ""
    lead_score: float = 0.0


class LeadUpdate(BaseModel):
    """리드 수정 요청 스키마."""

    lead_name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    interested_item: str | None = None
    assigned_to: str | None = None
    lead_score: float | None = None
    status: LeadStatus | None = None


class Lead(BaseDocument):
    """리드 문서 — CRM 잠재 고객 정보.

    naming prefix: LEAD
    """

    lead_name: str = ""
    company_name: str = ""
    email: str = ""
    phone: str = ""
    source: str = ""
    interested_item: str = ""
    assigned_to: str = ""
    lead_score: float = 0.0
    status: LeadStatus = LeadStatus.OPEN
