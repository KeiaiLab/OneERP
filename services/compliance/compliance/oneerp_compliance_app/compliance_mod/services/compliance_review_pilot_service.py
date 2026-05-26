"""ComplianceReviewPilotService — M3 compliance/compliance."""

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


class ComplianceReviewPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    review_no: str = ""
    regulation: str = ""
    severity: str = ""


class ComplianceReviewSubmissionResult(ResponseDTO):
    id: str
    review_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    regulation: str


class ComplianceReviewPilotService(SubmitMixinService):
    REPO_KEY = "compliance_review_pilot"
    DOC_CLASS = ComplianceReviewPilotDoc
    RESULT_CLASS = ComplianceReviewSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CMP_001
