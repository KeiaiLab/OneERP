"""DashboardPublishPilotService — M3 platform/analytics."""

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


class DashboardPublishPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    publish_no: str = ""
    dashboard_id: str = ""
    audience: str = ""


class DashboardPublishSubmissionResult(ResponseDTO):
    id: str
    publish_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    dashboard_id: str


class DashboardPublishPilotService(SubmitMixinService):
    REPO_KEY = "dashboard_publish_pilot"
    DOC_CLASS = DashboardPublishPilotDoc
    RESULT_CLASS = DashboardPublishSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.ANL_001
