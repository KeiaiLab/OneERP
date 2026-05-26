"""CampaignPilotService — M3 marketing 파일럿."""

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


class CampaignPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    campaign_no: str = ""
    name: str = ""
    channel: str = ""  # email / sms / push / web


class CampaignSubmissionResult(ResponseDTO):
    id: str
    campaign_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    channel: str


class CampaignPilotService(SubmitMixinService):
    REPO_KEY = "campaign_pilot"
    DOC_CLASS = CampaignPilotDoc
    RESULT_CLASS = CampaignSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.MKT_001
