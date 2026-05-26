"""ContractApprovalPilotService — M3 compliance/clm 파일럿."""

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


class ContractApprovalPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    contract_no: str = ""
    counterparty: str = ""
    contract_type: str = ""  # nda / msa / sow / order


class ContractApprovalSubmissionResult(ResponseDTO):
    id: str
    contract_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    contract_type: str


class ContractApprovalPilotService(SubmitMixinService):
    REPO_KEY = "contract_approval_pilot"
    DOC_CLASS = ContractApprovalPilotDoc
    RESULT_CLASS = ContractApprovalSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CLM_001
