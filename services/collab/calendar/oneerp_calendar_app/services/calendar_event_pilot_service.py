"""CalendarEventPilotService — M3 collab/calendar 파일럿."""

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


class CalendarEventPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    event_no: str = ""
    title: str = ""
    starts_at: str = ""


class CalendarEventSubmissionResult(ResponseDTO):
    id: str
    event_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    starts_at: str


class CalendarEventPilotService(SubmitMixinService):
    REPO_KEY = "calendar_event_pilot"
    DOC_CLASS = CalendarEventPilotDoc
    RESULT_CLASS = CalendarEventSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CAL_001
