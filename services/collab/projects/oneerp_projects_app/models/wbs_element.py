"""WBS 요소(WbsElement) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WbsElementCreate(BaseModel):
    """WBS 요소 생성 요청 스키마."""

    project_id: str
    element_code: str = ""
    element_name: str = ""
    parent_id: str = ""
    level: int = 0
    budget: Decimal = Decimal(0)


class WbsElementUpdate(BaseModel):
    """WBS 요소 수정 요청 스키마."""

    project_id: str | None = None
    element_code: str | None = None
    element_name: str | None = None
    parent_id: str | None = None
    level: int | None = None
    budget: Decimal | None = None


class WbsElement(BaseDocument):
    """WBS 요소 문서."""

    project_id: str = ""
    element_code: str = ""
    element_name: str = ""
    parent_id: str = ""
    level: int = 0
    budget: Decimal = Decimal(0)
