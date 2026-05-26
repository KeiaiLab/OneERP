"""이익센터(ProfitCenter) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ProfitCenterCreate(BaseModel):
    """이익센터 생성 요청 스키마."""

    name: str
    parent_id: str = ""
    is_group: bool = False
    is_active: bool = True


class ProfitCenterUpdate(BaseModel):
    """이익센터 수정 요청 스키마."""

    name: str | None = None
    parent_id: str | None = None
    is_group: bool | None = None
    is_active: bool | None = None


class ProfitCenter(BaseDocument):
    """이익센터 문서."""

    name: str = ""
    parent_id: str = ""
    is_group: bool = False
    is_active: bool = True
