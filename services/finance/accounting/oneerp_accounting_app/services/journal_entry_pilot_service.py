"""JournalEntryService — M3 Wave A2 회계 분개 파일럿.

SubmitMixinService 활용 — ~30 LOC 로 P1~P7 준수.
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


class JournalEntryPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    entry_no: str = ""
    posting_date: str = ""
    total_debit: MonetaryValue = MonetaryValue(amount=Decimal(0), currency="KRW")


class JournalEntrySubmissionResult(ResponseDTO):
    id: str
    entry_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    total_debit: MonetaryValue


class JournalEntryService(SubmitMixinService):
    REPO_KEY = "journal_entry"
    DOC_CLASS = JournalEntryPilotDoc
    RESULT_CLASS = JournalEntrySubmissionResult
    SUBMIT_BLOCK_ERR = ERR.ACCT_002
