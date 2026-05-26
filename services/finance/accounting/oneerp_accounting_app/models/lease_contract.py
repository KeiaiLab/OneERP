"""리스 계약(LeaseContract) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LeaseContractStatus(StrEnum):
    """리스 계약 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class LeaseContractCreate(BaseModel):
    """리스 계약 생성 요청 스키마."""

    model_config = {"populate_by_name": True}

    lessee: str
    lessor: str
    asset_description: str = ""
    lease_start: date | None = None
    lease_end: date | None = None
    monthly_payment: Decimal = Decimal(0)
    contract_value: Decimal = Field(default=Decimal(0), alias="total_value")


class LeaseContractUpdate(BaseModel):
    """리스 계약 수정 요청 스키마."""

    model_config = {"populate_by_name": True}

    lessee: str | None = None
    lessor: str | None = None
    asset_description: str | None = None
    lease_start: date | None = None
    lease_end: date | None = None
    monthly_payment: Decimal | None = None
    contract_value: Decimal | None = Field(default=None, alias="total_value")


class LeaseContract(BaseDocument):
    """리스 계약 문서."""

    status: LeaseContractStatus = Field(
        default=LeaseContractStatus.DRAFT,
        description="리스 계약 상태",
    )
    lessee: str = ""
    lessor: str = ""
    asset_description: str = ""
    lease_start: date | None = None
    lease_end: date | None = None
    monthly_payment: Decimal = Decimal(0)
    contract_value: Decimal = Field(default=Decimal(0), alias="total_value")
