"""IncidentReportPilotService — M3 ehs 파일럿."""

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


class IncidentReportPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    incident_no: str = ""
    location: str = ""
    severity: str = ""  # near_miss / minor / major / critical


class IncidentReportSubmissionResult(ResponseDTO):
    id: str
    incident_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    severity: str


class IncidentReportPilotService(SubmitMixinService):
    REPO_KEY = "incident_report_pilot"
    DOC_CLASS = IncidentReportPilotDoc
    RESULT_CLASS = IncidentReportSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.EHS_001
