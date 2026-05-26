"""InspectionPilotService — M3 quality 파일럿."""

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


class InspectionPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    inspection_no: str = ""
    item_code: str = ""
    result: str = ""  # pass / fail / hold


class InspectionSubmissionResult(ResponseDTO):
    id: str
    inspection_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    result: str


class InspectionPilotService(SubmitMixinService):
    REPO_KEY = "inspection_pilot"
    DOC_CLASS = InspectionPilotDoc
    RESULT_CLASS = InspectionSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.QC_001
