"""판매송장(SalesInvoice) CRUD 엔드포인트 테스트."""

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


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
@patch(
    "oneerp_selling_app.routes.sales_invoices.resolve_sales_partner_snapshot",
    return_value={
        "sales_partner_id": "SPAR-001",
        "sales_partner_name": "총판A",
        "sales_partner_commission_rate": 7.5,
    },
)
@patch("oneerp_selling_app.routes.sales_invoices.generate_name", return_value="SINV-2026-00001")
def test_판매송장_생성_정상(
    mock_name: MagicMock,
    mock_partner_snapshot: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """POST /api/v1/sales-invoices -- 정상 생성 시 201을 반환한다."""
    assert mock_partner_snapshot is not None
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/sales-invoices",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "posting_date": "2026-03-17",
            "due_date": "2026-04-17",
            "items": [
                {"item_code": "ITEM-001", "item_name": "상품A", "qty": 10, "rate": 1000},
            ],
            "taxes": [
                {"tax_type": "VAT", "rate": 10.0, "amount": 1000.0},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "SINV-2026-00001"
    insert_doc = mock_repo.return_value.insert.call_args.args[0]
    assert insert_doc.sales_partner_id == "SPAR-001"
    assert insert_doc.sales_partner_name == "총판A"
    assert insert_doc.sales_partner_commission_rate == 7.5


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-invoices -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "SINV-001", "customer_name": "고객"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/sales-invoices?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


@patch("oneerp_selling_app.routes.sales_invoices._get_etax_repo")
@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_목록은_상태배지와_전자세금계산서_요약을_반환한다(
    mock_repo: MagicMock,
    mock_etax_repo: MagicMock,
) -> None:
    """목록 응답이 송장 상태/전자세금계산서/후속 액션을 함께 노출한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "SINV-001",
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "docstatus": 1,
            "grand_total": 55000,
            "outstanding_amount": 25000,
            "sales_order_ref": "SO-001",
            "delivery_note_ref": "DN-001",
            "etax_invoice_ref": "ETAX-001",
        }
    ]
    repo.count.return_value = 1
    mock_repo.return_value = repo

    etax_repo = MagicMock()
    etax_repo.find_by_id.return_value = {
        "_id": "ETAX-001",
        "transmission_status": "pending",
        "nts_confirmation_no": None,
    }
    mock_etax_repo.return_value = etax_repo

    response = client.get(
        "/api/v1/sales-invoices"
        "?customer_id=CUST-001"
        "&status_badge=submitted_partial"
        "&transmission_status=pending"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    invoice = payload["data"][0]
    assert invoice["status_badge"] == "submitted_partial"
    assert invoice["payment_summary"] == {
        "grand_total": 55000.0,
        "outstanding_amount": 25000.0,
        "collected_amount": 30000.0,
        "is_paid_in_full": False,
    }
    assert invoice["etax_summary"] == {
        "etax_invoice_id": "ETAX-001",
        "transmission_status": "pending",
        "nts_confirmation_no": None,
    }
    assert invoice["available_actions"] == [
        "register_payment",
        "open_accounts_receivable",
        "open_etax_invoice",
        "submit_etax_to_nts",
        "cancel",
    ]


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
@patch("oneerp_selling_app.routes.sales_invoices.generate_name", return_value="SINV-2026-00002")
def test_판매송장_생성시_net_total_저장(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-invoices -- net_total이 items.amount 합계로 저장된다."""
    repo = MagicMock()
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/sales-invoices",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "posting_date": "2026-03-17",
            "due_date": "2026-04-17",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "상품A",
                    "qty": 10,
                    "rate": 1000,
                    "amount": 10000,
                },
                {
                    "item_code": "ITEM-002",
                    "item_name": "상품B",
                    "qty": 5,
                    "rate": 2000,
                    "amount": 10000,
                },
            ],
            "taxes": [
                {"tax_type": "VAT", "rate": 10.0, "amount": 2000.0},
            ],
        },
    )
    assert response.status_code == 201

    # insert 호출 시 전달된 SalesInvoice 모델의 net_total 검증
    insert_call = repo.insert.call_args
    invoice_obj = insert_call[0][0]
    assert invoice_obj.net_total == 20000  # 10000 + 10000


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-invoices/{doc_id} -- 없는 판매송장은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/sales-invoices/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_selling_app.routes.sales_invoices._get_etax_repo")
@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_상세는_수금요약과_전자세금계산서_상태를_노출한다(
    mock_repo: MagicMock,
    mock_etax_repo: MagicMock,
) -> None:
    """상세 응답이 상태 배지와 후속 처리 액션을 제공한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SINV-010",
        "customer_id": "CUST-010",
        "customer_name": "상세 고객",
        "docstatus": 1,
        "grand_total": 77000,
        "outstanding_amount": 77000,
        "sales_order_ref": "SO-010",
        "delivery_note_ref": "DN-010",
        "etax_invoice_ref": "ETAX-010",
    }
    mock_repo.return_value = repo

    etax_repo = MagicMock()
    etax_repo.find_by_id.return_value = {
        "_id": "ETAX-010",
        "transmission_status": "pending",
        "nts_confirmation_no": None,
    }
    mock_etax_repo.return_value = etax_repo

    response = client.get("/api/v1/sales-invoices/SINV-010")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted_unpaid"
    assert payload["payment_summary"] == {
        "grand_total": 77000.0,
        "outstanding_amount": 77000.0,
        "collected_amount": 0.0,
        "is_paid_in_full": False,
    }
    assert payload["etax_summary"] == {
        "etax_invoice_id": "ETAX-010",
        "transmission_status": "pending",
        "nts_confirmation_no": None,
    }
    assert payload["available_actions"] == [
        "register_payment",
        "open_accounts_receivable",
        "open_etax_invoice",
        "submit_etax_to_nts",
        "cancel",
    ]


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_리포트용_정규화_데이터를_반환한다(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-invoices/{id}/report — PDF 렌더링용 정규화 응답을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SINV-777",
        "customer_id": "CUST-777",
        "customer_name": "테스트 고객",
        "customer_business_number": "123-45-67890",
        "customer_contact_name": "이담당",
        "customer_address": "서울특별시 중구 세종대로 1",
        "posting_date": "2026-04-10",
        "items": [
            {
                "item_name": "ERP 구축",
                "spec": "컨설팅",
                "qty": 2,
                "unit": "MD",
                "rate": 1500000,
            }
        ],
        "company_name": "원이알피 주식회사",
        "company_ceo": "김대표",
        "company_address": "서울특별시 강남구 테헤란로 123",
        "company_business_number": "987-65-43210",
        "company_phone": "02-1234-5678",
        "remark": "테스트 비고",
    }
    mock_repo.return_value = repo

    response = client.get("/api/v1/sales-invoices/SINV-777/report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["invoice_number"] == "SINV-777"
    assert payload["invoice_date"] == "2026-04-10"
    assert payload["customer"]["name"] == "테스트 고객"
    assert payload["customer"]["business_number"] == "123-45-67890"
    assert payload["items"][0]["item_name"] == "ERP 구축"
    assert payload["items"][0]["quantity"] == 2
    assert payload["items"][0]["unit_price"] == 1500000
    assert payload["company"]["name"] == "원이알피 주식회사"
    assert payload["remark"] == "테스트 비고"


# ---------- BR-SELL-012: 송장 제출 시 outstanding_amount 재설정 ----------


@patch("oneerp_selling_app.routes.sales_invoices._get_etax_repo")
@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
@patch("oneerp_selling_app.routes.sales_invoices.generate_name", return_value="ETAX-2026-00001")
def test_판매송장_제출시_outstanding_amount_재설정과_전자세금계산서_자동연결(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_etax_repo: MagicMock,
) -> None:
    """BR-SELL-012: 제출 시 outstanding_amount가 grand_total로 동기화된다."""
    repo = MagicMock()
    # 초안 수정 후 grand_total과 outstanding_amount가 불일치하는 상황
    repo.find_by_id.return_value = {
        "_id": "SINV-001",
        "docstatus": 0,
        "grand_total": 55000,
        "outstanding_amount": 50000,  # 이전 값 — 불일치
        "net_total": 50000,
        "customer_id": "CUST-001",
        "customer_name": "고객",
        "posting_date": "2026-03-17",
        "due_date": "2026-04-17",
        "etax_invoice_ref": None,
    }
    mock_repo.return_value = repo
    etax_repo = MagicMock()
    mock_etax_repo.return_value = etax_repo

    response = client.post("/api/v1/sales-invoices/SINV-001/submit")

    assert response.status_code == 200
    etax_insert_arg = etax_repo.insert.call_args.args[0]
    assert etax_insert_arg["invoice_ref"] == "SINV-001"
    assert etax_insert_arg["transmission_status"] == "pending"
    # update_by_id로 outstanding_amount와 전자세금계산서 참조를 동기화 확인
    repo.update_by_id.assert_called_once_with(
        "SINV-001",
        {
            "outstanding_amount": 55000,
            "etax_invoice_ref": "ETAX-2026-00001",
        },
    )
    repo.submit_with_event.assert_called_once()
    assert (
        repo.submit_with_event.call_args.kwargs["event_data"]["etax_invoice_ref"]
        == "ETAX-2026-00001"
    )


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_제출시_grand_total_없으면_0으로_설정(mock_repo: MagicMock) -> None:
    """BR-SELL-012: grand_total이 없는 문서는 outstanding_amount를 0으로 설정한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SINV-002",
        "docstatus": 0,
        # grand_total 키가 없는 경우
        "customer_id": "CUST-001",
        "customer_name": "고객",
        "posting_date": "2026-03-17",
        "due_date": "2026-04-17",
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/sales-invoices/SINV-002/submit")

    assert response.status_code == 200
    repo.update_by_id.assert_called_once_with("SINV-002", {"outstanding_amount": 0})


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_제출_미존재_404(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-invoices/{id}/submit -- 없는 송장은 404."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.post("/api/v1/sales-invoices/NOT-EXIST/submit")
    assert response.status_code == 404


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_제출_이미_제출됨_400(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-invoices/{id}/submit -- 이미 제출 상태면 400."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SINV-003",
        "docstatus": 1,  # 이미 제출
        "grand_total": 10000,
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/sales-invoices/SINV-003/submit")
    assert response.status_code == 400


@patch("oneerp_selling_app.routes.sales_invoices._get_repo")
def test_판매송장_삭제는_초안만_허용한다(mock_repo: MagicMock) -> None:
    """DELETE /api/v1/sales-invoices/{id} -- 제출된 문서는 삭제할 수 없다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SINV-006",
        "docstatus": 1,
    }
    mock_repo.return_value = repo

    response = client.delete("/api/v1/sales-invoices/SINV-006")

    assert response.status_code == 400
    repo.delete_by_id.assert_not_called()
