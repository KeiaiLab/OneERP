"""수출 신고(ExportDeclaration) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ExportDeclarationCreate(BaseModel):
    """수출 신고 생성 요청 스키마."""

    invoice_id: str
    destination_country: str = ""
    hs_code: str = ""
    declared_value: Decimal = Decimal(0)
    currency: str = "USD"
    declaration_date: date | None = None


class ExportDeclarationUpdate(BaseModel):
    """수출 신고 수정 요청 스키마."""

    invoice_id: str | None = None
    destination_country: str | None = None
    hs_code: str | None = None
    declared_value: Decimal | None = None
    currency: str | None = None
    declaration_date: date | None = None


class ExportDeclaration(BaseDocument):
    """수출 신고 문서."""

    invoice_id: str = ""
    destination_country: str = ""
    hs_code: str = ""
    declared_value: Decimal = Decimal(0)
    currency: str = "USD"
    declaration_date: date | None = None
