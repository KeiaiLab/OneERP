"""EcommerceOrderPilotService — M3 sales/ecommerce."""

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


class EcommerceOrderPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    order_no: str = ""
    customer_id: str = ""
    total_amount: int = 0


class EcommerceOrderSubmissionResult(ResponseDTO):
    id: str
    order_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    total_amount: int


class EcommerceOrderPilotService(SubmitMixinService):
    REPO_KEY = "ecommerce_order_pilot"
    DOC_CLASS = EcommerceOrderPilotDoc
    RESULT_CLASS = EcommerceOrderSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.ECM_001
