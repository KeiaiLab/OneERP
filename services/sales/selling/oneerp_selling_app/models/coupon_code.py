"""쿠폰 코드(CouponCode) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CouponCodeCreate(BaseModel):
    """쿠폰 코드 생성 요청 스키마."""

    coupon_code: str
    coupon_type: str = ""
    discount_value: Decimal = Decimal(0)
    max_uses: int = 0
    used_count: int = 0
    valid_from: date | None = None
    valid_until: date | None = None
    is_active: bool = True


class CouponCodeUpdate(BaseModel):
    """쿠폰 코드 수정 요청 스키마."""

    coupon_code: str | None = None
    coupon_type: str | None = None
    discount_value: Decimal | None = None
    max_uses: int | None = None
    used_count: int | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    is_active: bool | None = None


class CouponCode(BaseDocument):
    """쿠폰 코드 문서."""

    coupon_code: str = ""
    coupon_type: str = ""
    discount_value: Decimal = Decimal(0)
    max_uses: int = 0
    used_count: int = 0
    valid_from: date | None = None
    valid_until: date | None = None
    is_active: bool = True
