"""판매 분석(SalesAnalytics) 워크벤치 엔드포인트 테스트.

Route → Service 분리 후 SalesAnalyticsService 를 mock 한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_selling_app.main import app

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


def _make_service(invoices: list, quotations: list) -> MagicMock:
    service = MagicMock()
    service.load_invoices.return_value = invoices
    service.load_quotations.return_value = quotations
    return service


@patch("oneerp_selling_app.routes.sales_analytics.SalesAnalyticsService")
def test_판매분석_목록은_워크벤치_요약과_차트번들을_반환한다(
    mock_service_cls: MagicMock,
) -> None:
    """GET /api/v1/sales-analytics -- KPI 요약/차트/행 액션을 함께 반환한다."""
    invoices = [
        {
            "_id": "SINV-001",
            "docstatus": 1,
            "customer_id": "CUST-001",
            "customer_name": "알파상사",
            "posting_date": "2026-04-10",
            "grand_total": 160000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 4, "amount": 100000},
                {"item_code": "ITEM-B", "item_name": "B 품목", "qty": 2, "amount": 60000},
            ],
        },
        {
            "_id": "SINV-002",
            "docstatus": 1,
            "customer_id": "CUST-002",
            "customer_name": "베타유통",
            "posting_date": "2026-03-05",
            "grand_total": 90000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 1, "amount": 90000},
            ],
        },
    ]
    quotations = [
        {
            "_id": "QTN-001",
            "docstatus": 1,
            "customer_id": "CUST-001",
            "customer_name": "알파상사",
            "valid_till": "2020-01-01",
            "grand_total": 50000,
        },
        {
            "_id": "QTN-002",
            "docstatus": 1,
            "customer_id": "CUST-002",
            "customer_name": "베타유통",
            "valid_till": "2099-01-01",
            "grand_total": 30000,
            "converted_to": "SO-001",
        },
    ]
    mock_service_cls.return_value = _make_service(invoices, quotations)

    response = client.get("/api/v1/sales-analytics?group_by=customer&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["summary"] == {
        "submitted_invoice_count": 2,
        "invoice_amount_total": 250000.0,
        "active_customer_count": 2,
        "open_quotation_count": 1,
        "stale_quotation_count": 1,
        "best_customer_name": "알파상사",
        "best_customer_amount": 160000.0,
    }
    assert data["recommended_action"] == "review_stale_quotations"
    assert data["available_actions"] == [
        "open_quotations",
        "open_sales_orders",
        "open_sales_invoices",
    ]
    first_row = data["data"][0]
    assert first_row["group_key"] == "CUST-001"
    assert first_row["status_badge"] == "top_customer"
    assert first_row["recommended_action"] == "expand_account_plan"
    assert first_row["available_actions"] == [
        "open_customer",
        "open_sales_invoices",
        "review_margin",
    ]
    assert data["charts"]["sales_trend"] == [
        {"period": "2026-03", "amount": 90000.0, "qty": 1.0},
        {"period": "2026-04", "amount": 160000.0, "qty": 6.0},
    ]
    assert data["charts"]["customer_mix"][0]["customer_name"] == "알파상사"
    pipeline = {row["status"]: row["count"] for row in data["charts"]["quotation_pipeline"]}
    assert pipeline == {"converted": 1, "stale": 1}


@patch("oneerp_selling_app.routes.sales_analytics.SalesAnalyticsService")
def test_판매분석은_status_badge_필터와_품목차트를_지원한다(
    mock_service_cls: MagicMock,
) -> None:
    """GET /api/v1/sales-analytics -- 품목 관점 랭킹과 status_badge 필터를 지원한다."""
    invoices = [
        {
            "_id": "SINV-101",
            "docstatus": 1,
            "customer_id": "CUST-001",
            "customer_name": "알파상사",
            "posting_date": "2026-04-10",
            "grand_total": 200000,
            "items": [
                {"item_code": "ITEM-A", "item_name": "A 품목", "qty": 10, "amount": 150000},
                {"item_code": "ITEM-B", "item_name": "B 품목", "qty": 2, "amount": 50000},
            ],
        },
        {
            "_id": "SINV-102",
            "docstatus": 1,
            "customer_id": "CUST-002",
            "customer_name": "베타유통",
            "posting_date": "2026-04-11",
            "grand_total": 40000,
            "items": [
                {"item_code": "ITEM-C", "item_name": "C 품목", "qty": 1, "amount": 40000},
            ],
        },
    ]
    mock_service_cls.return_value = _make_service(invoices, [])

    response = client.get("/api/v1/sales-analytics?group_by=item&status_badge=best_seller")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["group_key"] == "ITEM-A"
    assert data["data"][0]["status_badge"] == "best_seller"
    assert data["charts"]["item_mix"][0]["item_code"] == "ITEM-A"


@patch("oneerp_selling_app.routes.sales_analytics.SalesAnalyticsService")
def test_판매분석_빈_결과는_0_요약과_빈_차트를_반환한다(
    mock_service_cls: MagicMock,
) -> None:
    """GET /api/v1/sales-analytics -- 데이터가 없을 때도 워크벤치 기본 구조를 유지한다."""
    mock_service_cls.return_value = _make_service([], [])

    response = client.get("/api/v1/sales-analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []
    assert data["summary"] == {
        "submitted_invoice_count": 0,
        "invoice_amount_total": 0.0,
        "active_customer_count": 0,
        "open_quotation_count": 0,
        "stale_quotation_count": 0,
        "best_customer_name": "",
        "best_customer_amount": 0.0,
    }
    assert data["charts"] == {
        "sales_trend": [],
        "customer_mix": [],
        "item_mix": [],
        "quotation_pipeline": [],
    }
