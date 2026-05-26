"""자동화 정의(AutomationDefinition) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AutomationDefinitionCreate(BaseModel):
    """자동화 정의 생성 요청 스키마."""

    name: str
    category: str = "general"
    is_active: bool = False


class AutomationDefinitionUpdate(BaseModel):
    """자동화 정의 수정 요청 스키마."""

    name: str | None = None
    category: str | None = None
    is_active: bool | None = None


class AutomationDefinition(BaseDocument):
    """자동화 정의 문서."""

    name: str = ""
    category: str = "general"
    is_active: bool = False
