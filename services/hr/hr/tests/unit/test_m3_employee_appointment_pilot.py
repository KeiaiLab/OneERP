"""M3 Wave C2 — hr EmployeeAppointmentService 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_hr_app.services.employee_appointment_service import (
    EmployeeAppointmentService,
    EmployeeAppointmentSubmissionResult,
)


def _make_svc(doc_raw: dict | None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = EmployeeAppointmentService(tenant_id="tenant-1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "employee_appointment"
    repo.write_outbox = MagicMock()
    svc.register_repo("employee_appointment", repo)
    return svc, repo


def test_채용_발령_제출() -> None:
    svc, repo = _make_svc(
        {
            "_id": "APP-001",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "appointment_no": "APP-2026-0001",
            "employee_id": "EMP-100",
            "appointment_type": "hire",
            "effective_date": "2026-05-01",
        }
    )
    result = svc.submit("APP-001")
    assert isinstance(result, EmployeeAppointmentSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.appointment_type == "hire"
    assert repo.write_outbox.called


def test_이미_SUBMITTED_HR_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "APP-002",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "appointment_no": "APP-2026-0002",
            "employee_id": "EMP-101",
            "appointment_type": "promote",
            "effective_date": "2026-04-15",
        }
    )
    with pytest.raises(ValueError, match=ERR.HR_001.value) as excinfo:
        svc.submit("APP-002")
    assert excinfo.value.args[0]["code"] == ERR.HR_001.value
