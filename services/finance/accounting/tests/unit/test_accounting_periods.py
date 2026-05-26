"""회계기간(Accounting Period) 워크벤치 API 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)

_BASE_URL = "/api/v1/accounting-periods"


@patch(
    "oneerp_accounting_app.routes.accounting_periods._today",
    return_value=date(2026, 4, 10),
    create=True,
)
@patch("oneerp_accounting_app.routes.accounting_periods._get_period_closing_service", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_fiscal_year_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_repo", create=True)
@patch(
    "oneerp_accounting_app.routes.accounting_periods.generate_name",
    return_value="APD-2026-00001",
    create=True,
)
def test_회계기간_생성은_회계연도와_워크벤치_초기값을_반환한다(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_fiscal_year_repo: MagicMock,
    mock_service: MagicMock,
    mock_today: MagicMock,
) -> None:
    """회계기간 생성 시 회계연도와 초기 마감 검증 요약이 함께 반환되어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "APD-2026-00001",
        "period_name": "2026-05",
        "start_date": "2026-05-01",
        "end_date": "2026-05-31",
        "company": "COMP-001",
        "status": "open",
        "fiscal_year": "FY-2026",
        "tenant_id": "test-tenant",
    }
    mock_repo.return_value = repo

    fy_repo = MagicMock()
    fy_repo.find_by_id.return_value = {
        "_id": "FY-2026",
        "year_name": "2026",
        "is_closed": False,
    }
    mock_fiscal_year_repo.return_value = fy_repo

    service = MagicMock()
    service.validate_period_closeable.return_value = {
        "period_id": "APD-2026-00001",
        "closeable": True,
        "draft_count": 0,
        "submitted_count": 0,
        "total_entries": 0,
    }
    mock_service.return_value = service

    response = client.post(
        _BASE_URL,
        json={
            "period_name": "2026-05",
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "company": "COMP-001",
            "status": "open",
            "fiscal_year": "FY-2026",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "APD-2026-00001"
    assert payload["period_name"] == "2026-05"
    assert payload["fiscal_year"] == "FY-2026"
    assert payload["status_badge"] == "future_open"
    assert payload["recommended_action"] == "monitor_period_start"
    assert payload["close_validation_summary"] == {
        "closeable": True,
        "draft_count": 0,
        "submitted_count": 0,
        "total_entries": 0,
    }


@patch(
    "oneerp_accounting_app.routes.accounting_periods._today",
    return_value=date(2026, 4, 10),
    create=True,
)
@patch("oneerp_accounting_app.routes.accounting_periods._get_period_closing_service", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_fiscal_year_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_repo", create=True)
def test_회계기간_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_repo: MagicMock,
    mock_fiscal_year_repo: MagicMock,
    mock_service: MagicMock,
    mock_today: MagicMock,
) -> None:
    """목록은 마감 가능 상태를 한 번에 확인할 수 있는 요약을 제공해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "APD-PAST-READY",
            "period_name": "2026-03",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "company": "COMP-001",
            "status": "open",
            "fiscal_year": "FY-2026",
        },
        {
            "_id": "APD-CURRENT",
            "period_name": "2026-04",
            "start_date": "2026-04-01",
            "end_date": "2026-04-30",
            "company": "COMP-001",
            "status": "open",
            "fiscal_year": "FY-2026",
        },
        {
            "_id": "APD-CLOSED",
            "period_name": "2026-02",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "company": "COMP-001",
            "status": "closed",
            "fiscal_year": "FY-2026",
        },
    ]
    mock_repo.return_value = repo

    fy_repo = MagicMock()
    fy_repo.find_by_id.return_value = {
        "_id": "FY-2026",
        "year_name": "2026",
        "is_closed": False,
    }
    mock_fiscal_year_repo.return_value = fy_repo

    service = MagicMock()
    service.validate_period_closeable.side_effect = lambda period_id: {
        "APD-PAST-READY": {
            "period_id": period_id,
            "closeable": True,
            "draft_count": 0,
            "submitted_count": 8,
            "total_entries": 8,
        },
        "APD-CURRENT": {
            "period_id": period_id,
            "closeable": False,
            "draft_count": 2,
            "submitted_count": 5,
            "total_entries": 7,
        },
        "APD-CLOSED": {
            "period_id": period_id,
            "closeable": True,
            "draft_count": 0,
            "submitted_count": 4,
            "total_entries": 4,
        },
    }[period_id]
    mock_service.return_value = service

    response = client.get(f"{_BASE_URL}?status_badge=close_ready&page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "open_count": 1,
        "closed_count": 0,
        "current_period_count": 0,
        "close_ready_count": 1,
        "close_blocked_count": 0,
        "reopenable_count": 0,
        "total_draft_entries": 0,
    }
    assert payload["data"][0]["_id"] == "APD-PAST-READY"
    assert payload["data"][0]["status_badge"] == "close_ready"
    assert payload["data"][0]["recommended_action"] == "close_period"
    assert payload["data"][0]["close_validation_summary"]["submitted_count"] == 8


@patch(
    "oneerp_accounting_app.routes.accounting_periods._today",
    return_value=date(2026, 4, 10),
    create=True,
)
@patch("oneerp_accounting_app.routes.accounting_periods._get_period_closing_service", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_fiscal_year_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_repo", create=True)
def test_회계기간_상세는_마감검증_요약과_권장액션을_반환한다(
    mock_repo: MagicMock,
    mock_fiscal_year_repo: MagicMock,
    mock_service: MagicMock,
    mock_today: MagicMock,
) -> None:
    """상세는 기간 범위와 마감 차단 사유를 함께 보여줘야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "APD-2026-00002",
        "period_name": "2026-03",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "company": "COMP-001",
        "status": "open",
        "fiscal_year": "FY-2026",
    }
    mock_repo.return_value = repo

    fy_repo = MagicMock()
    fy_repo.find_by_id.return_value = {
        "_id": "FY-2026",
        "year_name": "2026",
        "is_closed": False,
    }
    mock_fiscal_year_repo.return_value = fy_repo

    service = MagicMock()
    service.validate_period_closeable.return_value = {
        "period_id": "APD-2026-00002",
        "closeable": False,
        "draft_count": 3,
        "submitted_count": 11,
        "total_entries": 14,
    }
    mock_service.return_value = service

    response = client.get(f"{_BASE_URL}/APD-2026-00002/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "close_blocked"
    assert payload["recommended_action"] == "review_draft_entries"
    assert payload["period_scope_summary"] == {
        "company": "COMP-001",
        "fiscal_year": "FY-2026",
        "day_count": 31,
        "is_current": False,
        "is_future": False,
        "is_past": True,
    }
    assert payload["close_validation_summary"] == {
        "closeable": False,
        "draft_count": 3,
        "submitted_count": 11,
        "total_entries": 14,
    }
    assert payload["available_actions"] == [
        "edit",
        "open_journal_entries",
        "validate_close",
    ]


@patch(
    "oneerp_accounting_app.routes.accounting_periods._today",
    return_value=date(2026, 4, 10),
    create=True,
)
@patch("oneerp_accounting_app.routes.accounting_periods._get_period_closing_service", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_fiscal_year_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_repo", create=True)
def test_회계기간_마감과_재개가_워크벤치_상태를_갱신한다(
    mock_repo: MagicMock,
    mock_fiscal_year_repo: MagicMock,
    mock_service: MagicMock,
    mock_today: MagicMock,
) -> None:
    """운영자는 기간 마감과 재개 결과를 즉시 워크벤치에서 확인해야 한다."""
    repo = MagicMock()
    repo.find_by_id.side_effect = [
        {
            "_id": "APD-2026-00003",
            "period_name": "2026-03",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "company": "COMP-001",
            "status": "closed",
            "fiscal_year": "FY-2026",
        },
        {
            "_id": "APD-2026-00003",
            "period_name": "2026-03",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "company": "COMP-001",
            "status": "closed",
            "fiscal_year": "FY-2026",
        },
        {
            "_id": "APD-2026-00003",
            "period_name": "2026-03",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "company": "COMP-001",
            "status": "open",
            "fiscal_year": "FY-2026",
        },
    ]
    mock_repo.return_value = repo

    fy_repo = MagicMock()
    fy_repo.find_by_id.return_value = {
        "_id": "FY-2026",
        "year_name": "2026",
        "is_closed": False,
    }
    mock_fiscal_year_repo.return_value = fy_repo

    service = MagicMock()
    service.close_period.return_value = {
        "period_id": "APD-2026-00003",
        "pcv_id": "PCV-2026-00001",
        "net_income": 400000,
        "status": "closed",
    }
    service.validate_period_closeable.side_effect = [
        {
            "period_id": "APD-2026-00003",
            "closeable": True,
            "draft_count": 0,
            "submitted_count": 9,
            "total_entries": 9,
        },
        {
            "period_id": "APD-2026-00003",
            "closeable": True,
            "draft_count": 0,
            "submitted_count": 9,
            "total_entries": 9,
        },
    ]
    mock_service.return_value = service

    close_response = client.post(
        f"{_BASE_URL}/APD-2026-00003/close",
        json={"closing_account": "ACC-RETAINED", "remarks": "월 마감"},
    )

    assert close_response.status_code == 200
    close_payload = close_response.json()
    assert close_payload["close_result"]["pcv_id"] == "PCV-2026-00001"
    assert close_payload["status_badge"] == "closed_reopenable"
    assert close_payload["recommended_action"] == "reopen_period"

    reopen_response = client.post(f"{_BASE_URL}/APD-2026-00003/reopen")

    assert reopen_response.status_code == 200
    reopen_payload = reopen_response.json()
    assert reopen_payload["status"] == "open"
    assert reopen_payload["status_badge"] == "close_ready"
    assert reopen_payload["recommended_action"] == "close_period"


@patch("oneerp_accounting_app.routes.accounting_periods._get_journal_entry_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_fiscal_year_repo", create=True)
@patch("oneerp_accounting_app.routes.accounting_periods._get_repo", create=True)
def test_사용중이거나_마감된_회계기간은_삭제할_수_없다(
    mock_repo: MagicMock,
    mock_fiscal_year_repo: MagicMock,
    mock_journal_repo: MagicMock,
) -> None:
    """닫힌 기간이나 분개가 연결된 기간을 삭제하면 안 된다."""
    repo = MagicMock()
    repo.find_by_id.side_effect = [
        {
            "_id": "APD-CLOSED",
            "period_name": "2026-02",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "status": "closed",
            "fiscal_year": "FY-2026",
        },
        {
            "_id": "APD-LINKED",
            "period_name": "2026-03",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "status": "open",
            "fiscal_year": "FY-2026",
        },
    ]
    mock_repo.return_value = repo

    fy_repo = MagicMock()
    fy_repo.find_by_id.return_value = {"_id": "FY-2026", "is_closed": False}
    mock_fiscal_year_repo.return_value = fy_repo

    journal_repo = MagicMock()
    journal_repo.find_many.return_value = [{"_id": "JE-2026-00001"}]
    mock_journal_repo.return_value = journal_repo

    closed_response = client.delete(f"{_BASE_URL}/APD-CLOSED")
    assert closed_response.status_code == 422
    assert closed_response.json()["detail"] == "마감된 회계기간은 삭제할 수 없습니다"

    linked_response = client.delete(f"{_BASE_URL}/APD-LINKED")
    assert linked_response.status_code == 422
    assert linked_response.json()["detail"] == "분개전표가 연결된 회계기간은 삭제할 수 없습니다"
