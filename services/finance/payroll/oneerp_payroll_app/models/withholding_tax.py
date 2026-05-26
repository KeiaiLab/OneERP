"""원천징수(WithholdingTax) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WithholdingTaxCreate(BaseModel):
    """원천징수 생성 요청 스키마."""

    tax_name: str
    rate: Decimal = Decimal(0)
    threshold: Decimal = Decimal(0)
    tax_type: str = "income"


class WithholdingTaxUpdate(BaseModel):
    """원천징수 수정 요청 스키마."""

    tax_name: str | None = None
    rate: Decimal | None = None
    threshold: Decimal | None = None
    tax_type: str | None = None


class WithholdingTax(BaseDocument):
    """원천징수 문서 — Payroll 원천징수 마스터.

    naming prefix: WHT
    """

    tax_name: str = ""
    rate: Decimal = Decimal(0)
    threshold: Decimal = Decimal(0)
    tax_type: str = "income"
