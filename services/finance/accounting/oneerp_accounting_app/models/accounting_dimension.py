"""회계 차원(AccountingDimension) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AccountingDimensionCreate(BaseModel):
    """회계 차원 생성 요청 스키마."""

    dimension_name: str
    is_mandatory: bool = False
    is_active: bool = True


class AccountingDimensionUpdate(BaseModel):
    """회계 차원 수정 요청 스키마."""

    dimension_name: str | None = None
    is_mandatory: bool | None = None
    is_active: bool | None = None


class AccountingDimension(BaseDocument):
    """회계 차원 문서."""

    dimension_name: str = ""
    is_mandatory: bool = False
    is_active: bool = True
