"""세그먼트 보고서(SegmentReport) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SegmentReportStatus(StrEnum):
    """세그먼트 보고서 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class SegmentReportCreate(BaseModel):
    """세그먼트 보고서 생성 요청 스키마."""

    segment_name: str
    period: str = ""
    revenue: Decimal = Decimal(0)
    expenses: Decimal = Decimal(0)
    profit: Decimal = Decimal(0)


class SegmentReportUpdate(BaseModel):
    """세그먼트 보고서 수정 요청 스키마."""

    segment_name: str | None = None
    period: str | None = None
    revenue: Decimal | None = None
    expenses: Decimal | None = None
    profit: Decimal | None = None


class SegmentReport(BaseDocument):
    """세그먼트 보고서 문서."""

    status: SegmentReportStatus = Field(
        default=SegmentReportStatus.DRAFT,
        description="세그먼트 보고서 상태",
    )
    segment_name: str = ""
    period: str = ""
    revenue: Decimal = Decimal(0)
    expenses: Decimal = Decimal(0)
    profit: Decimal = Decimal(0)
