"""창고(Warehouse) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class Warehouse(BaseDocument):
    """창고 마스터 — 재고 보관 위치.

    naming prefix: WH
    """

    warehouse_name: str = Field(default="", description="창고명")
    warehouse_type: str = Field(default="stores", description="창고 유형")
    parent_warehouse: str | None = Field(default=None, description="상위 창고")
    is_group: bool = Field(default=False, description="그룹 여부")
    is_active: bool = Field(default=True, description="활성 여부")
    company: str = Field(default="", description="소속 회사")


class WarehouseCreate(BaseModel):
    """창고 생성 요청."""

    warehouse_name: str
    warehouse_type: str = "stores"
    parent_warehouse: str | None = None
    is_group: bool = False
    company: str = ""


class WarehouseUpdate(BaseModel):
    """창고 수정 요청."""

    warehouse_name: str | None = None
    warehouse_type: str | None = None
    parent_warehouse: str | None = None
    is_group: bool | None = None
    is_active: bool | None = None
