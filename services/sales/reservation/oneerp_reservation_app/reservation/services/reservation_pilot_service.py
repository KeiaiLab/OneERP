"""ReservationPilotService — M3 sales/reservation."""

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


class ReservationPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    reservation_no: str = ""
    resource_id: str = ""
    starts_at: str = ""


class ReservationSubmissionResult(ResponseDTO):
    id: str
    reservation_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    resource_id: str


class ReservationPilotService(SubmitMixinService):
    REPO_KEY = "reservation_pilot"
    DOC_CLASS = ReservationPilotDoc
    RESULT_CLASS = ReservationSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.RSV_001
