"""운임 정산(FreightSettlement) 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class ChargeItem(BaseModel):
    """추가 비용/차감 항목."""

    description: str = ""
    amount: float = 0


class FreightSettlementCreate(BaseModel):
    """운임 정산 생성 요청."""

    carrier_id: str
    period_from: date
    period_to: date
    shipment_ids: list[str]
    subtotal_amount: float
    fuel_surcharge: float = 0
    additional_charges: list[ChargeItem] | None = None
    deductions: list[ChargeItem] | None = None
    currency: str = "KRW"
    notes: str | None = None
    company: str = ""


class FreightSettlementUpdate(BaseModel):
    """운임 정산 수정 요청."""

    additional_charges: list[ChargeItem] | None = None
    deductions: list[ChargeItem] | None = None
    notes: str | None = None
    company: str | None = None


class FreightSettlement(BaseDocument):
    """운임 정산 — 기간별 운송사 운임 집계 문서.

    naming prefix: FS
    """

    settlement_no: str = Field(default="", description="정산번호")
    carrier_id: str = Field(default="", description="운송사")
    period_from: date | None = Field(default=None, description="정산 시작일")
    period_to: date | None = Field(default=None, description="정산 종료일")
    shipment_ids: list[str] = Field(default_factory=list, description="포함 배송 건")
    total_shipments: int = Field(default=0, description="배송 건 수")
    subtotal_amount: float = Field(default=0, description="운임 소계")
    fuel_surcharge: float = Field(default=0, description="유류할증료 합계")
    additional_charges: list[ChargeItem] = Field(default_factory=list, description="추가 비용")
    deductions: list[ChargeItem] = Field(default_factory=list, description="차감 항목")
    tax_amount: float = Field(default=0, description="부가세")
    total_amount: float = Field(default=0, description="정산 총액")
    currency: str = Field(default="KRW", description="통화")
    status: str = Field(default="draft", description="정산 상태")
    invoice_no: str | None = Field(default=None, description="세금계산서 번호")
    payment_due_date: date | None = Field(default=None, description="지급 예정일")
    notes: str | None = Field(default=None, description="비고")
    company: str = Field(default="", description="회사")
