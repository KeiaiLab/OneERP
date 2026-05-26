"""고객그룹(Customer Group) 마스터 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CustomerGroupCreate(BaseModel):
    """고객그룹 생성 요청 스키마."""

    group_name: str
    parent_group: str | None = None
    default_price_list: str = ""


class CustomerGroupUpdate(BaseModel):
    """고객그룹 수정 요청 스키마."""

    group_name: str | None = None
    parent_group: str | None = None
    default_price_list: str | None = None


class CustomerGroup(BaseDocument):
    """고객그룹 마스터 — 고객 분류 체계.

    naming prefix: CGR
    """

    group_name: str = ""
    parent_group: str | None = None
    default_price_list: str = ""
