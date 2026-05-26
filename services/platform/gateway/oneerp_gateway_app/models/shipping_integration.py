"""배송 연동(ShippingIntegration) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ShippingIntegrationStatus(StrEnum):
    """배송 연동 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class ShippingIntegrationCreate(BaseModel):
    """배송 연동 생성 요청 스키마."""

    carrier_name: str
    api_endpoint: str = ""
    account_id: str = ""
    is_active: bool = True


class ShippingIntegrationUpdate(BaseModel):
    """배송 연동 수정 요청 스키마."""

    carrier_name: str | None = None
    api_endpoint: str | None = None
    account_id: str | None = None
    is_active: bool | None = None


class ShippingIntegration(BaseDocument):
    """배송 연동 문서."""

    status: ShippingIntegrationStatus = Field(
        default=ShippingIntegrationStatus.ACTIVE,
        description="배송 연동 상태",
    )
    carrier_name: str = ""
    api_endpoint: str = ""
    account_id: str = ""
    is_active: bool = True
