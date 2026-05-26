"""ScopeEmissionReportPilotService — M3 esg 파일럿."""

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


class ScopeEmissionPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    report_no: str = ""
    period: str = ""  # YYYY (연도)
    scope: int = 1  # 1 / 2 / 3


class ScopeEmissionSubmissionResult(ResponseDTO):
    id: str
    report_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    scope: int


class ScopeEmissionPilotService(SubmitMixinService):
    REPO_KEY = "scope_emission_pilot"
    DOC_CLASS = ScopeEmissionPilotDoc
    RESULT_CLASS = ScopeEmissionSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.ESG_001
