"""휴가신청(LeaveApplication) 워크벤치 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_hr_app.routes.leave_applications as leave_application_routes

_BASE_URL = "/api/v1/leave-applications"


def _patch_workbench_repos(
    monkeypatch,
    *,
    applications: list[dict],
    balances: dict[tuple[str, str], list[dict]],
) -> None:
    application_repo = MagicMock()
    balance_repo = MagicMock()

    def _find_many(query=None, *, sort=None, skip=0, limit=20):
        query = query or {}
        results = list(applications)
        if query.get("employee_id"):
            results = [
                document
                for document in results
                if document.get("employee_id") == query["employee_id"]
            ]
        if query.get("leave_type"):
            results = [
                document
                for document in results
                if document.get("leave_type") == query["leave_type"]
            ]
        if query.get("status"):
            results = [
                document for document in results if document.get("status") == query["status"]
            ]
        return results[skip : skip + limit]

    def _count(query=None):
        return len(_find_many(query, skip=0, limit=10_000))

    application_repo.find_many.side_effect = _find_many
    application_repo.count.side_effect = _count
    application_repo.find_by_id.side_effect = lambda doc_id: next(
        (document for document in applications if document["_id"] == doc_id),
        None,
    )

    balance_repo.find_many.side_effect = lambda query=None, limit=1000: list(
        balances.get(
            (
                str((query or {}).get("employee", "")),
                str((query or {}).get("leave_type", "")),
            ),
            [],
        ),
    )

    monkeypatch.setattr(leave_application_routes, "_get_repo", lambda tenant_id: application_repo)
    monkeypatch.setattr(
        leave_application_routes,
        "_get_leave_balance_repo",
        lambda tenant_id: balance_repo,
    )


def test_휴가신청_목록은_워크벤치_요약과_상태배지를_반환한다(
    monkeypatch,
    test_client: MagicMock,
) -> None:
    """목록 조회는 승인 상태/잔액 리스크를 요약한 워크벤치 응답을 반환해야 한다."""

    _patch_workbench_repos(
        monkeypatch,
        applications=[
            {
                "_id": "LA-2026-00001",
                "employee_id": "EMP-001",
                "employee_name": "김직원",
                "leave_type": "연차",
                "from_date": "2026-04-14",
                "to_date": "2026-04-16",
                "total_days": 3,
                "status": "open",
                "reason": "가족 행사",
            },
            {
                "_id": "LA-2026-00002",
                "employee_id": "EMP-002",
                "employee_name": "박직원",
                "leave_type": "병가",
                "from_date": "2026-04-21",
                "to_date": "2026-04-21",
                "total_days": 1,
                "status": "approved",
                "reason": "병원 진료",
            },
            {
                "_id": "LA-2026-00003",
                "employee_id": "EMP-001",
                "employee_name": "김직원",
                "leave_type": "연차",
                "from_date": "2026-05-02",
                "to_date": "2026-05-05",
                "total_days": 4,
                "status": "open",
                "reason": "해외 출장 전 휴식",
            },
        ],
        balances={
            ("EMP-001", "연차"): [
                {
                    "_id": "LB-001",
                    "employee": "EMP-001",
                    "leave_type": "연차",
                    "total_allocated": 15,
                    "total_used": 12,
                    "balance": 3,
                }
            ],
            ("EMP-002", "병가"): [
                {
                    "_id": "LB-002",
                    "employee": "EMP-002",
                    "leave_type": "병가",
                    "total_allocated": 10,
                    "total_used": 1,
                    "balance": 9,
                }
            ],
        },
    )

    response = test_client.get(_BASE_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["summary"] == {
        "open_count": 2,
        "approved_count": 1,
        "rejected_count": 0,
        "pending_days": 7.0,
        "approved_days": 1.0,
        "insufficient_balance_count": 1,
        "employee_count": 2,
    }

    waiting_row = next(row for row in payload["data"] if row["id"] == "LA-2026-00001")
    approved_row = next(row for row in payload["data"] if row["id"] == "LA-2026-00002")

    assert waiting_row["status_badge"] == "pending_approval"
    assert waiting_row["recommended_action"] == "approve_or_reject"
    assert waiting_row["leave_balance_summary"]["remaining_days"] == 3.0
    assert waiting_row["leave_balance_summary"]["remaining_after_request"] == 0.0
    assert waiting_row["leave_balance_summary"]["has_sufficient_balance"] is True
    assert waiting_row["available_actions"] == ["approve", "reject", "delete"]

    assert approved_row["status_badge"] == "approved_deducted"
    assert approved_row["recommended_action"] == "review_attendance_sync"
    assert approved_row["period_summary"]["is_single_day"] is True


def test_휴가신청_요약은_잔액과_추천액션을_반환한다(
    monkeypatch,
    test_client: MagicMock,
) -> None:
    """상세 요약은 휴가 기간, 잔여 휴가, 운영 액션을 한 번에 보여줘야 한다."""

    _patch_workbench_repos(
        monkeypatch,
        applications=[
            {
                "_id": "LA-2026-00001",
                "employee_id": "EMP-001",
                "employee_name": "김직원",
                "leave_type": "연차",
                "from_date": "2026-04-14",
                "to_date": "2026-04-16",
                "total_days": 3,
                "status": "open",
                "reason": "가족 행사",
            }
        ],
        balances={
            ("EMP-001", "연차"): [
                {
                    "_id": "LB-001",
                    "employee": "EMP-001",
                    "leave_type": "연차",
                    "total_allocated": 15,
                    "total_used": 14,
                    "balance": 1,
                }
            ]
        },
    )

    response = test_client.get(f"{_BASE_URL}/LA-2026-00001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "pending_balance_review"
    assert payload["recommended_action"] == "adjust_leave_balance"
    assert payload["period_summary"] == {
        "from_date": "2026-04-14",
        "to_date": "2026-04-16",
        "total_days": 3.0,
        "is_single_day": False,
    }
    assert payload["leave_balance_summary"] == {
        "allocated_days": 15.0,
        "used_days": 14.0,
        "remaining_days": 1.0,
        "requested_days": 3.0,
        "remaining_after_request": -2.0,
        "has_sufficient_balance": False,
    }
    assert payload["available_actions"] == ["approve", "reject", "delete"]


def test_승인된_휴가신청은_삭제할_수_없다(
    monkeypatch,
    test_client: MagicMock,
) -> None:
    """OPEN 상태가 아닌 휴가 신청은 삭제할 수 없어야 한다."""

    application_repo = MagicMock()
    application_repo.find_by_id.return_value = {
        "_id": "LA-2026-00009",
        "employee_id": "EMP-009",
        "leave_type": "연차",
        "status": "approved",
    }
    monkeypatch.setattr(leave_application_routes, "_get_repo", lambda tenant_id: application_repo)

    response = test_client.delete(f"{_BASE_URL}/LA-2026-00009")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-032"
    assert "삭제" in response.json()["detail"]
    application_repo.delete_by_id.assert_not_called()
