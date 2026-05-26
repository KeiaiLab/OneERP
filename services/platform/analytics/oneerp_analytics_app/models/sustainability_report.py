"""지속가능성 보고서(SustainabilityReport) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SustainabilityReportStatus(StrEnum):
    """지속가능성 보고서 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"


class SustainabilityReportCreate(BaseModel):
    """지속가능성 보고서 생성 요청 스키마."""

    report_title: str
    period: str = ""
    framework: str = ""
    content: str = ""
    is_published: bool = False


class SustainabilityReportUpdate(BaseModel):
    """지속가능성 보고서 수정 요청 스키마."""

    report_title: str | None = None
    period: str | None = None
    framework: str | None = None
    content: str | None = None
    is_published: bool | None = None


class SustainabilityReport(BaseDocument):
    """지속가능성 보고서 문서."""

    status: SustainabilityReportStatus = Field(
        default=SustainabilityReportStatus.DRAFT,
        description="지속가능성 보고서 상태",
    )
    report_title: str = ""
    period: str = ""
    framework: str = ""
    content: str = ""
    is_published: bool = False
