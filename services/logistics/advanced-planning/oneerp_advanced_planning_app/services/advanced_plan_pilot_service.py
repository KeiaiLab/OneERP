"""AdvancedPlanPilotService — M3 logistics/advanced-planning."""

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


class AdvancedPlanPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    plan_no: str = ""
    horizon: str = ""
    plan_type: str = ""


class AdvancedPlanSubmissionResult(ResponseDTO):
    id: str
    plan_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    plan_type: str


class AdvancedPlanPilotService(SubmitMixinService):
    REPO_KEY = "advanced_plan_pilot"
    DOC_CLASS = AdvancedPlanPilotDoc
    RESULT_CLASS = AdvancedPlanSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.APL_001
