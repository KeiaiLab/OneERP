"""HS 코드 분류 모델 — 품목별 HS 코드 분류와 관세율 관리."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class HSClassificationCreate(BaseModel):
    """HS 분류 생성 요청 스키마."""

    item_code: str
    item_name: str = ""
    hs_code: str
    hs_description: str = ""
    country_code: str = "KR"
    duty_rate: Decimal = Decimal(0)
    preferential_rate: Decimal | None = None
    agreement_code: str = ""


class HSClassificationUpdate(BaseModel):
    """HS 분류 수정 요청 스키마."""

    hs_code: str | None = None
    hs_description: str | None = None
    duty_rate: Decimal | None = None
    preferential_rate: Decimal | None = None
    agreement_code: str | None = None
    is_active: bool | None = None


class HSClassification(BaseDocument):
    """HS 분류 문서 — 품목의 HS 코드와 관세율 정보를 저장한다."""

    item_code: str = ""
    item_name: str = ""
    hs_code: str = ""
    hs_description: str = ""
    country_code: str = "KR"
    duty_rate: Decimal = Decimal(0)
    preferential_rate: Decimal | None = None
    agreement_code: str = ""
    is_active: bool = True
