"""판매 파트너(SalesPartner) 마스터 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SalesPartnerCreate(BaseModel):
    """판매 파트너 생성 요청 스키마."""

    partner_name: str
    commission_rate: Decimal = Decimal(0)
    territory: str = ""
    partner_type: str = ""
    is_active: bool = True


class SalesPartnerUpdate(BaseModel):
    """판매 파트너 수정 요청 스키마."""

    partner_name: str | None = None
    commission_rate: Decimal | None = None
    territory: str | None = None
    partner_type: str | None = None
    is_active: bool | None = None


class SalesPartner(BaseDocument):
    """판매 파트너 마스터 — 커미션 기반 외부 판매 채널.

    naming prefix: SPAR
    """

    partner_name: str = ""
    commission_rate: Decimal = Decimal(0)
    territory: str = ""
    partner_type: str = ""
    is_active: bool = True
