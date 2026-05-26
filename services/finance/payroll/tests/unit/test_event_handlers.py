"""Payroll 이벤트 핸들러 단위 테스트."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from unittest.mock import MagicMock, patch


def _make_event_data(
    doc_id: str,
    tenant_id: str = "test",
    data: dict | None = None,
) -> dict:
    """테스트용 EventEnvelope 데이터를 생성한다."""
    return {
        "event": {
            "doc_id": doc_id,
            "tenant_id": tenant_id,
            "data": data or {},
        },
    }


def test_급여제출_이벤트_계산_호출() -> None:
    """급여처리 제출 이벤트 수신 시 급여 계산 서비스가 호출되는지 검증."""
    event_data = _make_event_data("PAYROLL-001")

    with patch(
        "oneerp_payroll_app.services.payroll_calculation_service.PayrollCalculationService"
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.process_payroll.return_value = ["SLIP-001", "SLIP-002"]
        mock_cls.return_value = mock_instance

        from oneerp_payroll_app.events.handlers import handle_payroll_entry_submitted

        asyncio.run(handle_payroll_entry_submitted(event_data, "evt-001"))

        mock_cls.assert_called_once_with("test")
        mock_instance.process_payroll.assert_called_once_with("PAYROLL-001")


# ---------------------------------------------------------------------------
# EMPLOYEE_UPDATED 핸들러 테스트
# ---------------------------------------------------------------------------

_DRAFT_ENTRY = {
    "_id": "PRLE-001",
    "docstatus": 0,
    "employees": [
        {
            "employee_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "개발팀",
            "designation": "사원",
            "base_salary": 3_000_000,
        },
        {
            "employee_id": "EMP-002",
            "employee_name": "김철수",
            "department": "영업팀",
            "designation": "대리",
            "base_salary": 3_500_000,
        },
    ],
}

_SUBMITTED_ENTRY = {
    "_id": "PRLE-002",
    "docstatus": 1,
    "employees": [
        {
            "employee_id": "EMP-001",
            "employee_name": "홍길동",
            "department": "개발팀",
            "designation": "사원",
            "base_salary": 3_000_000,
        },
    ],
}


def test_직원변경_DRAFT_급여대장_동기화() -> None:
    """EMPLOYEE_UPDATED 이벤트 수신 시 DRAFT 급여대장의 직원명이 갱신된다."""
    event_data = _make_event_data(
        "EMP-001",
        data={"employee_name": "홍길순", "department": "인사팀"},
    )

    mock_repo = MagicMock()
    draft = deepcopy(_DRAFT_ENTRY)
    mock_repo.find_many.return_value = [draft]

    with patch("oneerp_payroll_app.events.handlers.Repository", return_value=mock_repo):
        from oneerp_payroll_app.events.handlers import (
            handle_employee_updated,
        )

        asyncio.run(handle_employee_updated(event_data, "evt-100"))

    # find_many가 DRAFT + employee_id 조건으로 호출되었는지 확인
    call_args = mock_repo.find_many.call_args
    query = call_args[0][0]
    assert query["docstatus"] == 0
    assert query["employees.employee_id"] == "EMP-001"

    # update_by_id가 갱신된 employees 배열로 호출되었는지 확인
    mock_repo.update_by_id.assert_called_once()
    update_call = mock_repo.update_by_id.call_args
    assert update_call[0][0] == "PRLE-001"
    updated_employees = update_call[0][1]["employees"]

    # EMP-001의 이름과 부서가 갱신되었는지 확인
    emp_001 = next(e for e in updated_employees if e["employee_id"] == "EMP-001")
    assert emp_001["employee_name"] == "홍길순"
    assert emp_001["department"] == "인사팀"

    # EMP-002는 변경되지 않았는지 확인
    emp_002 = next(e for e in updated_employees if e["employee_id"] == "EMP-002")
    assert emp_002["employee_name"] == "김철수"
    assert emp_002["department"] == "영업팀"


def test_직원변경_SUBMITTED_급여대장_미변경() -> None:
    """SUBMITTED 상태의 급여대장은 EMPLOYEE_UPDATED 이벤트로 변경되지 않는다.

    find_many 쿼리가 docstatus=DRAFT 조건을 포함하므로
    SUBMITTED 급여대장은 조회 자체가 되지 않아 갱신이 발생하지 않는다.
    """
    event_data = _make_event_data(
        "EMP-001",
        data={"employee_name": "홍길순"},
    )

    mock_repo = MagicMock()
    # DRAFT 조건으로 조회하므로 SUBMITTED 문서는 결과에 포함되지 않음
    mock_repo.find_many.return_value = []

    with patch("oneerp_payroll_app.events.handlers.Repository", return_value=mock_repo):
        from oneerp_payroll_app.events.handlers import (
            handle_employee_updated,
        )

        asyncio.run(handle_employee_updated(event_data, "evt-200"))

    # 조회는 되지만 업데이트는 호출되지 않음
    mock_repo.find_many.assert_called_once()
    mock_repo.update_by_id.assert_not_called()


def test_직원변경_동기화대상_필드없으면_스킵() -> None:
    """동기화 대상 필드(employee_name, department, designation)가 아닌 변경은 무시한다."""
    event_data = _make_event_data(
        "EMP-001",
        data={"email": "new@example.com", "phone": "010-1234-5678"},
    )

    mock_repo = MagicMock()

    with patch("oneerp_payroll_app.events.handlers.Repository", return_value=mock_repo):
        from oneerp_payroll_app.events.handlers import (
            handle_employee_updated,
        )

        asyncio.run(handle_employee_updated(event_data, "evt-300"))

    # 동기화 대상 필드가 없으므로 조회 자체를 하지 않음
    mock_repo.find_many.assert_not_called()
    mock_repo.update_by_id.assert_not_called()
