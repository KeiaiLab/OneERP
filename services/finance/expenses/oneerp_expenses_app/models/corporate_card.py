"""법인카드(CorporateCard) 문서 모델 — Expenses 모듈.

L2 비즈니스 룰: BR-EXP-009 (법인카드 거래는 생성/조회만), BR-EXP-012 (한도 경고).
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CorporateCardCreate(BaseModel):
    """법인카드 생성 요청 스키마."""

    card_number: str
    employee_id: str
    card_type: str = "credit"
    credit_limit: Decimal = Decimal(0)
    is_active: bool = True


class CorporateCardUpdate(BaseModel):
    """법인카드 수정 요청 스키마."""

    card_number: str | None = None
    employee_id: str | None = None
    card_type: str | None = None
    credit_limit: Decimal | None = None
    is_active: bool | None = None


class CorporateCard(BaseDocument):
    """법인카드 문서 — Expenses 법인카드 마스터.

    naming prefix: CC
    """

    card_number: str = ""
    employee_id: str = Field(default="", alias="employee")
    card_type: str = "credit"
    credit_limit: Decimal = Decimal(0)
    is_active: bool = True
