"""품목 속성(ItemAttribute) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ItemAttributeCreate(BaseModel):
    """품목 속성 생성 요청 스키마."""

    attribute_name: str
    attribute_values: list[str] = Field(default_factory=list)
    is_numeric: bool = False


class ItemAttributeUpdate(BaseModel):
    """품목 속성 수정 요청 스키마."""

    attribute_name: str | None = None
    attribute_values: list[str] | None = None
    is_numeric: bool | None = None


class ItemAttribute(BaseDocument):
    """품목 속성 문서."""

    attribute_name: str = ""
    attribute_values: list[str] = Field(default_factory=list)
    is_numeric: bool = False
