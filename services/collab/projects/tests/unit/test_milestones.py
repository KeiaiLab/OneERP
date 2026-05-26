"""마일스톤(Milestone) API 엔드포인트 테스트."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_projects_app.routes.milestones import router

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


@patch("oneerp_projects_app.routes.milestones._get_repo")
@patch("oneerp_projects_app.routes.milestones.generate_name", return_value="MLS-2026-00001")
def test_마일스톤_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """마일스톤 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/milestones/",
        json={"milestone_name": "v1.0 출시", "project": "PRJ-001"},
    )
    assert response.status_code == 201
    assert response.json()["milestone_id"] == "MLS-2026-00001"


@patch("oneerp_projects_app.routes.milestones._get_repo")
@patch("oneerp_projects_app.routes.milestones.generate_name", return_value="MLS-2026-00002")
def test_마일스톤_생성시_완료조건과_청구금액을_저장한다(
    mock_name: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """완료 조건과 청구 금액은 문서에 보존되어야 한다."""
    repo = MagicMock()
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/milestones/",
        json={
            "milestone_name": "UAT 완료",
            "project": "PRJ-001",
            "completion_criteria": "고객 승인서 업로드",
            "billing_amount": "2500000",
        },
    )

    assert response.status_code == 201
    inserted = repo.insert.call_args.args[0]
    assert inserted.completion_criteria == "고객 승인서 업로드"
    assert inserted.billing_amount == Decimal(2500000)


@patch("oneerp_projects_app.routes.milestones._get_repo")
def test_마일스톤_목록_조회(mock_repo: MagicMock) -> None:
    """마일스톤 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "MLS-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/milestones/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_projects_app.routes.milestones._get_repo")
def test_마일스톤_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 마일스톤 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/milestones/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_projects_app.routes.milestones._get_billing_repo")
@patch("oneerp_projects_app.routes.milestones._get_repo")
def test_마일스톤_목록은_상태배지와_청구요약_필터를_반환한다(
    mock_repo: MagicMock,
    mock_billing_repo: MagicMock,
) -> None:
    """목록은 상태 배지/청구 요약을 제공하고 billing_status 필터를 지원해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "MLS-001",
            "project": "PRJ-001",
            "milestone_name": "설계 완료",
            "status": "pending",
            "due_date": date(2026, 4, 1),
            "billing_amount": "0",
        },
        {
            "_id": "MLS-002",
            "project": "PRJ-001",
            "milestone_name": "UAT 완료",
            "status": "completed",
            "due_date": date(2026, 4, 20),
            "billing_amount": "2500000",
            "billing_id": "PBL-001",
        },
    ]
    billing_repo = MagicMock()
    billing_repo.find_many.return_value = [
        {
            "_id": "PBL-001",
            "milestone_id": "MLS-002",
            "status": "draft",
            "is_invoiced": False,
            "total": 2500000.0,
        }
    ]
    mock_repo.return_value = repo
    mock_billing_repo.return_value = billing_repo

    response = client.get(
        "/api/v1/milestones/?project=PRJ-001&billing_status=ready_to_invoice&as_of_date=2026-04-10"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"]["ready_to_invoice_count"] == 1
    assert payload["summary"]["total_billing_amount"] == 2500000.0
    row = payload["data"][0]
    assert row["_id"] == "MLS-002"
    assert row["status_badge"] == "completed_ready_to_invoice"
    assert row["billing_summary"] == {
        "billing_required": True,
        "billing_id": "PBL-001",
        "billing_status": "ready_to_invoice",
        "billing_amount": 2500000.0,
        "is_invoiced": False,
    }
    assert row["available_actions"] == ["view", "open_billing"]


@patch("oneerp_projects_app.routes.milestones._get_billing_repo")
@patch("oneerp_projects_app.routes.milestones._get_repo")
def test_마일스톤_상세는_상태배지와_청구_워크벤치를_노출한다(
    mock_repo: MagicMock,
    mock_billing_repo: MagicMock,
) -> None:
    """상세 조회는 청구 상태와 가능 액션을 반환해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MLS-002",
        "project": "PRJ-001",
        "milestone_name": "UAT 완료",
        "status": "completed",
        "due_date": date(2026, 4, 20),
        "billing_amount": "2500000",
        "billing_id": "PBL-001",
    }
    billing_repo = MagicMock()
    billing_repo.find_many.return_value = [
        {
            "_id": "PBL-001",
            "milestone_id": "MLS-002",
            "status": "draft",
            "is_invoiced": False,
            "total": 2500000.0,
        }
    ]
    mock_repo.return_value = repo
    mock_billing_repo.return_value = billing_repo

    response = client.get("/api/v1/milestones/MLS-002")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "completed_ready_to_invoice"
    assert payload["billing_summary"]["billing_status"] == "ready_to_invoice"
    assert payload["billing_summary"]["billing_amount"] == 2500000.0
    assert payload["available_actions"] == ["view", "open_billing"]
