"""결제 조건 템플릿(PaymentTermsTemplate) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PaymentTermsTemplateCreate(BaseModel):
    """결제 조건 템플릿 생성 요청 스키마."""

    template_name: str
    description: str = ""
    credit_days: int = 0
    discount_percentage: Decimal = Decimal(0)
    discount_days: int = 0


class PaymentTermsTemplateUpdate(BaseModel):
    """결제 조건 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    description: str | None = None
    credit_days: int | None = None
    discount_percentage: Decimal | None = None
    discount_days: int | None = None


class PaymentTermsTemplate(BaseDocument):
    """결제 조건 템플릿 문서."""

    template_name: str = ""
    description: str = ""
    credit_days: int = 0
    discount_percentage: Decimal = Decimal(0)
    discount_days: int = 0
