"""재무비율 분석(FinancialRatioReport) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class FinancialRatioReportStatus(StrEnum):
    """재무비율 분석 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class FinancialRatioReportCreate(BaseModel):
    """재무비율 분석 생성 요청 스키마."""

    report_name: str
    period: str = ""
    current_ratio: Decimal = Decimal(0)
    debt_ratio: Decimal = Decimal(0)
    roe: Decimal = Decimal(0)
    roa: Decimal = Decimal(0)


class FinancialRatioReportUpdate(BaseModel):
    """재무비율 분석 수정 요청 스키마."""

    report_name: str | None = None
    period: str | None = None
    current_ratio: Decimal | None = None
    debt_ratio: Decimal | None = None
    roe: Decimal | None = None
    roa: Decimal | None = None


class FinancialRatioReport(BaseDocument):
    """재무비율 분석 문서."""

    status: FinancialRatioReportStatus = Field(
        default=FinancialRatioReportStatus.DRAFT,
        description="재무비율 분석 상태",
    )
    report_name: str = ""
    period: str = ""
    current_ratio: Decimal = Decimal(0)
    debt_ratio: Decimal = Decimal(0)
    roe: Decimal = Decimal(0)
    roa: Decimal = Decimal(0)
