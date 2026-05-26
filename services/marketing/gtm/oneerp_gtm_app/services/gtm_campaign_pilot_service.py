"""GTMCampaignPilotService — M3 marketing/gtm."""

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


class GTMCampaignPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    campaign_no: str = ""
    product: str = ""
    region: str = ""


class GTMCampaignSubmissionResult(ResponseDTO):
    id: str
    campaign_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    product: str


class GTMCampaignPilotService(SubmitMixinService):
    REPO_KEY = "gtm_campaign_pilot"
    DOC_CLASS = GTMCampaignPilotDoc
    RESULT_CLASS = GTMCampaignSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.GTM_001
