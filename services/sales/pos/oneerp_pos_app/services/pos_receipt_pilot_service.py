"""PosReceiptPilotService — M3 sales/pos.

POS 전용 ERR 코드(POS_001)는 차후 ErrorCatalog 확장 시 도입.
당분간 ERR.CMN_VALIDATION 사용.
"""

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


class PosReceiptPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    receipt_no: str = ""
    pos_id: str = ""
    payment_method: str = ""


class PosReceiptSubmissionResult(ResponseDTO):
    id: str
    receipt_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    payment_method: str


class PosReceiptPilotService(SubmitMixinService):
    REPO_KEY = "pos_receipt_pilot"
    DOC_CLASS = PosReceiptPilotDoc
    RESULT_CLASS = PosReceiptSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CMN_VALIDATION
