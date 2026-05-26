"""매입채무(Accounts Payable) 엔드포인트 단위 테스트."""

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


_BASE_URL = "/api/v1/accounts-payable"


def _cursor_with_docs(*docs: dict) -> MagicMock:
    """Repository.find_many 응답용 커서를 구성한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter(list(docs)))
    return mock_cursor


def test_매입채무_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts-payable — 매입채무 현황을 조회한다."""
    mock_collection.find.return_value = _cursor_with_docs(
        {
            "_id": "AP-2026-00001",
            "supplier": "공급업체A",
            "outstanding_amount": 500000,
            "aging_bucket": "0-30",
            "tenant_id": "default",
        },
    )
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


def test_매입채무_빈목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/accounts-payable — 데이터 없을 때 빈 목록을 반환한다."""
    mock_collection.find.return_value = _cursor_with_docs()
    response = client.get(_BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []


def test_매입채무_목록은_공급업체별_지급우선순위와_요약을_제공한다() -> None:
    """GET /api/v1/accounts-payable — 공급업체별 미지급금 추적과 후속 액션 힌트를 제공한다."""
    with patch("oneerp_accounting_app.routes.accounts_payable.Repository") as mock_repo_cls:
        ap_repo = MagicMock()

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            assert collection_name == "accounts_payable"
            return ap_repo

        mock_repo_cls.side_effect = _factory
        ap_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "AP-2026-00001",
                "supplier": "SUP-001",
                "supplier_name": "에이전트 공급업체",
                "outstanding_amount": 330000,
                "due_date": "2026-04-15",
                "invoice_id": "PI-001",
                "tenant_id": "default",
            },
            {
                "_id": "AP-2026-00002",
                "supplier": "SUP-001",
                "supplier_name": "에이전트 공급업체",
                "outstanding_amount": 120000,
                "due_date": "2026-04-27",
                "invoice_id": "PI-002",
                "tenant_id": "default",
            },
            {
                "_id": "AP-2026-00003",
                "supplier": "SUP-002",
                "supplier_name": "일반 공급업체",
                "outstanding_amount": 0,
                "due_date": "2026-04-05",
                "invoice_id": "PI-003",
                "tenant_id": "default",
            },
        )

        response = client.get(
            f"{_BASE_URL}"
            "?supplier=SUP-001"
            "&due_date_from=2026-04-01"
            "&due_date_to=2026-04-20"
            "&overdue_only=true"
            "&min_overdue_days=5"
            "&as_of_date=2026-04-25"
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "total_outstanding": 330000.0,
        "overdue_outstanding": 330000.0,
        "overdue_count": 1,
        "aging_buckets": {
            "current": {"count": 0, "amount": 0.0},
            "1-30": {"count": 1, "amount": 330000.0},
            "31-60": {"count": 0, "amount": 0.0},
            "61-90": {"count": 0, "amount": 0.0},
            "91+": {"count": 0, "amount": 0.0},
        },
        "supplier_count": 1,
        "priority_supplier_count": 1,
        "supplier_breakdown": [
            {
                "supplier": "SUP-001",
                "supplier_name": "에이전트 공급업체",
                "invoice_count": 1,
                "overdue_invoice_count": 1,
                "outstanding_amount": 330000.0,
                "overdue_outstanding": 330000.0,
                "max_overdue_days": 10,
                "next_due_date": "2026-04-15",
                "status_badge": "overdue",
                "recommended_action": "register_payment",
            }
        ],
    }
    payable = payload["data"][0]
    assert payable["supplier"] == "SUP-001"
    assert payable["supplier_name"] == "에이전트 공급업체"
    assert payable["invoice_id"] == "PI-001"
    assert payable["due_date"] == "2026-04-15"
    assert payable["overdue_days"] == 10
    assert payable["aging_bucket"] == "1-30"
    assert payable["status_badge"] == "overdue"
    assert payable["recommended_action"] == "register_payment"
    assert payable["available_actions"] == [
        "open_purchase_invoice",
        "register_payment",
        "create_payment_order",
    ]


def test_매입채무_상세는_공급업체_요약과_지급일정_맥락을_반환한다() -> None:
    """GET /api/v1/accounts-payable/{doc_id} — 공급업체별 미지급금 합계와 지급 일정 맥락을 제공한다."""
    with patch("oneerp_accounting_app.routes.accounts_payable.Repository") as mock_repo_cls:
        ap_repo = MagicMock()

        def _factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            assert collection_name == "accounts_payable"
            return ap_repo

        mock_repo_cls.side_effect = _factory
        ap_repo.find_by_id.return_value = {
            "_id": "AP-2026-00077",
            "supplier": "SUP-777",
            "supplier_name": "세부 공급업체",
            "outstanding_amount": 330000,
            "due_date": "2026-04-15",
            "invoice_id": "PI-777",
            "tenant_id": "default",
        }
        ap_repo.find_many.return_value = _cursor_with_docs(
            {
                "_id": "AP-2026-00077",
                "supplier": "SUP-777",
                "supplier_name": "세부 공급업체",
                "outstanding_amount": 330000,
                "due_date": "2026-04-15",
                "invoice_id": "PI-777",
                "tenant_id": "default",
            },
            {
                "_id": "AP-2026-00078",
                "supplier": "SUP-777",
                "supplier_name": "세부 공급업체",
                "outstanding_amount": 120000,
                "due_date": "2026-04-27",
                "invoice_id": "PI-778",
                "tenant_id": "default",
            },
        )

        response = client.get(f"{_BASE_URL}/AP-2026-00077?as_of_date=2026-04-25")

    assert response.status_code == 200
    payload = response.json()
    assert payload["_id"] == "AP-2026-00077"
    assert payload["status_badge"] == "overdue"
    assert payload["recommended_action"] == "register_payment"
    assert payload["available_actions"] == [
        "open_purchase_invoice",
        "register_payment",
        "create_payment_order",
    ]
    assert payload["payment_schedule_summary"] == {
        "overdue_invoice_count": 1,
        "due_within_7_days_count": 1,
        "due_today_count": 0,
        "settled_invoice_count": 0,
        "overdue_outstanding": 330000.0,
        "total_outstanding": 450000.0,
        "oldest_due_date": "2026-04-15",
        "next_due_date": "2026-04-27",
    }
    assert payload["supplier_summary"] == {
        "supplier": "SUP-777",
        "supplier_name": "세부 공급업체",
        "invoice_count": 2,
        "overdue_invoice_count": 1,
        "outstanding_amount": 450000.0,
        "overdue_outstanding": 330000.0,
        "max_overdue_days": 10,
        "next_due_date": "2026-04-27",
        "status_badge": "overdue",
        "recommended_action": "register_payment",
    }
