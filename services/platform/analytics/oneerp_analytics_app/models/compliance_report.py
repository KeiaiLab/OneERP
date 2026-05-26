"""컴플라이언스 보고서(ComplianceReport) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ComplianceReportStatus(StrEnum):
    """컴플라이언스 보고서 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"


class ComplianceReportCreate(BaseModel):
    """컴플라이언스 보고서 생성 요청 스키마."""

    report_name: str
    regulation: str = ""
    period: str = ""
    findings: int = 0
    is_compliant: bool = True


class ComplianceReportUpdate(BaseModel):
    """컴플라이언스 보고서 수정 요청 스키마."""

    report_name: str | None = None
    regulation: str | None = None
    period: str | None = None
    findings: int | None = None
    is_compliant: bool | None = None


class ComplianceReport(BaseDocument):
    """컴플라이언스 보고서 문서."""

    status: ComplianceReportStatus = Field(
        default=ComplianceReportStatus.DRAFT,
        description="컴플라이언스 보고서 상태",
    )
    report_name: str = ""
    regulation: str = ""
    period: str = ""
    findings: int = 0
    is_compliant: bool = True
