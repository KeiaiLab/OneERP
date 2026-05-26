"""단위 변환(UomConversion) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class UomConversionCreate(BaseModel):
    """단위 변환 생성 요청 스키마."""

    from_uom: str
    to_uom: str
    conversion_factor: Decimal = Decimal(1)


class UomConversionUpdate(BaseModel):
    """단위 변환 수정 요청 스키마."""

    from_uom: str | None = None
    to_uom: str | None = None
    conversion_factor: Decimal | None = None


class UomConversion(BaseDocument):
    """단위 변환 문서."""

    from_uom: str = ""
    to_uom: str = ""
    conversion_factor: Decimal = Decimal(1)
