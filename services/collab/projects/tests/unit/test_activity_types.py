"""활동유형(ActivityType) API 엔드포인트 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_projects_app.routes.activity_types import router

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


@patch("oneerp_projects_app.routes.activity_types._get_repo")
@patch("oneerp_projects_app.routes.activity_types.generate_name", return_value="ATYP-2026-00001")
def test_활동유형_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """활동유형 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post("/api/v1/activity-types/", json={"activity_type": "전화"})
    assert response.status_code == 201
    assert response.json()["activity_type_id"] == "ATYP-2026-00001"


@patch("oneerp_projects_app.routes.activity_types._get_repo")
def test_활동유형_목록_조회(mock_repo: MagicMock) -> None:
    """활동유형 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "ATYP-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/activity-types/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_projects_app.routes.activity_types._get_repo")
def test_활동유형_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 활동유형 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/activity-types/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_projects_app.routes.activity_types._get_repo")
def test_활동유형_목록은_워크벤치_요약과_상태배지를_반환한다(mock_repo: MagicMock) -> None:
    """활동유형 목록은 사용량/미청구 시간/마진 위험을 함께 보여줘야 한다."""
    activity_repo = MagicMock()
    activity_repo.find_many.return_value = [
        {
            "_id": "ATYP-001",
            "activity_type": "개발",
            "costing_rate": Decimal(70000),
            "billing_rate": Decimal(120000),
            "is_active": True,
        },
        {
            "_id": "ATYP-002",
            "activity_type": "지원",
            "costing_rate": Decimal(90000),
            "billing_rate": Decimal(80000),
            "is_active": True,
        },
        {
            "_id": "ATYP-003",
            "activity_type": "중단유형",
            "costing_rate": Decimal(0),
            "billing_rate": Decimal(0),
            "is_active": False,
        },
    ]
    timesheet_repo = MagicMock()
    timesheet_repo.find_many.return_value = [
        {
            "_id": "TS-001",
            "docstatus": 1,
            "billed": False,
            "time_logs": [
                {
                    "activity_type": "개발",
                    "hours": 8,
                    "project_ref": "PRJ-001",
                    "date": "2026-04-01",
                }
            ],
        },
        {
            "_id": "TS-002",
            "docstatus": 1,
            "billed": True,
            "time_logs": [
                {
                    "activity_type": "개발",
                    "hours": 2,
                    "project_ref": "PRJ-002",
                    "date": "2026-04-05",
                }
            ],
        },
        {
            "_id": "TS-003",
            "docstatus": 0,
            "billed": False,
            "time_logs": [
                {
                    "activity_type": "지원",
                    "hours": 4,
                    "project_ref": "PRJ-003",
                    "date": "2026-04-03",
                }
            ],
        },
    ]
    mock_repo.side_effect = [activity_repo, timesheet_repo]

    response = client.get("/api/v1/activity-types/?status_badge=margin_watch")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "active_count": 1,
        "inactive_count": 0,
        "in_use_count": 1,
        "margin_watch_count": 1,
        "total_logged_hours": 4.0,
        "unbilled_hours": 0.0,
    }
    assert payload["data"][0]["activity_type"] == "지원"
    assert payload["data"][0]["status_badge"] == "margin_watch"
    assert payload["data"][0]["recommended_action"] == "raise_billing_rate"
    assert payload["data"][0]["usage_summary"] == {
        "timesheet_count": 1,
        "submitted_timesheet_count": 0,
        "active_project_count": 1,
        "total_logged_hours": 4.0,
        "unbilled_hours": 0.0,
        "last_used_date": "2026-04-03",
    }


@patch("oneerp_projects_app.routes.activity_types._get_repo")
def test_활동유형_상세는_단가와_사용량_요약을_반환한다(mock_repo: MagicMock) -> None:
    """활동유형 상세는 단가/사용량 워크벤치와 권장 액션을 보여줘야 한다."""
    activity_repo = MagicMock()
    activity_repo.find_by_id.return_value = {
        "_id": "ATYP-001",
        "activity_type": "개발",
        "costing_rate": Decimal(70000),
        "billing_rate": Decimal(120000),
        "is_active": True,
    }
    timesheet_repo = MagicMock()
    timesheet_repo.find_many.return_value = [
        {
            "_id": "TS-001",
            "docstatus": 1,
            "billed": False,
            "time_logs": [
                {
                    "activity_type": "개발",
                    "hours": 8,
                    "project_ref": "PRJ-001",
                    "date": "2026-04-01",
                }
            ],
        },
        {
            "_id": "TS-002",
            "docstatus": 1,
            "billed": True,
            "time_logs": [
                {
                    "activity_type": "개발",
                    "hours": 2,
                    "project_ref": "PRJ-002",
                    "date": "2026-04-05",
                }
            ],
        },
    ]
    mock_repo.side_effect = [activity_repo, timesheet_repo]

    response = client.get("/api/v1/activity-types/ATYP-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "active_in_use"
    assert payload["recommended_action"] == "review_unbilled_timesheets"
    assert payload["rate_summary"] == {
        "costing_rate": 70000.0,
        "billing_rate": 120000.0,
        "margin_per_hour": 50000.0,
        "expected_margin_amount": 500000.0,
    }
    assert payload["usage_summary"] == {
        "timesheet_count": 2,
        "submitted_timesheet_count": 2,
        "active_project_count": 2,
        "total_logged_hours": 10.0,
        "unbilled_hours": 8.0,
        "last_used_date": "2026-04-05",
    }
    assert payload["available_actions"] == ["edit", "open_timesheets", "deactivate"]


@patch("oneerp_projects_app.routes.activity_types._get_repo")
def test_사용중이아닌_활동유형은_삭제할_수_있다(mock_repo: MagicMock) -> None:
    """이력이 없는 활동유형은 삭제할 수 있어야 한다."""
    activity_repo = MagicMock()
    activity_repo.find_by_id.return_value = {
        "_id": "ATYP-099",
        "activity_type": "미사용",
        "is_active": False,
    }
    timesheet_repo = MagicMock()
    timesheet_repo.find_many.return_value = []
    mock_repo.side_effect = [activity_repo, timesheet_repo]

    response = client.delete("/api/v1/activity-types/ATYP-099")

    assert response.status_code == 204
