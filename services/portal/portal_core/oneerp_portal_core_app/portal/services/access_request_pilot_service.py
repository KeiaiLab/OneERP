"""AccessRequestPilotService — M3 portal 파일럿."""

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


class AccessRequestPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    request_no: str = ""
    requester_id: str = ""
    target_resource: str = ""  # role / module / data scope


class AccessRequestSubmissionResult(ResponseDTO):
    id: str
    request_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    target_resource: str


class AccessRequestPilotService(SubmitMixinService):
    REPO_KEY = "access_request_pilot"
    DOC_CLASS = AccessRequestPilotDoc
    RESULT_CLASS = AccessRequestSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.PRT_001
