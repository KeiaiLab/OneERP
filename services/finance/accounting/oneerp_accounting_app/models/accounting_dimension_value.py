"""회계 차원 값(AccountingDimensionValue) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AccountingDimensionValueCreate(BaseModel):
    """회계 차원 값 생성 요청 스키마."""

    dimension_id: str
    value_name: str
    is_active: bool = True


class AccountingDimensionValueUpdate(BaseModel):
    """회계 차원 값 수정 요청 스키마."""

    dimension_id: str | None = None
    value_name: str | None = None
    is_active: bool | None = None


class AccountingDimensionValue(BaseDocument):
    """회계 차원 값 문서."""

    dimension_id: str = ""
    value_name: str = ""
    is_active: bool = True
