"""ESG 공시(ESGDisclosure) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ESGDisclosureStatus(StrEnum):
    """ESG 공시 상태."""

    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"


class ESGDisclosureCreate(BaseModel):
    """ESG 공시 생성 요청 스키마."""

    disclosure_title: str
    framework: str = ""
    period: str = ""
    content: str = ""
    is_published: bool = False


class ESGDisclosureUpdate(BaseModel):
    """ESG 공시 수정 요청 스키마."""

    disclosure_title: str | None = None
    framework: str | None = None
    period: str | None = None
    content: str | None = None
    is_published: bool | None = None


class ESGDisclosure(BaseDocument):
    """ESG 공시 문서."""

    status: ESGDisclosureStatus = Field(
        default=ESGDisclosureStatus.DRAFT,
        description="ESG 공시 상태",
    )
    disclosure_title: str = ""
    framework: str = ""
    period: str = ""
    content: str = ""
    is_published: bool = False
