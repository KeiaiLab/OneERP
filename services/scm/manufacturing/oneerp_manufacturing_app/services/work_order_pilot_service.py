"""WorkOrderPilotService — M3 manufacturing 파일럿."""

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


class WorkOrderPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    work_order_no: str = ""
    item_code: str = ""
    qty: int = 0


class WorkOrderSubmissionResult(ResponseDTO):
    id: str
    work_order_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    item_code: str


class WorkOrderPilotService(SubmitMixinService):
    REPO_KEY = "work_order_pilot"
    DOC_CLASS = WorkOrderPilotDoc
    RESULT_CLASS = WorkOrderSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.MFG_001
