"""결재라인(ApprovalLine) 문서 모델 — 전자결재 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ApprovalLineCreate(BaseModel):
    """결재라인 생성 요청 스키마."""

    template: str
    sequence: int = 0
    approver_role: str = ""
    approver: str = ""
    approval_type: str = "single"
    pre_approval_roles: list[str] = []
    condition: str = ""


class ApprovalLineUpdate(BaseModel):
    """결재라인 수정 요청 스키마."""

    template: str | None = None
    sequence: int | None = None
    approver_role: str | None = None
    approver: str | None = None
    approval_type: str | None = None
    pre_approval_roles: list[str] | None = None
    condition: str | None = None


class ApprovalLine(BaseDocument):
    """결재라인 문서 — 전자결재 결재 라인 마스터.

    naming prefix: AL
    """

    template: str = ""
    sequence: int = 0
    approver_role: str = ""
    approver: str = ""
    approval_type: str = "single"
    pre_approval_roles: list[str] = []
    condition: str = ""
