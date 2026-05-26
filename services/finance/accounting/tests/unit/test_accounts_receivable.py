"""매출채권(Accounts Receivable) 엔드포인트 단위 테스트."""

from __future__ import annotations

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


_BASE_URL = "/api/v1/accounts-receivable"


def _cursor_with_docs(*docs: dict) -> MagicMock:
    """Repository.find_many 응답용 커서를 구성한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter(list(docs)))
    return mock_cursor


def test_매출채권_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts-receivable — 매출채권 현황을 조회한다."""
    mock_collection.find.return_value = _cursor_with_docs(
        {
            "_id": "AREC-2026-00001",
            "customer": "고객A",
            "outstanding_amount": 1000000,
            "aging_bucket": "0-30",
            "tenant_id": "default",
        },
    )
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


def test_매출채권_빈목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts-receivable — 데이터 없을 때 빈 목록을 반환한다."""
    mock_collection.find.return_value = _cursor_with_docs()
    response = client.get(_BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []


def test_매출채권_목록은_고객요약과_수금우선순위를_제공한다() -> None:
    """GET /api/v1/accounts-receivable — 고객별 미수금 추적과 후속 액션 힌트를 제공한다."""
    with patch("oneerp_accounting_app.routes.accounts_receivable.Repository") as mock_repo_cls:
        ar_repo = MagicMock()
        dunning_repo = MagicMock()

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name == "accounts_receivable":
                return ar_repo
            if collection_name == "dunnings":
                return dunning_repo
            raise AssertionError(f"unexpected collection: {collection_name}")

        mock_repo_cls.side_effect = _factory
        ar_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "AREC-2026-00001",
                "customer": "CUST-001",
                "customer_name": "에이전트 상사",
                "outstanding_amount": 120000,
                "due_date": "2026-04-10",
                "invoice_id": "SINV-001",
                "tenant_id": "default",
            },
            {
                "_id": "AREC-2026-00002",
                "customer": "CUST-001",
                "customer_name": "에이전트 상사",
                "outstanding_amount": 45000,
                "due_date": "2026-04-24",
                "invoice_id": "SINV-002",
                "tenant_id": "default",
            },
            {
                "_id": "AREC-2026-00003",
                "customer": "CUST-002",
                "customer_name": "지연 고객",
                "outstanding_amount": 88000,
                "due_date": "2026-02-05",
                "invoice_id": "SINV-003",
                "tenant_id": "default",
            },
        )
        dunning_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "DUN-2026-00003",
                "customer": "CUST-001",
                "dunning_level": 1,
                "dunning_fee": 1200,
                "dunning_date": "2026-04-15",
                "docstatus": 1,
                "tenant_id": "default",
            }
        )

        response = client.get(
            f"{_BASE_URL}"
            "?customer=CUST-001"
            "&due_date_from=2026-04-01"
            "&due_date_to=2026-04-20"
            "&overdue_only=true"
            "&min_overdue_days=5"
            "&as_of_date=2026-04-20"
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"]["customer_count"] == 1
    assert payload["summary"]["priority_customer_count"] == 1
    assert payload["summary"]["customer_breakdown"][0] == {
        "customer": "CUST-001",
        "customer_name": "에이전트 상사",
        "invoice_count": 1,
        "overdue_invoice_count": 1,
        "outstanding_amount": 120000.0,
        "overdue_outstanding": 120000.0,
        "max_overdue_days": 10,
        "collection_status": "dunning_in_progress",
        "recommended_action": "review_dunning",
        "latest_dunning_level": 1,
        "latest_dunning_id": "DUN-2026-00003",
    }
    receivable = payload["data"][0]
    assert receivable["customer"] == "CUST-001"
    assert receivable["invoice_id"] == "SINV-001"
    assert receivable["overdue_days"] == 10
    assert receivable["aging_bucket"] == "1-30"
    assert receivable["collection_status"] == "dunning_in_progress"
    assert receivable["recommended_action"] == "review_dunning"
    assert receivable["available_actions"] == [
        "open_invoice",
        "register_payment",
        "view_dunning_history",
    ]


def test_매출채권_상세는_독촉요약과_고객스냅샷을_반환한다() -> None:
    """GET /api/v1/accounts-receivable/{doc_id} — 상세 조회에서 독촉 이력과 후속 액션을 확인한다."""
    with patch("oneerp_accounting_app.routes.accounts_receivable.Repository") as mock_repo_cls:
        ar_repo = MagicMock()
        dunning_repo = MagicMock()

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            if collection_name == "accounts_receivable":
                return ar_repo
            if collection_name == "dunnings":
                return dunning_repo
            raise AssertionError(f"unexpected collection: {collection_name}")

        mock_repo_cls.side_effect = _factory
        ar_repo.find_by_id.return_value = {
            "_id": "AREC-2026-00077",
            "customer": "CUST-777",
            "customer_name": "세부 고객",
            "outstanding_amount": 330000,
            "due_date": "2026-01-31",
            "invoice_id": "SINV-777",
            "tenant_id": "default",
        }
        ar_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "AREC-2026-00077",
                "customer": "CUST-777",
                "customer_name": "세부 고객",
                "outstanding_amount": 330000,
                "due_date": "2026-01-31",
                "invoice_id": "SINV-777",
                "tenant_id": "default",
            },
            {
                "_id": "AREC-2026-00078",
                "customer": "CUST-777",
                "customer_name": "세부 고객",
                "outstanding_amount": 120000,
                "due_date": "2026-03-05",
                "invoice_id": "SINV-778",
                "tenant_id": "default",
            },
        )
        dunning_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "DUN-2026-00077",
                "customer": "CUST-777",
                "dunning_level": 2,
                "dunning_fee": 6600,
                "dunning_date": "2026-04-01",
                "docstatus": 1,
                "tenant_id": "default",
            },
            {
                "_id": "DUN-2026-00078",
                "customer": "CUST-777",
                "dunning_level": 1,
                "dunning_fee": 2200,
                "dunning_date": "2026-03-01",
                "docstatus": 0,
                "tenant_id": "default",
            },
        )

        response = client.get(f"{_BASE_URL}/AREC-2026-00077?as_of_date=2026-04-20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["_id"] == "AREC-2026-00077"
    assert payload["collection_status"] == "critical_dunning"
    assert payload["recommended_action"] == "call_customer"
    assert payload["available_actions"] == [
        "open_invoice",
        "register_payment",
        "view_dunning_history",
    ]
    assert payload["dunning_summary"] == {
        "latest_dunning_id": "DUN-2026-00077",
        "latest_dunning_level": 2,
        "active_dunning_count": 2,
        "latest_dunning_date": "2026-04-01",
        "total_dunning_fee": 8800.0,
    }
    assert payload["customer_summary"] == {
        "customer": "CUST-777",
        "customer_name": "세부 고객",
        "invoice_count": 2,
        "overdue_invoice_count": 2,
        "outstanding_amount": 450000.0,
        "overdue_outstanding": 450000.0,
        "max_overdue_days": 79,
        "collection_status": "critical_dunning",
        "recommended_action": "call_customer",
        "latest_dunning_level": 2,
        "latest_dunning_id": "DUN-2026-00077",
    }
