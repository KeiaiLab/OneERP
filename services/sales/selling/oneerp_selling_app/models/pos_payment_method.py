"""POS 결제 수단(POSPaymentMethod) 마스터 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class POSPaymentMethodCreate(BaseModel):
    """POS 결제 수단 생성 요청 스키마."""

    method_name: str
    payment_type: str = "cash"
    is_active: bool = True


class POSPaymentMethodUpdate(BaseModel):
    """POS 결제 수단 수정 요청 스키마."""

    method_name: str | None = None
    payment_type: str | None = None
    is_active: bool | None = None


class POSPaymentMethod(BaseDocument):
    """POS 결제 수단 마스터 — 현금/카드/전자결제 등.

    naming prefix: POPM
    """

    method_name: str = ""
    payment_type: str = "cash"
    is_active: bool = True
