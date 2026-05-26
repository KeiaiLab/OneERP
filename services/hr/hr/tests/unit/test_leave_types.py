"""휴가유형(LeaveType) 워크벤치 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import oneerp_hr_app.routes.leave_types as leave_type_routes

_BASE_URL = "/api/v1/leave-types"


def _patch_workbench_repos(monkeypatch, *, leave_types, policies, balances, applications) -> None:
    leave_type_repo = MagicMock()
    leave_policy_repo = MagicMock()
    leave_balance_repo = MagicMock()
    leave_application_repo = MagicMock()

    leave_type_repo.find_many.return_value = leave_types
    leave_type_repo.find_by_id.side_effect = lambda doc_id: next(
        (document for document in leave_types if document["_id"] == doc_id),
        None,
    )
    leave_type_repo.count.return_value = 0

    leave_policy_repo.find_many.side_effect = lambda query=None, limit=1000: list(
        policies.get((query or {}).get("leave_type_id", ""), []),
    )
    leave_policy_repo.count.side_effect = lambda query=None: len(
        policies.get((query or {}).get("leave_type_id", ""), []),
    )

    leave_balance_repo.find_many.side_effect = lambda query=None, limit=1000: list(
        balances.get((query or {}).get("leave_type", ""), []),
    )
    leave_balance_repo.count.side_effect = lambda query=None: len(
        balances.get((query or {}).get("leave_type", ""), []),
    )

    leave_application_repo.find_many.side_effect = lambda query=None, limit=1000: list(
        applications.get((query or {}).get("leave_type", ""), []),
    )
    leave_application_repo.count.side_effect = lambda query=None: len(
        applications.get((query or {}).get("leave_type", ""), []),
    )

    monkeypatch.setattr(
        leave_type_routes, "_get_leave_type_repo", lambda tenant_id: leave_type_repo
    )
    monkeypatch.setattr(
        leave_type_routes, "_get_leave_policy_repo", lambda tenant_id: leave_policy_repo
    )
    monkeypatch.setattr(
        leave_type_routes, "_get_leave_balance_repo", lambda tenant_id: leave_balance_repo
    )
    monkeypatch.setattr(
        leave_type_routes,
        "_get_leave_application_repo",
        lambda tenant_id: leave_application_repo,
    )


def test_휴가유형_생성은_public_id를_반환한다(monkeypatch, test_client: MagicMock) -> None:
    """휴가유형 생성 응답은 id/_id를 모두 제공해야 한다."""
    repo = MagicMock()
    monkeypatch.setattr(leave_type_routes, "_get_leave_type_repo", lambda tenant_id: repo)
    monkeypatch.setattr(
        leave_type_routes, "generate_name", lambda prefix, **kwargs: "LT-2026-00001"
    )
    repo.find_many.return_value = []

    response = test_client.post(
        _BASE_URL,
        json={
            "leave_type_name": "연차",
            "max_leaves_allowed": 15,
            "is_carry_forward": True,
            "is_paid": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "LT-2026-00001"
    assert data["_id"] == "LT-2026-00001"
    assert data["leave_type_name"] == "연차"


def test_중복_휴가유형명은_생성할_수_없다(monkeypatch, test_client: MagicMock) -> None:
    """동일한 휴가유형명은 중복 생성할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "LT-2026-00001", "leave_type_name": "연차"}]
    monkeypatch.setattr(leave_type_routes, "_get_leave_type_repo", lambda tenant_id: repo)

    response = test_client.post(
        _BASE_URL,
        json={
            "leave_type_name": "연차",
            "max_leaves_allowed": 15,
            "is_carry_forward": True,
            "is_paid": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["error"] == "conflict"


def test_휴가유형_목록은_워크벤치_요약과_상태배지를_반환한다(
    monkeypatch,
    test_client: MagicMock,
) -> None:
    """목록 조회는 정책/잔액/신청 요약과 상태 배지를 함께 반환해야 한다."""
    _patch_workbench_repos(
        monkeypatch,
        leave_types=[
            {
                "_id": "LT-2026-00001",
                "leave_type_name": "연차",
                "max_leaves_allowed": 15,
                "is_carry_forward": True,
                "is_paid": True,
            },
            {
                "_id": "LT-2026-00002",
                "leave_type_name": "병가",
                "max_leaves_allowed": 30,
                "is_carry_forward": False,
                "is_paid": False,
            },
        ],
        policies={
            "LT-2026-00001": [
                {
                    "_id": "LVPL-001",
                    "leave_type_id": "LT-2026-00001",
                    "status": "active",
                    "max_carry_forward_days": 5,
                }
            ],
            "LT-2026-00002": [],
        },
        balances={
            "연차": [
                {
                    "_id": "LB-001",
                    "employee": "EMP-001",
                    "leave_type": "연차",
                    "total_allocated": Decimal(15),
                    "balance": Decimal(8),
                }
            ],
            "병가": [],
        },
        applications={
            "연차": [
                {"_id": "LA-001", "leave_type": "연차", "status": "open"},
                {"_id": "LA-002", "leave_type": "연차", "status": "approved"},
            ],
            "병가": [],
        },
    )

    response = test_client.get(_BASE_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["summary"] == {
        "paid_type_count": 1,
        "carry_forward_type_count": 1,
        "request_backlog_count": 1,
        "policy_unassigned_count": 1,
        "total_balance_days": 8.0,
    }
    annual_leave = next(row for row in payload["data"] if row["id"] == "LT-2026-00001")
    sick_leave = next(row for row in payload["data"] if row["id"] == "LT-2026-00002")
    assert annual_leave["status_badge"] == "request_backlog"
    assert annual_leave["summary"]["policy_count"] == 1
    assert annual_leave["summary"]["open_application_count"] == 1
    assert annual_leave["recommended_action"] == "review_open_requests"
    assert sick_leave["status_badge"] == "policy_unassigned"
    assert sick_leave["available_actions"][1] == "create_leave_policy"


def test_휴가유형_요약은_정책과_사용현황_권장액션을_반환한다(
    monkeypatch,
    test_client: MagicMock,
) -> None:
    """상세 요약은 carry-forward와 사용 현황을 한 번에 보여줘야 한다."""
    _patch_workbench_repos(
        monkeypatch,
        leave_types=[
            {
                "_id": "LT-2026-00001",
                "leave_type_name": "연차",
                "max_leaves_allowed": 15,
                "is_carry_forward": True,
                "is_paid": True,
            }
        ],
        policies={
            "LT-2026-00001": [
                {
                    "_id": "LVPL-001",
                    "leave_type_id": "LT-2026-00001",
                    "status": "active",
                    "max_carry_forward_days": 5,
                }
            ]
        },
        balances={
            "연차": [
                {
                    "_id": "LB-001",
                    "employee": "EMP-001",
                    "leave_type": "연차",
                    "total_allocated": Decimal(15),
                    "balance": Decimal(8),
                }
            ]
        },
        applications={"연차": []},
    )

    response = test_client.get(f"{_BASE_URL}/LT-2026-00001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "paid_carry_forward"
    assert payload["summary"] == {
        "policy_count": 1,
        "active_policy_count": 1,
        "balance_employee_count": 1,
        "open_application_count": 0,
        "approved_application_count": 0,
        "total_allocated_days": 15.0,
        "total_balance_days": 8.0,
        "max_carry_forward_days": 5.0,
    }
    assert payload["recommended_action"] == "review_year_end_rollover"
    assert payload["available_actions"] == [
        "edit",
        "open_leave_policies",
        "open_leave_balances",
        "review_carry_forward_policy",
    ]


def test_사용이력이_있는_휴가유형은_삭제할_수_없다(monkeypatch, test_client: MagicMock) -> None:
    """정책/잔액/휴가신청에 연결된 휴가유형은 삭제를 차단해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "LT-2026-00001",
        "leave_type_name": "연차",
        "max_leaves_allowed": 15,
        "is_carry_forward": True,
        "is_paid": True,
    }
    monkeypatch.setattr(leave_type_routes, "_get_leave_type_repo", lambda tenant_id: repo)
    monkeypatch.setattr(leave_type_routes, "_has_linked_usage", lambda tenant_id, leave_type: True)

    response = test_client.delete(f"{_BASE_URL}/LT-2026-00001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-050"
    repo.delete_by_id.assert_not_called()
