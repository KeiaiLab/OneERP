"""구매 분석(Purchase Analytics) 워크벤치 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_buying_app.main import app

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


@patch("oneerp_buying_app.routes.purchase_analytics._get_scorecard_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_order_repo")
def test_구매분석_목록은_KPI와_차트번들을_반환한다(
    mock_order_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    mock_scorecard_repo: MagicMock,
) -> None:
    """GET /api/v1/purchase-analytics -- KPI/차트/행 액션을 함께 반환한다."""
    order_repo = MagicMock()
    order_repo.find_many.return_value = [
        {
            "_id": "PO-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "알파상사",
            "transaction_date": "2026-04-10",
            "grand_total": 150000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 10, "amount": 150000},
            ],
        },
        {
            "_id": "PO-002",
            "docstatus": 1,
            "supplier_id": "SUP-002",
            "supplier_name": "베타공업",
            "transaction_date": "2026-03-05",
            "grand_total": 80000,
            "items": [
                {"item_code": "ITEM-B", "item_name": "B 품목", "qty": 4, "amount": 80000},
            ],
        },
    ]
    invoice_repo = MagicMock()
    invoice_repo.find_many.return_value = [
        {
            "_id": "PI-001",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "알파상사",
            "posting_date": "2026-04-15",
            "due_date": "2020-01-01",
            "grand_total": 120000,
            "outstanding_amount": 120000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 8, "amount": 120000},
            ],
        },
        {
            "_id": "PI-002",
            "docstatus": 1,
            "supplier_id": "SUP-002",
            "supplier_name": "베타공업",
            "posting_date": "2026-03-12",
            "due_date": "2099-01-01",
            "grand_total": 60000,
            "outstanding_amount": 0,
            "items": [
                {"item_code": "ITEM-B", "item_name": "B 품목", "qty": 3, "amount": 60000},
            ],
        },
    ]
    scorecard_repo = MagicMock()
    scorecard_repo.find_many.return_value = [
        {"supplier": "SUP-001", "total_score": 72},
        {"supplier": "SUP-002", "total_score": 94},
    ]
    mock_order_repo.return_value = order_repo
    mock_invoice_repo.return_value = invoice_repo
    mock_scorecard_repo.return_value = scorecard_repo

    response = client.get("/api/v1/purchase-analytics?group_by=supplier&page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["summary"] == {
        "submitted_purchase_order_count": 2,
        "purchase_order_amount_total": 230000.0,
        "submitted_purchase_invoice_count": 2,
        "purchase_invoice_amount_total": 180000.0,
        "active_supplier_count": 2,
        "open_purchase_order_count": 2,
        "overdue_payable_count": 1,
        "best_supplier_name": "알파상사",
        "best_supplier_amount": 120000.0,
    }
    assert data["recommended_action"] == "review_overdue_payables"
    assert data["available_actions"] == [
        "open_purchase_orders",
        "open_purchase_invoices",
        "open_suppliers",
        "review_supplier_scorecards",
    ]
    first_row = data["data"][0]
    assert first_row["group_key"] == "SUP-001"
    assert first_row["status_badge"] == "payment_due"
    assert first_row["recommended_action"] == "review_payables"
    assert first_row["summary"] == {
        "purchase_order_count": 1,
        "purchase_invoice_count": 1,
        "overdue_payable_count": 1,
        "latest_scorecard_total": 72.0,
    }
    assert data["charts"]["purchase_trend"] == [
        {
            "period": "2026-03",
            "ordered_amount": 80000.0,
            "invoiced_amount": 60000.0,
            "qty": 4.0,
        },
        {
            "period": "2026-04",
            "ordered_amount": 150000.0,
            "invoiced_amount": 120000.0,
            "qty": 10.0,
        },
    ]
    assert data["charts"]["supplier_mix"][0]["supplier_name"] == "알파상사"
    pipeline = {row["status"]: row["count"] for row in data["charts"]["payable_pipeline"]}
    assert pipeline == {"overdue": 1, "settled": 1}


@patch("oneerp_buying_app.routes.purchase_analytics._get_scorecard_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_order_repo")
def test_구매분석은_status_badge_필터와_품목차트를_지원한다(
    mock_order_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    mock_scorecard_repo: MagicMock,
) -> None:
    """GET /api/v1/purchase-analytics -- 품목 관점 랭킹과 status_badge 필터를 지원한다."""
    order_repo = MagicMock()
    order_repo.find_many.return_value = [
        {
            "_id": "PO-101",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "알파상사",
            "transaction_date": "2026-04-10",
            "grand_total": 200000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 10, "amount": 150000},
                {"item_code": "ITEM-B", "item_name": "B 품목", "qty": 2, "amount": 50000},
            ],
        },
        {
            "_id": "PO-102",
            "docstatus": 1,
            "supplier_id": "SUP-002",
            "supplier_name": "베타공업",
            "transaction_date": "2026-04-11",
            "grand_total": 40000,
            "items": [
                {"item_code": "ITEM-C", "item_name": "C 품목", "qty": 1, "amount": 40000},
            ],
        },
    ]
    invoice_repo = MagicMock()
    invoice_repo.find_many.return_value = [
        {
            "_id": "PI-101",
            "docstatus": 1,
            "supplier_id": "SUP-001",
            "supplier_name": "알파상사",
            "posting_date": "2026-04-15",
            "due_date": "2099-01-01",
            "grand_total": 180000,
            "outstanding_amount": 180000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 8, "amount": 180000},
            ],
        }
    ]
    mock_order_repo.return_value = order_repo
    mock_invoice_repo.return_value = invoice_repo
    mock_scorecard_repo.return_value = MagicMock(find_many=MagicMock(return_value=[]))

    response = client.get("/api/v1/purchase-analytics?group_by=item&status_badge=top_spend_item")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["group_key"] == "ITEM-A"
    assert data["data"][0]["status_badge"] == "top_spend_item"
    assert data["charts"]["item_mix"][0]["item_code"] == "ITEM-A"


@patch("oneerp_buying_app.routes.purchase_analytics._get_scorecard_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_analytics._get_purchase_order_repo")
def test_구매분석_빈_결과는_0_요약과_빈_차트를_반환한다(
    mock_order_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    mock_scorecard_repo: MagicMock,
) -> None:
    """GET /api/v1/purchase-analytics -- 데이터가 없을 때도 워크벤치 기본 구조를 유지한다."""
    mock_order_repo.return_value = MagicMock(find_many=MagicMock(return_value=[]))
    mock_invoice_repo.return_value = MagicMock(find_many=MagicMock(return_value=[]))
    mock_scorecard_repo.return_value = MagicMock(find_many=MagicMock(return_value=[]))

    response = client.get("/api/v1/purchase-analytics")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []
    assert data["summary"] == {
        "submitted_purchase_order_count": 0,
        "purchase_order_amount_total": 0.0,
        "submitted_purchase_invoice_count": 0,
        "purchase_invoice_amount_total": 0.0,
        "active_supplier_count": 0,
        "open_purchase_order_count": 0,
        "overdue_payable_count": 0,
        "best_supplier_name": "",
        "best_supplier_amount": 0.0,
    }
    assert data["charts"] == {
        "purchase_trend": [],
        "supplier_mix": [],
        "item_mix": [],
        "payable_pipeline": [],
    }
