"""EmployeeAppointmentService — M3 Wave C2 인사 발령 파일럿.

SubmitMixinService 활용 — 인사 발령(채용/승진/이동/퇴직) submit 워크플로.
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


class EmployeeAppointmentPilotDoc(BaseDocument, ApprovalMixin, SubmitTransitionMixin):
    appointment_no: str = ""
    employee_id: str = ""
    appointment_type: str = ""  # hire / promote / transfer / resign
    effective_date: str = ""


class EmployeeAppointmentSubmissionResult(ResponseDTO):
    id: str
    appointment_no: str
    docstatus: DocStatus
    approval_status: ApprovalStatus
    appointment_type: str


class EmployeeAppointmentService(SubmitMixinService):
    REPO_KEY = "employee_appointment"
    DOC_CLASS = EmployeeAppointmentPilotDoc
    RESULT_CLASS = EmployeeAppointmentSubmissionResult
    SUBMIT_BLOCK_ERR = ERR.HR_001
