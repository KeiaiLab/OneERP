"""결제 게이트웨이(PaymentGateway) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PaymentGatewayStatus(StrEnum):
    """결제 게이트웨이 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class PaymentGatewayCreate(BaseModel):
    """결제 게이트웨이 생성 요청 스키마."""

    gateway_name: str
    provider: str = ""
    merchant_id: str = ""
    is_active: bool = True
    is_sandbox: bool = False


class PaymentGatewayUpdate(BaseModel):
    """결제 게이트웨이 수정 요청 스키마."""

    gateway_name: str | None = None
    provider: str | None = None
    merchant_id: str | None = None
    is_active: bool | None = None
    is_sandbox: bool | None = None


class PaymentGateway(BaseDocument):
    """결제 게이트웨이 문서."""

    status: PaymentGatewayStatus = Field(
        default=PaymentGatewayStatus.ACTIVE,
        description="결제 게이트웨이 상태",
    )
    gateway_name: str = ""
    provider: str = ""
    merchant_id: str = ""
    is_active: bool = True
    is_sandbox: bool = False
