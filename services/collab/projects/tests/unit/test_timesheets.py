"""타임시트(Timesheet) API 엔드포인트 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_projects_app.routes.timesheets import router

_FAKE_USER = CurrentUser(
    sub="test-user",
    tenant_id="test-tenant",
    roles=("admin",),
    permissions=("*:*",),
)

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
client = TestClient(_app)
client_no_raise = TestClient(_app, raise_server_exceptions=False)


@patch("oneerp_projects_app.routes.timesheets._get_repo")
@patch("oneerp_projects_app.routes.timesheets.generate_name", return_value="TS-2026-00001")
def test_타임시트_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """타임시트 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/timesheets",
        json={
            "employee_id": "EMP-001",
            "employee_name": "홍길동",
            "start_date": "2026-03-01",
            "end_date": "2026-03-15",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "TS-2026-00001"


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_생성_기간역전_422(mock_repo: MagicMock) -> None:
    """종료일이 시작일보다 빠른 타임시트는 저장할 수 없어야 한다."""
    mock_repo.return_value = MagicMock()

    response = client.post(
        "/api/v1/timesheets",
        json={
            "employee_id": "EMP-001",
            "employee_name": "홍길동",
            "start_date": "2026-03-15",
            "end_date": "2026-03-01",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-016"


@patch("oneerp_projects_app.routes.timesheets._get_project_billing_repo")
@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_목록_필터와_요약_조회(
    mock_repo: MagicMock,
    mock_billing_repo: MagicMock,
) -> None:
    """타임시트 목록이 미청구/직원 필터와 요약 정보를 제공해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "TS-001",
            "employee_id": "EMP-001",
            "employee_name": "홍길동",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "total_hours": 8.0,
            "docstatus": 1,
            "billed": False,
            "time_logs": [
                {
                    "date": "2026-03-03",
                    "project_ref": "PROJ-001",
                    "task_ref": "TASK-001",
                    "hours": 8.0,
                    "activity_type": "개발",
                }
            ],
        },
        {
            "_id": "TS-002",
            "employee_id": "EMP-002",
            "employee_name": "이몽룡",
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "total_hours": 6.0,
            "docstatus": 1,
            "billed": True,
            "time_logs": [
                {
                    "date": "2026-03-04",
                    "project_ref": "PROJ-002",
                    "task_ref": "TASK-002",
                    "hours": 6.0,
                    "activity_type": "설계",
                }
            ],
        },
    ]
    mock_repo.return_value = repo
    billing_repo = MagicMock()
    billing_repo.find_many.return_value = [
        {"_id": "PBL-001", "timesheet_ref": "TS-002", "status": "draft", "total": 720000.0}
    ]
    mock_billing_repo.return_value = billing_repo

    response = client.get(
        "/api/v1/timesheets?page=1&page_size=10&employee_id=EMP-001&docstatus=1&billed=false"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["submitted_count"] == 1
    assert payload["summary"]["payroll_ready_hours"] == 8.0
    assert payload["summary"]["unbilled_count"] == 1
    assert response.json()["total"] == 1
    row = payload["data"][0]
    assert row["status_badge"] == "submitted_unbilled"
    assert row["time_log_summary"]["project_refs"] == ["PROJ-001"]
    assert row["available_actions"] == ["create_invoice", "view"]


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 타임시트 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/timesheets/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_projects_app.routes.timesheets._get_project_billing_repo")
@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_상세_요약_조회(
    mock_repo: MagicMock,
    mock_billing_repo: MagicMock,
) -> None:
    """타임시트 상세가 시간 요약과 급여/청구 컨텍스트를 제공해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TS-001",
        "employee_id": "EMP-001",
        "employee_name": "홍길동",
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "total_hours": 8.0,
        "docstatus": 1,
        "billed": True,
        "time_logs": [
            {
                "date": "2026-03-03",
                "project_ref": "PROJ-001",
                "task_ref": "TASK-001",
                "hours": 6.0,
                "activity_type": "개발",
            },
            {
                "date": "2026-03-04",
                "project_ref": "PROJ-001",
                "task_ref": "TASK-002",
                "hours": 2.0,
                "activity_type": "회의",
            },
        ],
    }
    mock_repo.return_value = repo
    billing_repo = MagicMock()
    billing_repo.find_many.return_value = [
        {"_id": "PBL-001", "timesheet_ref": "TS-001", "status": "draft", "total": 960000.0}
    ]
    mock_billing_repo.return_value = billing_repo

    response = client.get("/api/v1/timesheets/TS-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted_billed"
    assert payload["time_log_summary"]["activity_breakdown"][0]["activity_type"] == "개발"
    assert payload["payroll_summary"]["ready_for_payroll"] is True
    assert payload["billing_summary"]["billing_ids"] == ["PBL-001"]
    assert payload["available_actions"] == ["view", "view_invoice"]


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_제출_정상(mock_repo: MagicMock) -> None:
    """타임시트 제출 API가 정상 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TS-001",
        "docstatus": 0,
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "total_hours": 8.0,
        "time_logs": [
            {
                "date": "2026-03-03",
                "project_ref": "PROJ-001",
                "task_ref": "TASK-001",
                "hours": 8.0,
                "activity_type": "개발",
            }
        ],
    }
    mock_repo.return_value = repo
    response = client.post("/api/v1/timesheets/TS-001/submit")
    assert response.status_code == 200
    assert "제출" in response.json()["message"]


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_제출_작업일자_누락_422(mock_repo: MagicMock) -> None:
    """제출 시 time_logs의 작업일자는 필수여야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TS-001",
        "docstatus": 0,
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "total_hours": 8.0,
        "time_logs": [{"project_ref": "PROJ-001", "task_ref": "TASK-001", "hours": 8.0}],
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/timesheets/TS-001/submit")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-018"


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_타임시트_제출_0시간_422(mock_repo: MagicMock) -> None:
    """0시간 타임시트 제출은 422를 반환해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TS-001",
        "docstatus": 0,
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "total_hours": 0,
        "time_logs": [],
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/timesheets/TS-001/submit")

    assert response.status_code == 422
    assert response.json()["detail"] == "총 근무시간이 0보다 커야 제출할 수 있습니다"


@patch("oneerp_projects_app.routes.timesheets._get_repo")
def test_제출완료_타임시트_삭제_400(mock_repo: MagicMock) -> None:
    """제출 완료된 타임시트 삭제는 400으로 차단되어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TS-001", "docstatus": 1}
    repo.delete_by_id.side_effect = ValueError("초안 상태의 문서만 삭제할 수 있습니다")
    mock_repo.return_value = repo

    response = client_no_raise.delete("/api/v1/timesheets/TS-001")

    assert response.status_code == 400
    assert response.json()["detail"] == "초안 상태의 문서만 삭제할 수 있습니다"


@patch("oneerp_projects_app.routes.timesheets._get_repo")
@patch("oneerp_projects_app.routes.timesheets.TimesheetService")
def test_타임시트_인보이스_생성(mock_service_cls: MagicMock, mock_repo: MagicMock) -> None:
    """제출된 타임시트에서 청구서를 생성할 수 있어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TS-001", "docstatus": 1, "billed": False}
    mock_repo.return_value = repo
    service = MagicMock()
    service.generate_invoice_from_timesheet.return_value = {
        "billing_id": "PBL-001",
        "timesheet_id": "TS-001",
        "total_hours": Decimal(34),
        "hourly_rate": Decimal(150000),
        "amount": Decimal(5100000),
    }
    mock_service_cls.return_value = service

    response = client.post(
        "/api/v1/timesheets/TS-001/invoice",
        json={"hourly_rate": 150000},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["billing_id"] == "PBL-001"
    assert payload["total_hours"] == 34.0
    assert payload["hourly_rate"] == 150000.0
    assert payload["amount"] == 5100000.0
    service.generate_invoice_from_timesheet.assert_called_once()


@patch("oneerp_projects_app.routes.timesheets._get_repo")
@patch("oneerp_projects_app.routes.timesheets.TimesheetService")
def test_타임시트_인보이스는_활동유형_단가를_자동적용할_수_있다(
    mock_service_cls: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """hourly_rate 없이도 활동유형 billing_rate 기반 청구를 생성할 수 있어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TS-001", "docstatus": 1, "billed": False}
    mock_repo.return_value = repo
    service = MagicMock()
    service.generate_invoice_from_timesheet.return_value = {
        "billing_id": "PBL-AT-001",
        "timesheet_id": "TS-001",
        "amount": 1040000,
        "rate_source": "activity_type",
    }
    mock_service_cls.return_value = service

    response = client.post("/api/v1/timesheets/TS-001/invoice", json={})

    assert response.status_code == 200
    assert response.json()["rate_source"] == "activity_type"
    service.generate_invoice_from_timesheet.assert_called_once_with("TS-001", hourly_rate=None)
