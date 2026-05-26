"""ProjectKickoffPilotService — M3 collab/projects 파일럿."""

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


class ProjectKickoffPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    project_no: str = ""
    project_name: str = ""
    sponsor_id: str = ""


class ProjectKickoffSubmissionResult(ResponseDTO):
    id: str
    project_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    project_name: str


class ProjectKickoffPilotService(SubmitMixinService):
    REPO_KEY = "project_kickoff_pilot"
    DOC_CLASS = ProjectKickoffPilotDoc
    RESULT_CLASS = ProjectKickoffSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.PRJ_001
