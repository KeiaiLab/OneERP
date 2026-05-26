"""부가세 신고(VAT Return) 문서 모델 — 워크플로우: draft → submitted → cancelled.

L2 엔티티 정의:
- BR-KTAX-005: net_tax = output_tax - input_tax (양수=납부, 음수=환급)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class VATReturnCreate(BaseModel):
    """부가세 신고 생성 요청 스키마."""

    period: str = ""
    tax_amount: Decimal = Decimal(0)
    filing_date: date | None = None
    status: str = "draft"
    output_tax: Decimal = Decimal(0)
    input_tax: Decimal = Decimal(0)
    net_tax: Decimal = Decimal(0)


class VATReturnUpdate(BaseModel):
    """부가세 신고 수정 요청 스키마."""

    period: str | None = None
    tax_amount: Decimal | None = None
    filing_date: date | None = None
    status: str | None = None
    output_tax: Decimal | None = None
    input_tax: Decimal | None = None
    net_tax: Decimal | None = None


class VATReturn(BaseDocument):
    """부가세 신고 문서 — 부가가치세 신고/납부 관리.

    naming prefix: VAT
    """

    period: str = ""
    tax_amount: Decimal = Decimal(0)
    filing_date: date | None = None
    status: str = "draft"
    output_tax: Decimal = Decimal(0)
    input_tax: Decimal = Decimal(0)
    net_tax: Decimal = Decimal(0)
