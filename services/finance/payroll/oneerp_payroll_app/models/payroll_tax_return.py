"""급여세신고(PayrollTaxReturn) 문서 모델 — Payroll 모듈."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class PayrollTaxReturnCreate(BaseModel):
    """급여세신고 생성 요청 스키마."""

    period: str
    tax_type: str
    total_taxable: Decimal = Decimal(0)
    total_tax: Decimal = Decimal(0)
    filing_date: date | None = None


class PayrollTaxReturnUpdate(BaseModel):
    """급여세신고 수정 요청 스키마."""

    period: str | None = None
    tax_type: str | None = None
    total_taxable: Decimal | None = None
    total_tax: Decimal | None = None
    filing_date: date | None = None


class PayrollTaxReturn(BaseDocument):
    """급여세신고 문서 — Payroll 급여세 신고 트랜잭션.

    naming prefix: PTR
    """

    period: str = ""
    tax_type: str = ""
    total_taxable: Decimal = Decimal(0)
    total_tax: Decimal = Decimal(0)
    filing_date: date | None = None
