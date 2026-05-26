"""커스텀 보고서(CustomReport) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CustomReportCreate(BaseModel):
    """커스텀 보고서 생성 요청 스키마."""

    report_name: str
    report_type: str = ""
    data_source: str = ""
    query: str = ""
    is_public: bool = False


class CustomReportUpdate(BaseModel):
    """커스텀 보고서 수정 요청 스키마."""

    report_name: str | None = None
    report_type: str | None = None
    data_source: str | None = None
    query: str | None = None
    is_public: bool | None = None


class CustomReport(BaseDocument):
    """커스텀 보고서 문서."""

    report_name: str = ""
    report_type: str = ""
    data_source: str = ""
    query: str = ""
    is_public: bool = False
