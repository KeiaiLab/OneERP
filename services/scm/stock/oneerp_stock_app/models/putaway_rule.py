"""적치 규칙(PutawayRule) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PutawayRuleCreate(BaseModel):
    """적치 규칙 생성 요청 스키마."""

    item_code: str
    warehouse_id: str
    target_bin: str = ""
    priority: int = 0
    is_active: bool = True


class PutawayRuleUpdate(BaseModel):
    """적치 규칙 수정 요청 스키마."""

    item_code: str | None = None
    warehouse_id: str | None = None
    target_bin: str | None = None
    priority: int | None = None
    is_active: bool | None = None


class PutawayRule(BaseDocument):
    """적치 규칙 문서."""

    item_code: str = ""
    warehouse_id: str = ""
    target_bin: str = ""
    priority: int = 0
    is_active: bool = True
