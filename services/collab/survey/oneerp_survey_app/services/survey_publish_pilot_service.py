"""SurveyPublishPilotService — M3 collab/survey 파일럿."""

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


class SurveyPublishPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    survey_no: str = ""
    title: str = ""
    target_audience: str = ""


class SurveyPublishSubmissionResult(ResponseDTO):
    id: str
    survey_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    title: str


class SurveyPublishPilotService(SubmitMixinService):
    REPO_KEY = "survey_publish_pilot"
    DOC_CLASS = SurveyPublishPilotDoc
    RESULT_CLASS = SurveyPublishSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.SUR_001
