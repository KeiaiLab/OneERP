"""M3 Wave C3 — lms CourseEnrollmentService 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import ApprovalStatus, DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_learning_app.lms.services.course_enrollment_pilot_service import (
    CourseEnrollmentPilotService,
    CourseEnrollmentSubmissionResult,
)


def _make_svc(doc_raw: dict | None) -> tuple:
    uow = UnitOfWork(tenant_id="tenant-1")
    svc = CourseEnrollmentPilotService(tenant_id="tenant-1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "course_enrollment_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("course_enrollment_pilot", repo)
    return svc, repo


def test_수강신청_제출() -> None:
    svc, repo = _make_svc(
        {
            "_id": "ENR-001",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.DRAFT,
            "enrollment_no": "ENR-2026-0001",
            "employee_id": "EMP-100",
            "course_code": "OSH-2026-Q2",
            "requested_at": "2026-04-12T10:00:00+09:00",
        }
    )
    result = svc.submit("ENR-001")
    assert isinstance(result, CourseEnrollmentSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.approval_status == ApprovalStatus.PENDING
    assert result.course_code == "OSH-2026-Q2"
    assert repo.write_outbox.called


def test_중복_신청_차단() -> None:
    svc, _ = _make_svc(
        {
            "_id": "ENR-002",
            "tenant_id": "tenant-1",
            "docstatus": DocStatus.SUBMITTED,
            "enrollment_no": "ENR-2026-0002",
            "employee_id": "EMP-100",
            "course_code": "OSH-2026-Q2",
            "requested_at": "2026-04-10T09:00:00+09:00",
        }
    )
    with pytest.raises(ValueError, match=ERR.CMN_CONFLICT.value) as excinfo:
        svc.submit("ENR-002")
    assert excinfo.value.args[0]["code"] == ERR.CMN_CONFLICT.value
