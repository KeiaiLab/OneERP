"""품목변형(ItemVariant) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ItemVariant(BaseDocument):
    """품목변형 마스터 — 품목의 속성별 변형.

    naming prefix: IVR
    """

    item_code: str = ""
    variant_of: str = ""
    attributes: dict = {}


class ItemVariantCreate(BaseModel):
    """품목변형 생성 요청."""

    item_code: str = ""
    variant_of: str = ""
    attributes: dict = {}


class ItemVariantUpdate(BaseModel):
    """품목변형 수정 요청."""

    item_code: str | None = None
    variant_of: str | None = None
    attributes: dict | None = None
