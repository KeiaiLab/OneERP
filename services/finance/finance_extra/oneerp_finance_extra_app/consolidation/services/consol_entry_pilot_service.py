"""ConsolEntryPilotService — M3 consolidation 파일럿."""

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


class ConsolEntryPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    entry_no: str = ""
    period: str = ""  # YYYY-MM
    consol_type: str = ""  # equity / intercompany / dividend


class ConsolEntrySubmissionResult(ResponseDTO):
    id: str
    entry_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    consol_type: str


class ConsolEntryPilotService(SubmitMixinService):
    REPO_KEY = "consol_entry_pilot"
    DOC_CLASS = ConsolEntryPilotDoc
    RESULT_CLASS = ConsolEntrySubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CSL_001
