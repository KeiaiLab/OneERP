"""EngineeringChangeRequestPilotService — M3 plm 파일럿."""

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


class ECRPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    ecr_no: str = ""
    part_id: str = ""
    change_reason: str = ""


class ECRSubmissionResult(ResponseDTO):
    id: str
    ecr_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    part_id: str


class ECRPilotService(SubmitMixinService):
    REPO_KEY = "ecr_pilot"
    DOC_CLASS = ECRPilotDoc
    RESULT_CLASS = ECRSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.PLM_001
