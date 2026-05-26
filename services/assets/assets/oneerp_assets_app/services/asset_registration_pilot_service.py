"""AssetRegistrationPilotService — M3 assets/assets."""

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


class AssetRegistrationPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    request_no: str = ""
    asset_class: str = ""
    asset_no: str = ""


class AssetRegistrationSubmissionResult(ResponseDTO):
    id: str
    request_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    asset_no: str


class AssetRegistrationPilotService(SubmitMixinService):
    REPO_KEY = "asset_registration_pilot"
    DOC_CLASS = AssetRegistrationPilotDoc
    RESULT_CLASS = AssetRegistrationSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.AST_001
