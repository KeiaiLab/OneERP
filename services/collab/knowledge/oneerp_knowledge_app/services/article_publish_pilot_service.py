"""ArticlePublishPilotService — M3 collab/knowledge 파일럿."""

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


class ArticlePublishPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    publish_no: str = ""
    article_id: str = ""
    title: str = ""


class ArticlePublishSubmissionResult(ResponseDTO):
    id: str
    publish_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    article_id: str


class ArticlePublishPilotService(SubmitMixinService):
    REPO_KEY = "article_publish_pilot"
    DOC_CLASS = ArticlePublishPilotDoc
    RESULT_CLASS = ArticlePublishSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.KNW_001
