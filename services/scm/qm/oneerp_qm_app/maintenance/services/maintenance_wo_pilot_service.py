"""MaintenanceWorkOrderPilotService — M3 maintenance 파일럿."""

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


class MaintenanceWOPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    mwo_no: str = ""
    asset_id: str = ""
    maintenance_type: str = ""  # preventive / corrective / predictive


class MaintenanceWOSubmissionResult(ResponseDTO):
    id: str
    mwo_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    maintenance_type: str


class MaintenanceWOPilotService(SubmitMixinService):
    REPO_KEY = "maintenance_wo_pilot"
    DOC_CLASS = MaintenanceWOPilotDoc
    RESULT_CLASS = MaintenanceWOSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.MNT_001
