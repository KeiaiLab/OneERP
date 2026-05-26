"""운송비 배부(LandedCostVoucherTms) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LandedCostVoucherTMSStatus(StrEnum):
    """운송비 배부 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class LandedCostVoucherTmsCreate(BaseModel):
    """운송비 배부 생성 요청 스키마."""

    shipment_id: str = ""
    total_landed_cost: Decimal = Decimal(0)
    allocation_method: str = ""
    posting_date: date | None = None


class LandedCostVoucherTmsUpdate(BaseModel):
    """운송비 배부 수정 요청 스키마."""

    shipment_id: str | None = None
    total_landed_cost: Decimal | None = None
    allocation_method: str | None = None
    posting_date: date | None = None


class LandedCostVoucherTMS(BaseDocument):
    """운송비 배부 문서."""

    status: LandedCostVoucherTMSStatus = Field(
        default=LandedCostVoucherTMSStatus.DRAFT,
        description="운송비 배부 상태",
    )
    shipment_id: str = ""
    total_landed_cost: Decimal = Decimal(0)
    allocation_method: str = ""
    posting_date: date | None = None
