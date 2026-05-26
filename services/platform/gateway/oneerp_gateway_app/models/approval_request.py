"""결재요청(ApprovalRequest) 문서 모델 — 전자결재 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class ApprovalLineEmbed(BaseModel):
    """임베디드 결재 라인 — ApprovalRequest 내 각 결재 단계 상태.

    step: 단계 번호
    approver: 결재자 ID
    approver_role: 결재자 역할
    status: pending | approved | rejected | delegated | skipped
    comment: 코멘트
    acted_at: 처리 일시
    approval_type: 결재 유형 (single | consensus)
    pre_approval_roles: 전결 가능 역할 목록
    """

    step: int
    approver: str
    approver_role: str = ""
    status: str = "pending"
    comment: str = ""
    acted_at: datetime | None = None
    approval_type: str = "single"
    pre_approval_roles: list[str] = []


class ApprovalRequestCreate(BaseModel):
    """결재요청 생성 요청 스키마."""

    document_type: str
    document_id: str
    requester: str
    status: str = "pending"
    current_step: int = 1
    approval_lines: list[ApprovalLineEmbed] = []


class ApprovalRequestUpdate(BaseModel):
    """결재요청 수정 요청 스키마."""

    document_type: str | None = None
    document_id: str | None = None
    requester: str | None = None
    status: str | None = None
    current_step: int | None = None
    approval_lines: list[ApprovalLineEmbed] | None = None


class ApprovalRequest(BaseDocument):
    """결재요청 문서 — 전자결재 결재 요청 트랜잭션.

    naming prefix: AR
    """

    document_type: str = ""
    document_id: str = ""
    requester: str = ""
    status: str = "pending"
    current_step: int = 1
    approval_lines: list[ApprovalLineEmbed] = []


_APPROVAL_REQUEST_TYPES = {
    "datetime": __import__("datetime").datetime,
}

ApprovalLineEmbed.model_rebuild(_types_namespace=_APPROVAL_REQUEST_TYPES)
ApprovalRequestCreate.model_rebuild(_types_namespace=_APPROVAL_REQUEST_TYPES)
ApprovalRequestUpdate.model_rebuild(_types_namespace=_APPROVAL_REQUEST_TYPES)
ApprovalRequest.model_rebuild(_types_namespace=_APPROVAL_REQUEST_TYPES)
