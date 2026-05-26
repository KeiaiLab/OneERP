"""예산(Budget) 워크벤치 API 테스트."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app
from oneerp_core.document import DocStatus

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


@patch("oneerp_accounting_app.routes.budgets._get_budget_transfer_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_budget_version_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_repo")
@patch("oneerp_accounting_app.routes.budgets.generate_name", return_value="BGT-2026-00001")
def test_예산_생성은_워크벤치_초기값을_반환한다(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_transfer_repo: MagicMock,
) -> None:
    """예산 생성 시 잔여액/배지까지 포함한 초기 워크벤치 응답을 반환해야 한다."""
    repo = MagicMock()
    mock_repo.return_value = repo
    mock_version_repo.return_value.find_many.return_value = []
    mock_transfer_repo.return_value.find_many.return_value = []

    response = client.post(
        "/api/v1/budgets",
        json={
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-2026-00001",
            "budget_amount": 10000000,
            "actual_amount": 1500000,
            "items": [
                {
                    "account": "ACC-001",
                    "budget_amount": 7000000,
                    "actual_amount": 1000000,
                    "idx": 1,
                },
                {
                    "account": "ACC-002",
                    "budget_amount": 3000000,
                    "actual_amount": 500000,
                    "idx": 2,
                },
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "BGT-2026-00001"
    assert payload["budget_name"] == "영업본부 2026 예산"
    assert payload["remaining_amount"] == 8500000.0
    assert payload["status_badge"] == "draft"
    assert payload["budget_usage_summary"] == {
        "total_amount": 10000000.0,
        "spent_amount": 1500000.0,
        "remaining_amount": 8500000.0,
        "utilization_rate": 15.0,
        "line_item_count": 2,
        "over_budget_item_count": 0,
    }


@patch("oneerp_accounting_app.routes.budgets._get_budget_transfer_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_budget_version_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_repo")
def test_예산_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_transfer_repo: MagicMock,
) -> None:
    """예산 목록은 예산 집행 상태와 이전 필요 여부를 한 번에 보여줘야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "BGT-OVER",
            "budget_name": "생산본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-PROD",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(1200000),
            "docstatus": DocStatus.SUBMITTED,
            "items": [
                {
                    "account": "ACC-001",
                    "budget_amount": Decimal(1000000),
                    "actual_amount": Decimal(1200000),
                }
            ],
        },
        {
            "_id": "BGT-NEAR",
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-SALES",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(920000),
            "docstatus": DocStatus.SUBMITTED,
            "items": [
                {
                    "account": "ACC-002",
                    "budget_amount": Decimal(1000000),
                    "actual_amount": Decimal(920000),
                }
            ],
        },
        {
            "_id": "BGT-DRAFT",
            "budget_name": "R&D 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-RND",
            "budget_amount": Decimal(500000),
            "actual_amount": Decimal(50000),
            "docstatus": DocStatus.DRAFT,
            "items": [],
        },
    ]
    mock_repo.return_value = repo

    version_repo = MagicMock()
    version_repo.find_many.side_effect = lambda query, **_: {
        "BGT-OVER": [{"version_no": 3, "version_name": "Q2 조정안", "is_current": True}],
        "BGT-NEAR": [{"version_no": 2, "version_name": "영업본부 조정안", "is_current": True}],
        "BGT-DRAFT": [],
    }[query["budget_id"]]
    mock_version_repo.return_value = version_repo

    transfer_repo = MagicMock()
    transfer_repo.find_many.side_effect = lambda query, **_: {
        "BGT-OVER": [
            {
                "_id": "BTR-001",
                "from_budget_id": "BGT-OVER",
                "to_budget_id": "BGT-NEAR",
                "transfer_amount": Decimal(150000),
                "status": "approved",
                "transfer_date": "2026-04-01",
            }
        ],
        "BGT-NEAR": [],
        "BGT-DRAFT": [],
    }[
        next(
            item
            for clause in query["$or"]
            for item in (clause.get("from_budget_id"), clause.get("to_budget_id"))
            if item is not None
        )
    ]
    mock_transfer_repo.return_value = transfer_repo

    response = client.get("/api/v1/budgets?status_badge=over_budget&page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "draft_count": 0,
        "submitted_count": 1,
        "cancelled_count": 0,
        "over_budget_count": 1,
        "near_limit_count": 0,
        "pending_transfer_count": 1,
        "total_amount": 1000000.0,
        "spent_amount": 1200000.0,
        "remaining_amount": -200000.0,
    }
    assert payload["data"][0]["budget_name"] == "생산본부 2026 예산"
    assert payload["data"][0]["status_badge"] == "over_budget"
    assert payload["data"][0]["recommended_action"] == "create_budget_transfer"
    assert payload["data"][0]["transfer_summary"]["pending_transfer_count"] == 1


