"""CourseEnrollmentPilotService — M3 Wave C3 LMS 수강 신청 파일럿.

기존 course_enrollment_service.py 와 충돌 회피용 별도 이름.
SubmitMixinService 활용 — 수강 신청 submit 후 결재선 흐름.
"""

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


class CourseEnrollmentPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    enrollment_no: str = ""
    employee_id: str = ""
    course_code: str = ""
    requested_at: str = ""


class CourseEnrollmentSubmissionResult(ResponseDTO):
    id: str
    enrollment_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    course_code: str


class CourseEnrollmentPilotService(SubmitMixinService):
    REPO_KEY = "course_enrollment_pilot"
    DOC_CLASS = CourseEnrollmentPilotDoc
    RESULT_CLASS = CourseEnrollmentSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.CMN_CONFLICT
