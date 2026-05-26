"""수입 신고(ImportDeclaration) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-BUY-017: 수입 신고 관세 기록 (hs_code, declared_value, customs_duty)
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ImportDeclarationCreate(BaseModel):
    """수입 신고 생성 요청 스키마."""

    purchase_order_id: str
    origin_country: str = ""
    hs_code: str = ""
    declared_value: Decimal = Decimal(0)
    currency: str = "USD"
    customs_duty: Decimal = Decimal(0)
    declaration_date: date | None = None


class ImportDeclarationUpdate(BaseModel):
    """수입 신고 수정 요청 스키마."""

    purchase_order_id: str | None = None
    origin_country: str | None = None
    hs_code: str | None = None
    declared_value: Decimal | None = None
    currency: str | None = None
    customs_duty: Decimal | None = None
    declaration_date: date | None = None


class ImportDeclaration(BaseDocument):
    """수입 신고 문서."""

    purchase_order_id: str = ""
    origin_country: str = ""
    hs_code: str = ""
    declared_value: Decimal = Decimal(0)
    currency: str = "USD"
    customs_duty: Decimal = Decimal(0)
    declaration_date: date | None = None
