"""품목그룹(ItemGroup) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ItemGroup(BaseDocument):
    """품목그룹 마스터 — 품목 분류 체계.

    naming prefix: IG
    """

    group_name: str = ""
    parent_group: str | None = None
    is_group: bool = False


class ItemGroupCreate(BaseModel):
    """품목그룹 생성 요청."""

    group_name: str = ""
    parent_group: str | None = None
    is_group: bool = False


class ItemGroupUpdate(BaseModel):
    """품목그룹 수정 요청."""

    group_name: str | None = None
    parent_group: str | None = None
    is_group: bool | None = None
