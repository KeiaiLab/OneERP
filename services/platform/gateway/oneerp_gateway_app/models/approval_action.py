"""결재이력(ApprovalAction) 문서 모델 — 전자결재 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date, datetime


class ApprovalActionCreate(BaseModel):
    """결재이력 생성 요청 스키마."""

    approval_request: str
    action_type: str = "approve"
    actor: str = ""
    comment: str = ""
    action_date: date | None = None
    acted_at: datetime | None = None
    step: int = 0
    request_status: str = ""
    document_type: str = ""
    document_id: str = ""
    approval_type: str = "single"
    delegate_to: str = ""


class ApprovalAction(BaseDocument):
    """결재이력 문서 — 전자결재 결재 이력 로그.

    naming prefix: AA
    """

    approval_request: str = ""
    action_type: str = "approve"
    actor: str = ""
    comment: str = ""
    action_date: date | None = None
    acted_at: datetime | None = None
    step: int = 0
    request_status: str = ""
    document_type: str = ""
    document_id: str = ""
    approval_type: str = "single"
    delegate_to: str = ""


_APPROVAL_ACTION_TYPES = {
    "date": __import__("datetime").date,
    "datetime": __import__("datetime").datetime,
}

ApprovalActionCreate.model_rebuild(_types_namespace=_APPROVAL_ACTION_TYPES)
ApprovalAction.model_rebuild(_types_namespace=_APPROVAL_ACTION_TYPES)
