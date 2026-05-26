"""구매송장(PurchaseInvoice) CRUD 엔드포인트 테스트."""

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


@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
@patch("oneerp_buying_app.routes.purchase_invoices.generate_name", return_value="PI-2026-00001")
def test_구매송장_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-invoices -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/purchase-invoices",
        json={
            "supplier_id": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "posting_date": "2026-03-17",
            "due_date": "2026-04-17",
            "items": [
                {"item_code": "ITEM-001", "item_name": "원자재A", "qty": 10, "rate": 5000},
            ],
            "taxes": [
                {"tax_type": "VAT", "rate": 10.0, "amount": 5000.0},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "PI-2026-00001"


@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
def test_구매송장_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-invoices -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "PI-001", "supplier_name": "업체"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/purchase-invoices?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_etax_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
def test_구매송장_목록은_상태배지와_3way_매칭요약을_반환한다(
    mock_repo: MagicMock,
    mock_etax_repo: MagicMock,
    mock_po_repo: MagicMock,
    mock_receipt_repo: MagicMock,
) -> None:
    """구매송장 목록은 상태 배지/전자세금계산서/3-way 매칭 요약을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "PI-001",
            "supplier_id": "SUP-001",
            "supplier_name": "업체",
            "purchase_order_id": "PO-001",
            "purchase_receipt_id": "PRCP-001",
            "docstatus": 1,
            "grand_total": 110000,
            "net_total": 100000,
            "outstanding_amount": 110000,
            "etax_invoice_ref": "ETAX-001",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 10000,
                    "amount": 100000,
                }
            ],
            "taxes": [{"tax_type": "VAT", "amount": 10000}],
        }
    ]
    mock_repo.return_value = repo

    etax_repo = MagicMock()
    etax_repo.find_by_id.return_value = {
        "_id": "ETAX-001",
        "transmission_status": "pending",
        "nts_confirmation_no": None,
    }
    mock_etax_repo.return_value = etax_repo

    purchase_order_repo = MagicMock()
    purchase_order_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_po_repo.return_value = purchase_order_repo

    purchase_receipt_repo = MagicMock()
    purchase_receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_receipt_repo.return_value = purchase_receipt_repo

    response = client.get(
        "/api/v1/purchase-invoices",
        params={"status_badge": "submitted_unpaid", "match_status": "matched"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    row = data["data"][0]
    assert row["status_badge"] == "submitted_unpaid"
    assert row["matching_summary"] == {
        "match_status": "matched",
        "comparison_basis": "purchase_receipt",
        "purchase_order_id": "PO-001",
        "purchase_receipt_id": "PRCP-001",
        "invoice_qty": 10.0,
        "reference_qty": 10.0,
        "qty_delta": 0.0,
        "invoice_amount": 100000.0,
        "reference_amount": 100000.0,
        "amount_delta": 0.0,
    }
    assert row["etax_summary"]["transmission_status"] == "pending"
    assert row["available_actions"] == [
        "register_payment",
        "open_accounts_payable",
        "open_purchase_order",
        "open_purchase_receipt",
        "open_etax_invoice",
        "submit_etax_to_nts",
        "cancel",
    ]


@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
def test_구매송장_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-invoices/{doc_id} -- 없는 구매송장은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/purchase-invoices/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_etax_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
def test_구매송장_상세는_지급요약과_전자세금계산서_상태를_노출한다(
    mock_repo: MagicMock,
    mock_etax_repo: MagicMock,
    mock_po_repo: MagicMock,
    mock_receipt_repo: MagicMock,
) -> None:
    """상세 조회는 지급 요약, 전자세금계산서 상태, 3-way 매칭 결과를 함께 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PI-002",
        "supplier_id": "SUP-001",
        "supplier_name": "업체",
        "purchase_order_id": "PO-001",
        "purchase_receipt_id": "PRCP-001",
        "docstatus": 1,
        "grand_total": 110000,
        "net_total": 100000,
        "outstanding_amount": 30000,
        "etax_invoice_ref": "ETAX-002",
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "원자재A",
                "qty": 10,
                "rate": 10000,
                "amount": 100000,
            }
        ],
        "taxes": [{"tax_type": "VAT", "amount": 10000}],
    }
    mock_repo.return_value = repo

    etax_repo = MagicMock()
    etax_repo.find_by_id.return_value = {
        "_id": "ETAX-002",
        "transmission_status": "sent",
        "nts_confirmation_no": "NTS-12345",
    }
    mock_etax_repo.return_value = etax_repo

    purchase_order_repo = MagicMock()
    purchase_order_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_po_repo.return_value = purchase_order_repo

    purchase_receipt_repo = MagicMock()
    purchase_receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_receipt_repo.return_value = purchase_receipt_repo

    response = client.get("/api/v1/purchase-invoices/PI-002")

    assert response.status_code == 200
    data = response.json()
    assert data["status_badge"] == "submitted_partial"
    assert data["payment_summary"] == {
        "grand_total": 110000.0,
        "outstanding_amount": 30000.0,
        "paid_amount": 80000.0,
        "is_paid_in_full": False,
    }
    assert data["etax_summary"] == {
        "etax_invoice_id": "ETAX-002",
        "transmission_status": "sent",
        "nts_confirmation_no": "NTS-12345",
    }
    assert data["matching_summary"]["match_status"] == "matched"


@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.purchase_invoices._get_repo")
def test_매입송장_3way_매칭_불일치시_제출을_차단한다(
    mock_repo: MagicMock,
    mock_po_repo: MagicMock,
    mock_receipt_repo: MagicMock,
) -> None:
    """참조 입고 수량/금액과 다른 매입송장은 제출할 수 없다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PI-2026-00021",
        "docstatus": 0,
        "purchase_order_id": "PO-001",
        "purchase_receipt_id": "PRCP-001",
        "supplier_id": "SUP-001",
        "supplier_name": "테스트 공급업체",
        "grand_total": 132000,
        "net_total": 120000,
        "outstanding_amount": 132000,
        "posting_date": "2026-03-17",
        "due_date": "2026-04-17",
        "items": [{"item_code": "ITEM-001", "qty": 12, "rate": 10000, "amount": 120000}],
        "taxes": [{"tax_type": "VAT", "rate": 10, "amount": 12000}],
    }
    mock_repo.return_value = repo

    purchase_order_repo = MagicMock()
    purchase_order_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_po_repo.return_value = purchase_order_repo

    purchase_receipt_repo = MagicMock()
    purchase_receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-001",
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 100000}],
    }
    mock_receipt_repo.return_value = purchase_receipt_repo

    response = client.post("/api/v1/purchase-invoices/PI-2026-00021/submit")

    assert response.status_code == 400
    assert response.json()["detail"] == "ERR-BUY-054: 3-way 매칭 불일치로 제출할 수 없습니다"
    repo.submit_with_event.assert_not_called()
