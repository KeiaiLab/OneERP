"""납품서(DeliveryNote) 커스텀 라우트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import oneerp_selling_app.routes.delivery_notes  # noqa: F401

_BASE_URL = "/api/v1/delivery-notes"


@patch("oneerp_selling_app.routes.delivery_notes.generate_name", return_value="DN-2026-00001")
@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_납품서_생성_정상(
    mock_get_repo: MagicMock,
    mock_name: MagicMock,
    test_client: MagicMock,
) -> None:
    """POST /api/v1/delivery-notes -- 정상 생성 시 id 응답을 반환한다."""
    repo = MagicMock()
    mock_get_repo.return_value = repo

    response = test_client.post(
        _BASE_URL,
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "posting_date": "2026-03-17",
            "items": [
                {"item_code": "ITEM-001", "item_name": "상품A", "qty": 5, "warehouse": "WH-001"},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "DN-2026-00001"
    insert_doc = repo.insert.call_args[0][0]
    assert insert_doc.items[0].amount == 0


@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_납품서_목록_조회(mock_get_repo: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/delivery-notes -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "DN-001", "customer_name": "고객", "docstatus": 0}]
    repo.count.return_value = 1
    mock_get_repo.return_value = repo

    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["data"][0]["status_badge"] == "draft"


@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_납품서_목록_응답에_상태배지와_후속송장요약을_포함한다(
    mock_get_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """GET /api/v1/delivery-notes -- 상태/후속 송장 요약과 필터 쿼리를 제공한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "DN-001",
            "docstatus": 1,
            "sales_order_ref": "SO-001",
            "transporter": "대한통운",
            "downstream_refs": {"sales_invoice_ids": ["SINV-001"]},
        }
    ]
    repo.count.return_value = 1
    mock_get_repo.return_value = repo

    response = test_client.get(
        f"{_BASE_URL}?status_badge=submitted&sales_order_ref=SO-001&transporter=대한통운",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"][0]["status_badge"] == "submitted"
    assert data["data"][0]["downstream_summary"] == {
        "sales_invoice_count": 1,
        "has_downstream_documents": True,
    }
    assert data["data"][0]["available_actions"] == ["create_sales_invoice", "cancel"]
    repo.find_many.assert_called_once()
    query = repo.find_many.call_args.args[0]
    assert query == {
        "docstatus": 1,
        "sales_order_ref": "SO-001",
        "transporter": "대한통운",
    }


@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_납품서_상세_조회_미존재_404(mock_get_repo: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/delivery-notes/{doc_id} -- 없는 납품서는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_get_repo.return_value = repo

    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")

    assert response.status_code == 404


@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_출고창고가_없는_납품서는_제출할_수_없다(
    mock_get_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """POST /api/v1/delivery-notes/{doc_id}/submit -- 출고 창고 미지정 시 제출을 막는다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "DN-001",
        "docstatus": 0,
        "items": [{"item_code": "ITEM-001", "qty": 1, "warehouse": ""}],
    }
    mock_get_repo.return_value = repo

    response = test_client.post(f"{_BASE_URL}/DN-001/submit")

    assert response.status_code == 400
    assert response.json()["detail"].startswith("ERR-SELL-050")
    repo.submit_with_event.assert_not_called()


@patch("oneerp_selling_app.routes.delivery_notes._get_sales_invoice_repo")
@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
@patch("oneerp_selling_app.routes.delivery_notes.generate_name", return_value="SINV-2026-00001")
def test_제출된_납품서에서_판매송장_초안을_생성한다(
    mock_name: MagicMock,
    mock_get_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """POST /api/v1/delivery-notes/{doc_id}/sales-invoice -- 제출된 납품서에서 송장 초안을 만든다."""
    delivery_repo = MagicMock()
    delivery_repo.find_by_id.return_value = {
        "_id": "DN-001",
        "docstatus": 1,
        "customer_id": "CUST-001",
        "customer_name": "납품 고객",
        "sales_partner_id": "SPAR-001",
        "sales_partner_name": "총판A",
        "sales_partner_commission_rate": 7.5,
        "posting_date": "2026-04-09",
        "sales_order_ref": "SO-001",
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "품목A",
                "qty": 3,
                "rate": 2000,
                "amount": 6000,
                "warehouse": "WH-001",
            },
            {
                "item_code": "ITEM-002",
                "item_name": "품목B",
                "qty": 1,
                "rate": 4000,
                "amount": 4000,
                "warehouse": "WH-001",
            },
        ],
        "downstream_refs": {"sales_invoice_ids": []},
    }
    invoice_repo = MagicMock()
    mock_get_repo.return_value = delivery_repo
    mock_invoice_repo.return_value = invoice_repo

    response = test_client.post(
        f"{_BASE_URL}/DN-001/sales-invoice",
        json={
            "posting_date": "2026-04-09",
            "due_date": "2026-05-09",
            "taxes": [{"tax_type": "VAT", "rate": 10, "amount": 1000}],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "SINV-2026-00001"
    assert response.json()["downstream_summary"] == {
        "sales_invoice_count": 1,
        "has_downstream_documents": True,
    }
    insert_doc = invoice_repo.insert.call_args[0][0]
    assert insert_doc.delivery_note_ref == "DN-001"
    assert insert_doc.sales_order_ref == "SO-001"
    assert insert_doc.sales_partner_id == "SPAR-001"
    assert insert_doc.sales_partner_name == "총판A"
    assert insert_doc.sales_partner_commission_rate == 7.5
    assert insert_doc.net_total == 10000
    assert insert_doc.grand_total == 11000
    delivery_repo.update_by_id.assert_called_once_with(
        "DN-001",
        {
            "downstream_refs": {"sales_invoice_ids": ["SINV-2026-00001"]},
            "updated_by": "test-user",
        },
    )


@patch("oneerp_selling_app.routes.delivery_notes._get_sales_invoice_repo")
@patch("oneerp_selling_app.routes.delivery_notes._get_repo")
def test_초안_납품서에서는_판매송장_초안_생성을_거부한다(
    mock_get_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """POST /api/v1/delivery-notes/{doc_id}/sales-invoice -- 초안 납품서는 송장 초안을 만들 수 없다."""
    delivery_repo = MagicMock()
    delivery_repo.find_by_id.return_value = {
        "_id": "DN-001",
        "docstatus": 0,
        "customer_id": "CUST-001",
        "customer_name": "납품 고객",
        "items": [{"item_code": "ITEM-001", "qty": 3}],
    }
    mock_get_repo.return_value = delivery_repo
    mock_invoice_repo.return_value = MagicMock()

    response = test_client.post(f"{_BASE_URL}/DN-001/sales-invoice", json={})

    assert response.status_code == 400
