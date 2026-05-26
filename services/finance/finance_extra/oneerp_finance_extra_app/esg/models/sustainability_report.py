"""지속가능성 보고서(SustainabilityReport) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class SustainabilityReportCreate(BaseModel):
    """지속가능성 보고서 생성 요청 스키마."""

    report_code: str
    title: str
    reporting_year: int = 0
    company: str = ""
    scope_1_emissions: Decimal = Decimal(0)
    scope_2_emissions: Decimal = Decimal(0)
    scope_3_emissions: Decimal = Decimal(0)
    social_metrics: dict[str, Any] = {}
    governance_metrics: dict[str, Any] = {}
    status: str = "draft"
    published_date: datetime | None = None


class SustainabilityReportUpdate(BaseModel):
    """지속가능성 보고서 수정 요청 스키마."""

    report_code: str | None = None
    title: str | None = None
    reporting_year: int | None = None
    company: str | None = None
    scope_1_emissions: Decimal | None = None
    scope_2_emissions: Decimal | None = None
    scope_3_emissions: Decimal | None = None
    social_metrics: dict[str, Any] | None = None
    governance_metrics: dict[str, Any] | None = None
    status: str | None = None
    published_date: datetime | None = None


class SustainabilityReport(BaseDocument):
    """지속가능성 보고서 문서."""

    report_code: str = ""
    title: str = ""
    reporting_year: int = 0
    company: str = ""
    scope_1_emissions: Decimal = Decimal(0)
    scope_2_emissions: Decimal = Decimal(0)
    scope_3_emissions: Decimal = Decimal(0)
    social_metrics: dict[str, Any] = {}
    governance_metrics: dict[str, Any] = {}
    status: str = "draft"
    published_date: datetime | None = None
