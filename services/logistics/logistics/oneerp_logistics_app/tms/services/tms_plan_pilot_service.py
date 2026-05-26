"""TMSPlanPilotService — M3 logistics/tms."""

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


class TMSPlanPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    plan_no: str = ""
    route: str = ""
    carrier: str = ""


class TMSPlanSubmissionResult(ResponseDTO):
    id: str
    plan_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    route: str


class TMSPlanPilotService(SubmitMixinService):
    REPO_KEY = "tms_plan_pilot"
    DOC_CLASS = TMSPlanPilotDoc
    RESULT_CLASS = TMSPlanSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.TMS_001
