"""BoardPostPilotService — M3 collab/board 파일럿."""

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


class BoardPostPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    post_no: str = ""
    board_id: str = ""
    title: str = ""


class BoardPostSubmissionResult(ResponseDTO):
    id: str
    post_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    title: str


class BoardPostPilotService(SubmitMixinService):
    REPO_KEY = "board_post_pilot"
    DOC_CLASS = BoardPostPilotDoc
    RESULT_CLASS = BoardPostSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.BRD_001
