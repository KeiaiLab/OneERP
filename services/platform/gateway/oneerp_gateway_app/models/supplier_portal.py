"""공급사 포털(SupplierPortal) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SupplierPortalStatus(StrEnum):
    """공급사 포털 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class SupplierPortalCreate(BaseModel):
    """공급사 포털 생성 요청 스키마."""

    supplier_id: str
    portal_url: str = ""
    features: list[str] = Field(default_factory=list)
    is_active: bool = True


class SupplierPortalUpdate(BaseModel):
    """공급사 포털 수정 요청 스키마."""

    supplier_id: str | None = None
    portal_url: str | None = None
    features: list[str] | None = None
    is_active: bool | None = None


class SupplierPortal(BaseDocument):
    """공급사 포털 문서."""

    status: SupplierPortalStatus = Field(
        default=SupplierPortalStatus.ACTIVE,
        description="공급사 포털 상태",
    )
    supplier_id: str = ""
    portal_url: str = ""
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