@patch("oneerp_accounting_app.routes.budgets._get_budget_transfer_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_budget_version_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_repo")
def test_예산_상세는_집행률과_버전_이전_요약을_반환한다(
    mock_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_transfer_repo: MagicMock,
) -> None:
    """예산 상세는 초과 경고와 버전/이전 현황을 함께 보여줘야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "BGT-2026-00001",
        "budget_name": "영업본부 2026 예산",
        "fiscal_year": "FY-2026",
        "cost_center": "CC-SALES",
        "budget_amount": Decimal(1000000),
        "actual_amount": Decimal(950000),
        "docstatus": DocStatus.SUBMITTED,
        "items": [
            {
                "account": "ACC-001",
                "budget_amount": Decimal(600000),
                "actual_amount": Decimal(620000),
            },
            {
                "account": "ACC-002",
                "budget_amount": Decimal(400000),
                "actual_amount": Decimal(330000),
            },
        ],
    }
    mock_repo.return_value = repo

    version_repo = MagicMock()
    version_repo.find_many.return_value = [
        {
            "_id": "BVER-002",
            "version_no": 2,
            "version_name": "Q2 조정안",
            "is_current": True,
            "status": "approved",
        },
        {
            "_id": "BVER-001",
            "version_no": 1,
            "version_name": "초기안",
            "is_current": False,
            "status": "locked",
        },
    ]
    mock_version_repo.return_value = version_repo

    transfer_repo = MagicMock()
    transfer_repo.find_many.return_value = [
        {
            "_id": "BTR-001",
            "from_budget_id": "BGT-2026-00001",
            "to_budget_id": "BGT-2026-00002",
            "transfer_amount": Decimal(150000),
            "status": "approved",
            "transfer_date": "2026-04-01",
        },
        {
            "_id": "BTR-002",
            "from_budget_id": "BGT-2026-00003",
            "to_budget_id": "BGT-2026-00001",
            "transfer_amount": Decimal(50000),
            "status": "executed",
            "transfer_date": "2026-03-15",
        },
    ]
    mock_transfer_repo.return_value = transfer_repo

    response = client.get("/api/v1/budgets/BGT-2026-00001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "near_limit"
    assert payload["recommended_action"] == "review_budget_transfer"
    assert payload["budget_usage_summary"] == {
        "total_amount": 1000000.0,
        "spent_amount": 950000.0,
        "remaining_amount": 50000.0,
        "utilization_rate": 95.0,
        "line_item_count": 2,
        "over_budget_item_count": 1,
    }
    assert payload["version_summary"] == {
        "version_count": 2,
        "approved_version_count": 1,
        "locked_version_count": 1,
        "current_version_no": 2,
        "current_version_name": "Q2 조정안",
    }
    assert payload["transfer_summary"] == {
        "pending_transfer_count": 1,
        "executed_transfer_count": 1,
        "outbound_transfer_amount": 150000.0,
        "inbound_transfer_amount": 50000.0,
        "latest_transfer_date": "2026-04-01",
    }
    assert payload["available_actions"] == [
        "cancel",
        "open_budget_versions",
        "open_budget_transfers",
        "create_budget_transfer",
    ]


@patch("oneerp_accounting_app.routes.budgets._get_budget_transfer_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_budget_version_repo", create=True)
@patch("oneerp_accounting_app.routes.budgets._get_repo")
def test_예산_제출과_취소가_상태를_갱신한다(
    mock_repo: MagicMock,
    mock_version_repo: MagicMock,
    mock_transfer_repo: MagicMock,
) -> None:
    """예산 제출/취소는 예산 워크벤치 응답에 새로운 docstatus를 반영해야 한다."""
    repo = MagicMock()
    repo.find_by_id.side_effect = [
        {
            "_id": "BGT-2026-00001",
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-SALES",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(100000),
            "docstatus": DocStatus.DRAFT,
            "items": [],
        },
        {
            "_id": "BGT-2026-00001",
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-SALES",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(100000),
            "docstatus": DocStatus.SUBMITTED,
            "items": [],
        },
        {
            "_id": "BGT-2026-00001",
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-SALES",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(100000),
            "docstatus": DocStatus.SUBMITTED,
            "items": [],
        },
        {
            "_id": "BGT-2026-00001",
            "budget_name": "영업본부 2026 예산",
            "fiscal_year": "FY-2026",
            "cost_center": "CC-SALES",
            "budget_amount": Decimal(1000000),
            "actual_amount": Decimal(100000),
            "docstatus": DocStatus.CANCELLED,
            "items": [],
        },
    ]
    mock_repo.return_value = repo
    mock_version_repo.return_value.find_many.return_value = []
    mock_transfer_repo.return_value.find_many.return_value = []

    submit_response = client.post("/api/v1/budgets/BGT-2026-00001/submit")
    cancel_response = client.post("/api/v1/budgets/BGT-2026-00001/cancel")

    assert submit_response.status_code == 200
    assert submit_response.json()["docstatus"] == DocStatus.SUBMITTED
    assert submit_response.json()["status_badge"] == "within_budget"

    assert cancel_response.status_code == 200
    assert cancel_response.json()["docstatus"] == DocStatus.CANCELLED
    assert cancel_response.json()["status_badge"] == "cancelled"
