"""프로젝트(Project) API 엔드포인트 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_projects_app.routes.projects import router

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


@patch("oneerp_projects_app.routes.projects._get_repo")
@patch("oneerp_projects_app.routes.projects.generate_name", return_value="PROJ-2026-00001")
def test_프로젝트_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """프로젝트 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/projects",
        json={"project_name": "ERP 구축"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "PROJ-2026-00001"


@patch("oneerp_projects_app.routes.projects._get_repo")
def test_프로젝트_목록_조회(mock_repo: MagicMock) -> None:
    """프로젝트 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "PROJ-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/projects?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_projects_app.routes.projects._get_repo")
def test_프로젝트_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 프로젝트 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/projects/NOT-EXIST")
    assert response.status_code == 404


def test_프로젝트_일정역전_검증() -> None:
    """예상 종료일이 시작일보다 빠르면 422를 반환해야 한다."""
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": "일정 오류 프로젝트",
            "expected_start_date": "2026-06-01",
            "expected_end_date": "2026-05-01",
        },
    )

    assert response.status_code == 422


@patch("oneerp_projects_app.routes.projects._get_repo")
@patch("oneerp_projects_app.routes.projects._get_employee_repo")
@patch("oneerp_projects_app.routes.projects.generate_name", return_value="PROJ-2026-00001")
def test_프로젝트_생성시_존재하지_않는_프로젝트_관리자를_차단한다(
    mock_name: MagicMock,
    mock_employee_repo: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """존재하지 않는 프로젝트 관리자를 지정하면 422를 반환해야 한다."""
    mock_repo.return_value = MagicMock()
    employee_repo = MagicMock()
    employee_repo.find_by_id.return_value = None
    mock_employee_repo.return_value = employee_repo

    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": "관리자 검증 프로젝트",
            "project_manager": "EMP-MISSING-001",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-010"


@patch("oneerp_projects_app.routes.projects._get_task_repo")
@patch("oneerp_projects_app.routes.projects._get_milestone_repo")
@patch("oneerp_projects_app.routes.projects._get_employee_repo")
@patch("oneerp_projects_app.routes.projects._get_repo")
def test_프로젝트_목록은_필터와_운영_요약을_반환한다(
    mock_repo: MagicMock,
    mock_employee_repo: MagicMock,
    mock_milestone_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """프로젝트 목록이 상태/회사/관리자 필터와 카드형 요약 정보를 제공해야 한다."""
    project_repo = MagicMock()
    project_repo.find_many.return_value = [
        {
            "_id": "PROJ-0001",
            "project_name": "ERP 고도화",
            "status": "in_progress",
            "company": "COMP-001",
            "project_manager": "EMP-001",
            "budget": 15000000,
            "percent_complete": 45.0,
        },
        {
            "_id": "PROJ-0002",
            "project_name": "창고 개선",
            "status": "open",
            "company": "COMP-002",
            "project_manager": "EMP-002",
            "budget": 5000000,
            "percent_complete": 5.0,
        },
    ]
    mock_repo.return_value = project_repo

    employee_repo = MagicMock()
    employee_repo.find_many.return_value = [
        {"_id": "EMP-001", "employee_name": "김PM"},
        {"_id": "EMP-002", "employee_name": "박PM"},
    ]
    mock_employee_repo.return_value = employee_repo

    task_repo = MagicMock()
    task_repo.find_many.return_value = [
        {"_id": "TASK-1", "project_ref": "PROJ-0001", "status": "completed"},
        {"_id": "TASK-2", "project_ref": "PROJ-0001", "status": "working"},
        {"_id": "TASK-3", "project_ref": "PROJ-0002", "status": "open"},
    ]
    mock_task_repo.return_value = task_repo

    milestone_repo = MagicMock()
    milestone_repo.find_many.return_value = [
        {"_id": "MLS-1", "project": "PROJ-0001", "status": "overdue"},
        {"_id": "MLS-2", "project": "PROJ-0001", "status": "pending"},
    ]
    mock_milestone_repo.return_value = milestone_repo

    response = client.get(
        "/api/v1/projects?status=in_progress&company=COMP-001&project_manager=EMP-001"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"]["in_progress"] == 1
    assert payload["summary"]["total_budget"] == 15000000.0
    assert payload["summary"]["average_progress"] == 45.0
    row = payload["data"][0]
    assert row["id"] == "PROJ-0001"
    assert row["project_manager_name"] == "김PM"
    assert row["task_count"] == 2
    assert row["completed_task_count"] == 1
    assert row["overdue_milestone_count"] == 1


@patch("oneerp_projects_app.routes.projects._get_repo")
def test_프로젝트_완료율은_0에서_100사이여야_한다(mock_repo: MagicMock) -> None:
    """프로젝트 완료율이 100을 초과하면 422를 반환해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PROJ-0001",
        "project_name": "완료율 검증 프로젝트",
        "percent_complete": Decimal(20),
    }
    mock_repo.return_value = repo

    response = client.put(
        "/api/v1/projects/PROJ-0001",
        json={"percent_complete": 120.0},
    )

    assert response.status_code == 422


@patch("oneerp_projects_app.routes.projects._get_project_billing_repo")
@patch("oneerp_projects_app.routes.projects._get_resource_allocation_repo")
@patch("oneerp_projects_app.routes.projects._get_milestone_repo")
@patch("oneerp_projects_app.routes.projects._get_task_repo")
@patch("oneerp_projects_app.routes.projects._get_repo")
def test_하위_문서가_남아있는_프로젝트는_삭제할_수_없다(
    mock_repo: MagicMock,
    mock_task_repo: MagicMock,
    mock_milestone_repo: MagicMock,
    mock_resource_repo: MagicMock,
    mock_billing_repo: MagicMock,
) -> None:
    """작업/마일스톤/자원/청구가 연결된 프로젝트는 삭제를 차단해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PROJ-0001",
        "project_name": "삭제 차단 프로젝트",
    }
    mock_repo.return_value = repo

    task_repo = MagicMock()
    task_repo.count.return_value = 1
    mock_task_repo.return_value = task_repo
    mock_milestone_repo.return_value = MagicMock()
    mock_resource_repo.return_value = MagicMock()
    mock_billing_repo.return_value = MagicMock()

    response = client.delete("/api/v1/projects/PROJ-0001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-011"
