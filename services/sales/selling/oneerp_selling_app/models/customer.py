"""고객(Customer) 마스터 모델."""

from __future__ import annotations

from oneerp_core.models import BasePartyDocument, EmbeddedAddress, EmbeddedContact
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """고객 생성 요청 스키마."""

    customer_name: str
    customer_type: str = "individual"  # individual / company
    tax_id: str | None = None
    default_currency: str = "KRW"
    territory: str | None = None
    address: EmbeddedAddress | None = None
    contact: EmbeddedContact | None = None


class CustomerUpdate(BaseModel):
    """고객 수정 요청 스키마."""

    customer_name: str | None = None
    customer_type: str | None = None
    tax_id: str | None = None
    default_currency: str | None = None
    territory: str | None = None
    address: EmbeddedAddress | None = None
    contact: EmbeddedContact | None = None


class Customer(BasePartyDocument):
    """고객 마스터 — 판매 거래 상대방 정보.

    naming prefix: CUST
    """

    customer_name: str = Field(default="", description="고객명")
    customer_type: str = Field(default="individual", description="고객 유형 (individual / company)")
    territory: str | None = Field(default=None, description="영업 지역")
