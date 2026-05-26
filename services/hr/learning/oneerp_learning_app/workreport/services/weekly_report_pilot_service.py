"""WeeklyReportPilotService — M3 workreport 파일럿."""

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


class WeeklyReportPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    report_no: str = ""
    employee_id: str = ""
    week_of: str = ""  # YYYY-Www


class WeeklyReportSubmissionResult(ResponseDTO):
    id: str
    report_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    week_of: str


class WeeklyReportPilotService(SubmitMixinService):
    REPO_KEY = "weekly_report_pilot"
    DOC_CLASS = WeeklyReportPilotDoc
    RESULT_CLASS = WeeklyReportSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.WRP_001
