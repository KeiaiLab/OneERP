"""코스트센터(Cost Center) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CostCenterCreate(BaseModel):
    """코스트센터 생성 요청 스키마."""

    cost_center_name: str
    parent_cost_center: str | None = None
    is_group: bool = False
    company: str = ""


class CostCenterUpdate(BaseModel):
    """코스트센터 수정 요청 스키마."""

    cost_center_name: str | None = None
    parent_cost_center: str | None = None
    is_group: bool | None = None
    company: str | None = None


class CostCenter(BaseDocument):
    """코스트센터 문서 — 비용 배분 단위.

    naming prefix: CC
    """

    cost_center_name: str = ""
    parent_cost_center: str | None = None
    is_group: bool = False
    company: str = ""
