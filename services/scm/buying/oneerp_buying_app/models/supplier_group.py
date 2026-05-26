"""공급업체그룹(SupplierGroup) 마스터 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SupplierGroupCreate(BaseModel):
    """공급업체그룹 생성 요청 스키마."""

    group_name: str
    parent_group: str | None = None


class SupplierGroupUpdate(BaseModel):
    """공급업체그룹 수정 요청 스키마."""

    group_name: str | None = None
    parent_group: str | None = None


class SupplierGroup(BaseDocument):
    """공급업체그룹 마스터 — 공급업체를 그룹으로 분류.

    naming prefix: SGR
    """

    group_name: str = ""
    parent_group: str | None = None
