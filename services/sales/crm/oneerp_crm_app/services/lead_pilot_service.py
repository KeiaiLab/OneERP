"""LeadPilotService — M3 crm 파일럿."""

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


class LeadPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    lead_no: str = ""
    company_name: str = ""
    stage: str = ""  # new / qualified / proposal / closed_won / closed_lost


class LeadSubmissionResult(ResponseDTO):
    id: str
    lead_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    stage: str


class LeadPilotService(SubmitMixinService):
    REPO_KEY = "lead_pilot"
    DOC_CLASS = LeadPilotDoc
    RESULT_CLASS = LeadSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CRM_001
