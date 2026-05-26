"""공급업체(Supplier) 마스터 모델."""

from __future__ import annotations

from oneerp_core.models import BasePartyDocument, EmbeddedAddress, EmbeddedContact
from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    """공급업체 생성 요청 스키마."""

    supplier_name: str
    supplier_group: str | None = None
    supplier_type: str
    tax_id: str | None = None
    country: str = "KR"
    representative_name: str | None = None
    default_currency: str = "KRW"
    payment_terms: str | None = None
    delivery_terms: str | None = None
    bank_name: str | None = None
    bank_account_no: str | None = None
    supplied_items: list[str] = Field(default_factory=list)
    address: EmbeddedAddress | None = None
    contact: EmbeddedContact | None = None
    is_active: bool = True


class SupplierUpdate(BaseModel):
    """공급업체 수정 요청 스키마."""

    supplier_name: str | None = None
    supplier_group: str | None = None
    supplier_type: str | None = None
    tax_id: str | None = None
    country: str | None = None
    representative_name: str | None = None
    default_currency: str | None = None
    payment_terms: str | None = None
    delivery_terms: str | None = None
    bank_name: str | None = None
    bank_account_no: str | None = None
    supplied_items: list[str] | None = None
    address: EmbeddedAddress | None = None
    contact: EmbeddedContact | None = None
    is_active: bool | None = None


class Supplier(BasePartyDocument):
    """공급업체 마스터 — 구매 거래 상대방 정보.

    naming prefix: SUP
    """

    supplier_name: str = Field(default="", description="공급업체명")
    supplier_group: str | None = Field(default=None, description="공급업체 그룹")
    supplier_type: str = Field(default="", description="공급업체 유형")
    country: str = Field(default="KR", description="국가")
    representative_name: str | None = Field(default=None, description="대표자명")
    payment_terms: str | None = Field(default=None, description="결제 조건")
    delivery_terms: str | None = Field(default=None, description="납기 조건")
    bank_name: str | None = Field(default=None, description="은행명")
    bank_account_no: str | None = Field(default=None, description="계좌번호")
    supplied_items: list[str] = Field(default_factory=list, description="공급 가능 품목")
    is_active: bool = Field(default=True, description="활성 여부")
