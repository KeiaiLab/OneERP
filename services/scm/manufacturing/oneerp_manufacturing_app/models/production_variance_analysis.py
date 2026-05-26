"""생산 차이 분석(ProductionVarianceAnalysis) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class ProductionVarianceAnalysisStatus(StrEnum):
    """생산 차이 분석 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class ProductionVarianceAnalysisCreate(BaseModel):
    """생산 차이 분석 생성 요청 스키마."""

    work_order_id: str
    planned_cost: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)
    variance_percentage: Decimal = Decimal(0)
    analysis_date: date | None = None


class ProductionVarianceAnalysisUpdate(BaseModel):
    """생산 차이 분석 수정 요청 스키마."""

    work_order_id: str | None = None
    planned_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    variance: Decimal | None = None
    variance_percentage: Decimal | None = None
    analysis_date: date | None = None


class ProductionVarianceAnalysis(BaseDocument):
    """생산 차이 분석 문서."""

    status: ProductionVarianceAnalysisStatus = Field(
        default=ProductionVarianceAnalysisStatus.DRAFT,
        description="생산 차이 분석 상태",
    )
    work_order_id: str = ""
    planned_cost: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)
    variance_percentage: Decimal = Decimal(0)
    analysis_date: date | None = None
