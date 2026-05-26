"""ExpenseClaimService — M3 Wave B2 경비 청구 파일럿.

SubmitMixinService 활용 — 경비 청구 submit 워크플로.
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import (
    ApprovalMixin,
    ApprovalStatus,
    BaseDocument,
    DocStatus,
    MonetaryValue,
    SubmitTransitionMixin,
)
from oneerp_core.dto import ResponseDTO
from oneerp_core.error_catalog import ERR
from oneerp_core.service_base import SubmitMixinService


class ExpenseClaimPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    claim_no: str = ""
    employee_id: str = ""
    purpose: str = ""
    total_amount: MonetaryValue = MonetaryValue(amount=Decimal(0), currency="KRW")


class ExpenseClaimSubmissionResult(ResponseDTO):
    id: str
    claim_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    total_amount: MonetaryValue


class ExpenseClaimService(SubmitMixinService):
    REPO_KEY = "expense_claim"
    DOC_CLASS = ExpenseClaimPilotDoc
    RESULT_CLASS = ExpenseClaimSubmissionResult
    # expenses 전용 ERR 코드 추가 전까지 일반 검증 코드 사용 (M4 ErrorCatalog 확장)
    SUBMIT_BLOCK_ERR = ERR.CMN_VALIDATION
