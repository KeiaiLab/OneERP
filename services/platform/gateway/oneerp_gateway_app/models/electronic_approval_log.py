"""전자결재 로그(ElectronicApprovalLog) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ElectronicApprovalLogCreate(BaseModel):
    """전자결재 로그 생성 요청 스키마."""

    approval_request_id: str
    action: str = ""
    actor: str = ""
    action_date: date | None = None
    comment: str = ""


class ElectronicApprovalLogUpdate(BaseModel):
    """전자결재 로그 수정 요청 스키마."""

    approval_request_id: str | None = None
    action: str | None = None
    actor: str | None = None
    action_date: date | None = None
    comment: str | None = None


class ElectronicApprovalLog(BaseDocument):
    """전자결재 로그 문서."""

    approval_request_id: str = ""
    action: str = ""
    actor: str = ""
    action_date: date | None = None
    comment: str = ""


_ELECTRONIC_APPROVAL_LOG_TYPES = {"date": __import__("datetime").date}

ElectronicApprovalLogCreate.model_rebuild(_types_namespace=_ELECTRONIC_APPROVAL_LOG_TYPES)
ElectronicApprovalLogUpdate.model_rebuild(_types_namespace=_ELECTRONIC_APPROVAL_LOG_TYPES)
ElectronicApprovalLog.model_rebuild(_types_namespace=_ELECTRONIC_APPROVAL_LOG_TYPES)
