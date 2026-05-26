"""ESG 공시(ESGDisclosure) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class ESGDisclosureCreate(BaseModel):
    """ESG 공시 생성 요청 스키마."""

    disclosure_code: str
    title: str
    disclosure_type: str = ""
    reporting_period: str = ""
    company: str = ""
    sustainability_report_id: str | None = None
    status: str = "draft"
    publication_date: datetime | None = None
    regulatory_body: str = ""


class ESGDisclosureUpdate(BaseModel):
    """ESG 공시 수정 요청 스키마."""

    disclosure_code: str | None = None
    title: str | None = None
    disclosure_type: str | None = None
    reporting_period: str | None = None
    company: str | None = None
    sustainability_report_id: str | None = None
    status: str | None = None
    publication_date: datetime | None = None
    regulatory_body: str | None = None


class ESGDisclosure(BaseDocument):
    """ESG 공시 문서."""

    disclosure_code: str = ""
    title: str = ""
    disclosure_type: str = ""
    reporting_period: str = ""
    company: str = ""
    sustainability_report_id: str | None = None
    status: str = "draft"
    publication_date: datetime | None = None
    regulatory_body: str = ""
