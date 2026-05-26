"""전자세금계산서(E-Tax Invoice) 문서 모델.

L2 엔티티 정의:
- BR-KTAX-001: 전자세금계산서 발행 의무 (부가가치세법 제32조)
- BR-KTAX-002: 공급자/수요자 사업자번호, 공급가액, 부가세액, 작성일자 필수
"""

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ETaxInvoiceCreate(BaseModel):
    """전자세금계산서 생성 요청 스키마."""

    invoice_ref: str
    issue_date: date
    supplier_or_customer: str
    supply_amount: Decimal = Decimal(0)
    tax_amount: Decimal = Decimal(0)
    nts_confirmation_no: str | None = None
    transmission_status: str = "pending"
    issue_type: str = "정발행"
    receipt_type: str = "청구"


class ETaxInvoiceUpdate(BaseModel):
    """전자세금계산서 수정 요청 스키마."""

    invoice_ref: str | None = None
    issue_date: date | None = None
    supplier_or_customer: str | None = None
    supply_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    nts_confirmation_no: str | None = None
    transmission_status: str | None = None
    issue_type: str | None = None
    receipt_type: str | None = None


class NTSCancelRequest(BaseModel):
    """국세청 전송 취소 요청 스키마."""

    reason: str


class ETaxInvoice(BaseDocument):
    """전자세금계산서 문서 — 국세청 연동 세금계산서.

    naming prefix: ETAX
    """

    invoice_ref: str = ""
    issue_date: date | None = None
    supplier_or_customer: str = ""
    supply_amount: Decimal = Decimal(0)
    tax_amount: Decimal = Decimal(0)
    nts_confirmation_no: str | None = None
    transmission_status: str = "pending"
    issue_type: str = "정발행"
    receipt_type: str = "청구"
    xml_payload: str = ""
    nts_response: dict = {}
    nts_submitted_at: datetime | None = None
    nts_confirmed_at: datetime | None = None
