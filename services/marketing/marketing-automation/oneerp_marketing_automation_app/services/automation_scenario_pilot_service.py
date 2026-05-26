"""AutomationScenarioPilotService — M3 marketing/marketing-automation."""

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


class AutomationScenarioPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    scenario_no: str = ""
    name: str = ""
    trigger_event: str = ""


class AutomationScenarioSubmissionResult(ResponseDTO):
    id: str
    scenario_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    name: str


class AutomationScenarioPilotService(SubmitMixinService):
    REPO_KEY = "automation_scenario_pilot"
    DOC_CLASS = AutomationScenarioPilotDoc
    RESULT_CLASS = AutomationScenarioSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.MAU_001
