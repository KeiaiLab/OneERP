"""프로모션(PromotionalScheme) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PromotionalSchemeCreate(BaseModel):
    """프로모션 생성 요청 스키마."""

    scheme_name: str
    start_date: date | None = None
    end_date: date | None = None
    discount_percentage: Decimal = Decimal(0)
    min_qty: Decimal = Decimal(0)
    is_active: bool = True


class PromotionalSchemeUpdate(BaseModel):
    """프로모션 수정 요청 스키마."""

    scheme_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    discount_percentage: Decimal | None = None
    min_qty: Decimal | None = None
    is_active: bool | None = None


class PromotionalScheme(BaseDocument):
    """프로모션 문서."""

    scheme_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    discount_percentage: Decimal = Decimal(0)
    min_qty: Decimal = Decimal(0)
    is_active: bool = True
