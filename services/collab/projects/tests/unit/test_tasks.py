"""작업(Task) API 엔드포인트 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_projects_app.routes.tasks import router

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


@patch("oneerp_projects_app.routes.tasks._get_repo")
@patch("oneerp_projects_app.routes.tasks.generate_name", return_value="TASK-2026-00001")
def test_작업_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """작업 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/tasks",
        json={"subject": "API 설계"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "TASK-2026-00001"


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_목록_조회(mock_repo: MagicMock) -> None:
    """작업 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "TASK-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/tasks?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_목록_필터_조회(mock_repo: MagicMock) -> None:
    """상태·담당자·프로젝트 필터가 저장소 쿼리로 전달되어야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    mock_repo.return_value = repo

    response = client.get(
        "/api/v1/tasks?status=working&assigned_to=EMP-001&project_ref=PROJ-001&page=2&page_size=5"
    )

    assert response.status_code == 200
    repo.find_many.assert_called_once_with(
        {"status": "working", "assigned_to": "EMP-001", "project_ref": "PROJ-001"},
        skip=5,
        limit=5,
        sort=[("created_at", -1)],
    )
    repo.count.assert_called_once_with(
        {"status": "working", "assigned_to": "EMP-001", "project_ref": "PROJ-001"}
    )


@patch("oneerp_projects_app.routes.tasks._get_repo")
@patch("oneerp_projects_app.routes.tasks.generate_name", return_value="TASK-2026-00002")
def test_작업_생성시_일정과_선행작업을_저장한다(
    mock_name: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """일정과 선행 작업 정보가 Task 문서에 반영되어야 한다."""
    repo = MagicMock()
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/tasks",
        json={
            "subject": "후속 개발",
            "project_ref": "PROJ-001",
            "assigned_to": "EMP-001",
            "start_date": "2026-04-01",
            "end_date": "2026-04-03",
            "predecessor_task_ids": ["TASK-2026-00001"],
        },
    )

    assert response.status_code == 201
    inserted = repo.insert.call_args.args[0]
    assert inserted.start_date == date(2026, 4, 1)
    assert inserted.end_date == date(2026, 4, 3)
    assert inserted.predecessor_task_ids == ["TASK-2026-00001"]


def test_작업_생성시_종료일이_시작일보다_빠르면_422() -> None:
    """잘못된 일정 역전은 생성 시점에 거부되어야 한다."""
    response = client.post(
        "/api/v1/tasks",
        json={
            "subject": "일정 오류 작업",
            "start_date": "2026-04-05",
            "end_date": "2026-04-01",
        },
    )

    assert response.status_code == 422


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 작업 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/tasks/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_진행전환시_담당자_없으면_차단(mock_repo: MagicMock) -> None:
    """담당자가 없는 작업은 진행중으로 전환할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TASK-2026-00010",
        "subject": "담당자 없는 작업",
        "status": "open",
        "assigned_to": "",
        "predecessor_task_ids": [],
    }
    mock_repo.return_value = repo

    response = client.put(
        "/api/v1/tasks/TASK-2026-00010",
        json={"status": "working"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-012"
    repo.update_by_id.assert_not_called()


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_진행전환시_선행작업_미완료면_차단(mock_repo: MagicMock) -> None:
    """선행 작업이 남아 있으면 후속 작업을 시작할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.side_effect = [
        {
            "_id": "TASK-2026-00002",
            "subject": "후속 작업",
            "status": "open",
            "assigned_to": "EMP-001",
            "predecessor_task_ids": ["TASK-2026-00001"],
        },
        {
            "_id": "TASK-2026-00001",
            "subject": "선행 작업",
            "status": "working",
        },
    ]
    mock_repo.return_value = repo

    response = client.put(
        "/api/v1/tasks/TASK-2026-00002",
        json={"status": "working"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "선행 작업이 완료되어야 합니다"
    repo.update_by_id.assert_not_called()


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_검토대기전환시_실적시간이_없으면_차단(mock_repo: MagicMock) -> None:
    """실제 시간이 없는 작업은 검토대기로 올릴 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TASK-2026-00020",
        "subject": "실적 없는 작업",
        "status": "working",
        "assigned_to": "EMP-001",
        "actual_time": 0,
        "predecessor_task_ids": [],
    }
    mock_repo.return_value = repo

    response = client.put(
        "/api/v1/tasks/TASK-2026-00020",
        json={"status": "pending_review"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-013"
    repo.update_by_id.assert_not_called()


@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_완료전환은_검토대기에서만_허용(mock_repo: MagicMock) -> None:
    """검토대기가 아니면 완료 처리할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TASK-2026-00030",
        "subject": "바로 완료 시도",
        "status": "working",
        "assigned_to": "EMP-001",
        "actual_time": 3,
        "predecessor_task_ids": [],
    }
    mock_repo.return_value = repo

    response = client.put(
        "/api/v1/tasks/TASK-2026-00030",
        json={"status": "completed"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-014"
    repo.update_by_id.assert_not_called()


@patch("oneerp_projects_app.routes.tasks._get_timesheet_repo")
@patch("oneerp_projects_app.routes.tasks._get_repo")
def test_작업_삭제시_타임시트로그가_남아있으면_차단(
    mock_repo: MagicMock,
    mock_timesheet_repo: MagicMock,
) -> None:
    """타임시트가 연결된 작업은 삭제할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TASK-2026-00040",
        "subject": "삭제 차단 작업",
    }
    repo.find_many.return_value = []
    mock_repo.return_value = repo
    timesheet_repo = MagicMock()
    timesheet_repo.find_many.return_value = [{"_id": "TS-2026-00001", "docstatus": 1}]
    mock_timesheet_repo.return_value = timesheet_repo

    response = client.delete("/api/v1/tasks/TASK-2026-00040")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-PRJ-015"
    repo.delete_by_id.assert_not_called()
