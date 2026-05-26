"""세금규칙(Tax Rule) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-KTAX-018: 연결 세금 계산 (조건 매칭으로 세율 자동 결정, 미매칭 시 기본 10%)
- BR-KTAX-007: 4대보험 요율 (payroll 서비스 social_insurance_service에서 사용)
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class TaxRuleCreate(BaseModel):
    """세금규칙 생성 요청 스키마."""

    tax_type: str
    tax_rate: Decimal = Decimal(0)
    conditions: dict = {}
    priority: int = 0
    is_active: bool = True


class TaxRuleUpdate(BaseModel):
    """세금규칙 수정 요청 스키마."""

    tax_type: str | None = None
    tax_rate: Decimal | None = None
    conditions: dict | None = None
    priority: int | None = None
    is_active: bool | None = None


class TaxRule(BaseDocument):
    """세금규칙 문서 — 세금 자동 적용 규칙.

    naming prefix: TXR
    """

    tax_type: str = ""
    tax_rate: Decimal = Decimal(0)
    conditions: dict = {}
    priority: int = 0
    is_active: bool = True
