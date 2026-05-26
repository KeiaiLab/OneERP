"""고객 포털(CustomerPortal) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CustomerPortalStatus(StrEnum):
    """고객 포털 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class CustomerPortalCreate(BaseModel):
    """고객 포털 생성 요청 스키마."""

    customer_id: str
    portal_url: str = ""
    features: list[str] = Field(default_factory=list)
    is_active: bool = True


class CustomerPortalUpdate(BaseModel):
    """고객 포털 수정 요청 스키마."""

    customer_id: str | None = None
    portal_url: str | None = None
    features: list[str] | None = None
    is_active: bool | None = None


class CustomerPortal(BaseDocument):
    """고객 포털 문서."""

    status: CustomerPortalStatus = Field(
        default=CustomerPortalStatus.ACTIVE,
        description="고객 포털 상태",
    )
    customer_id: str = ""
    portal_url: str = ""
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
