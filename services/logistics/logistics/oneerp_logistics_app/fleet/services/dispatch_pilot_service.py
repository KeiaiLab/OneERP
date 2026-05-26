"""VehicleDispatchPilotService — M3 fleet 파일럿."""

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


class VehicleDispatchPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    dispatch_no: str = ""
    vehicle_id: str = ""
    driver_id: str = ""
    departure_at: str = ""


class VehicleDispatchSubmissionResult(ResponseDTO):
    id: str
    dispatch_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    vehicle_id: str


class VehicleDispatchPilotService(SubmitMixinService):
    REPO_KEY = "vehicle_dispatch_pilot"
    DOC_CLASS = VehicleDispatchPilotDoc
    RESULT_CLASS = VehicleDispatchSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.FLT_001
