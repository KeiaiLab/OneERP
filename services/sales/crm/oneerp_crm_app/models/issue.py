"""이슈(Issue) 문서 모델 — 고객 지원 티켓."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class IssuePriority(StrEnum):
    """이슈 우선순위."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(StrEnum):
    """이슈 상태."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IssueCreate(BaseModel):
    """이슈 생성 요청 스키마."""

    subject: str
    description: str = ""
    customer_id: str = ""
    priority: IssuePriority = IssuePriority.MEDIUM
    assigned_to: str = ""


class IssueUpdate(BaseModel):
    """이슈 수정 요청 스키마."""

    subject: str | None = None
    description: str | None = None
    customer_id: str | None = None
    priority: IssuePriority | None = None
    assigned_to: str | None = None


class IssueResolve(BaseModel):
    """이슈 해결 요청 스키마."""

    resolution: str


class Issue(BaseDocument):
    """이슈 문서 — 고객 지원 티켓.

    naming prefix: ISS
    """

    subject: str = ""
    description: str = ""
    customer_id: str = ""
    priority: IssuePriority = IssuePriority.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    assigned_to: str = ""
    resolution: str = ""
