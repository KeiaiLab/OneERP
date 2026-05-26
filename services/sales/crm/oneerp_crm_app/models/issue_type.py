"""이슈유형(IssueType) 문서 모델 — Support 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class IssueTypeCreate(BaseModel):
    """이슈유형 생성 요청 스키마."""

    issue_type_name: str
    description: str = ""
    priority: str = "medium"


class IssueTypeUpdate(BaseModel):
    """이슈유형 수정 요청 스키마."""

    issue_type_name: str | None = None
    description: str | None = None
    priority: str | None = None


class IssueType(BaseDocument):
    """이슈유형 문서 — Support 이슈유형 마스터.

    naming prefix: ISTP
    """

    issue_type_name: str = ""
    description: str = ""
    priority: str = "medium"
