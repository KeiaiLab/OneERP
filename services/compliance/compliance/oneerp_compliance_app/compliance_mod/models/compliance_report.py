"""��플라이언스 보고서(ComplianceReport) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ReportType(StrEnum):
    """보고서 유형."""

    SOX = "sox"
    INTERNAL_AUDIT = "internal_audit"
    RISK_REVIEW = "risk_review"


class OverallRating(StrEnum):
    """종합 평가."""

    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNSATISFACTORY = "unsatisfactory"


class ReportStatus(StrEnum):
    """보고서 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"


class ComplianceReportCreate(BaseModel):
    """컴플���이언스 보고서 생성 요청 스키마."""

    report_type: ReportType
    period: str
    findings: list[dict[str, Any]]
    overall_rating: OverallRating
    prepared_by: str
    approved_by: str | None = None
    status: ReportStatus = ReportStatus.DRAFT
    company: str = ""


class ComplianceReportUpdate(BaseModel):
    """컴플라이언스 보고서 수정 요청 스키마."""

    report_type: ReportType | None = None
    period: str | None = None
    findings: list[dict[str, Any]] | None = None
    overall_rating: OverallRating | None = None
    prepared_by: str | None = None
    approved_by: str | None = None
    status: ReportStatus | None = None
    company: str | None = None


class ComplianceReport(BaseDocument):
    """컴플라이언스 보고서 문서."""

    report_type: ReportType = ReportType.INTERNAL_AUDIT
    period: str = ""
    findings: list[dict[str, Any]] | None = None
    overall_rating: OverallRating = OverallRating.SATISFACTORY
    prepared_by: str = ""
    approved_by: str | None = None
    status: ReportStatus = ReportStatus.DRAFT
    company: str = ""
