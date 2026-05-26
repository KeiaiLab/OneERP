"""RentalContractPilotService — M3 sales/rental."""

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


class RentalContractPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    contract_no: str = ""
    asset_id: str = ""
    customer_id: str = ""


class RentalContractSubmissionResult(ResponseDTO):
    id: str
    contract_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    asset_id: str


class RentalContractPilotService(SubmitMixinService):
    REPO_KEY = "rental_contract_pilot"
    DOC_CLASS = RentalContractPilotDoc
    RESULT_CLASS = RentalContractSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.RNT_001
