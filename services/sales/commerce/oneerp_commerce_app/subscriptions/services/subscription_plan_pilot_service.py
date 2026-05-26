"""SubscriptionPlanPilotService — M3 sales/subscriptions."""

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


class SubscriptionPlanPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    plan_no: str = ""
    customer_id: str = ""
    plan_tier: str = ""


class SubscriptionPlanSubmissionResult(ResponseDTO):
    id: str
    plan_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    plan_tier: str


class SubscriptionPlanPilotService(SubmitMixinService):
    REPO_KEY = "subscription_plan_pilot"
    DOC_CLASS = SubscriptionPlanPilotDoc
    RESULT_CLASS = SubscriptionPlanSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.SUB_001
