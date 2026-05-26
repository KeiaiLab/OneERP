"""WikiPagePilotService — M3 collab/wiki 파일럿."""

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


class WikiPagePilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    page_no: str = ""
    space: str = ""
    title: str = ""


class WikiPageSubmissionResult(ResponseDTO):
    id: str
    page_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    title: str


class WikiPagePilotService(SubmitMixinService):
    REPO_KEY = "wiki_page_pilot"
    DOC_CLASS = WikiPagePilotDoc
    RESULT_CLASS = WikiPageSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.WIK_001
