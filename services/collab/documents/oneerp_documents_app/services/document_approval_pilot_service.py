"""DocumentApprovalPilotService — M3 collab/documents 파일럿."""

from __future__ import annotations

from oneerp_core.document import (
    ApprovalMixin,
    ApprovalStatus,
    BaseDocument,
    DocStatus,
    SubmitTransitionMixin,
)
from oneerp_core.dto import ResponseDTO
from oneerp_core.error_catalog import ERR
from oneerp_core.service_base import SubmitMixinService


class DocumentApprovalPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    request_no: str = ""
    document_id: str = ""
    requester_id: str = ""


class DocumentApprovalSubmissionResult(ResponseDTO):
    id: str
    request_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    document_id: str


class DocumentApprovalPilotService(SubmitMixinService):
    REPO_KEY = "document_approval_pilot"
    DOC_CLASS = DocumentApprovalPilotDoc
    RESULT_CLASS = DocumentApprovalSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.DOC_001
