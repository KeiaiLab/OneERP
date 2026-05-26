"""판매주문(SalesOrder) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_core.events.schemas import EventType
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


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
@patch(
    "oneerp_selling_app.routes.sales_orders.resolve_sales_partner_snapshot",
    return_value={
        "sales_partner_id": "SPAR-001",
        "sales_partner_name": "총판A",
        "sales_partner_commission_rate": 7.5,
    },
)
@patch("oneerp_selling_app.routes.sales_orders.generate_name", return_value="SO-2026-00001")
def test_판매주문_생성_정상(
    mock_name: MagicMock,
    mock_partner_snapshot: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """POST /api/v1/sales-orders -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/sales-orders",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "transaction_date": "2026-03-17",
            "delivery_date": "2026-03-24",
            "items": [
                {"item_code": "ITEM-001", "item_name": "품목A", "qty": 5, "rate": 2000},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "SO-2026-00001"
    insert_doc = mock_repo.return_value.insert.call_args.args[0]
    assert insert_doc.sales_partner_id == "SPAR-001"
    assert insert_doc.sales_partner_name == "총판A"
    assert insert_doc.sales_partner_commission_rate == 7.5


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_생성_납품예정일이_거래일보다_빠르면_거부(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-orders -- delivery_date < transaction_date 이면 422를 반환한다."""
    mock_repo.return_value = MagicMock()

    response = client.post(
        "/api/v1/sales-orders",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "transaction_date": "2026-03-24",
            "delivery_date": "2026-03-17",
            "items": [
                {"item_code": "ITEM-001", "item_name": "품목A", "qty": 5, "rate": 2000},
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("ERR-SELL-047")


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_생성_품목이_없으면_거부(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-orders -- 품목이 없으면 422를 반환한다."""
    mock_repo.return_value = MagicMock()

    response = client.post(
        "/api/v1/sales-orders",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "transaction_date": "2026-03-17",
            "delivery_date": "2026-03-24",
            "items": [],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("ERR-SELL-048")


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-orders -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "SO-001",
            "customer_name": "고객",
            "docstatus": 1,
            "downstream_refs": {
                "delivery_note_ids": ["DN-001"],
                "sales_invoice_ids": ["SINV-001", "SINV-002"],
            },
        }
    ]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/sales-orders?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["status_badge"] == "submitted"
    assert data["data"][0]["downstream_summary"] == {
        "delivery_note_count": 1,
        "sales_invoice_count": 2,
        "has_downstream_documents": True,
    }


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-orders/{doc_id} -- 없는 주문은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/sales-orders/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_상세_조회_관련문서_요약을_포함(mock_repo: MagicMock) -> None:
    """GET /api/v1/sales-orders/{doc_id} -- 상태 뱃지와 downstream 요약을 함께 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "SO-001",
        "customer_name": "고객",
        "docstatus": 1,
        "downstream_refs": {
            "delivery_note_ids": ["DN-001", "DN-002"],
            "sales_invoice_ids": ["SINV-001"],
        },
    }
    mock_repo.return_value = repo

    response = client.get("/api/v1/sales-orders/SO-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "submitted"
    assert payload["downstream_summary"]["delivery_note_count"] == 2
    assert payload["downstream_summary"]["sales_invoice_count"] == 1


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_제출_이벤트_발행(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-orders/{doc_id}/submit -- submit_with_event 호출을 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "SO-001", "docstatus": 0}
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo
    response = client.post("/api/v1/sales-orders/SO-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()
    call_args = repo.submit_with_event.call_args
    # 위치 인자: doc_id
    assert call_args[0][0] == "SO-001"
    # 키워드 인자: event_type
    assert call_args[1]["event_type"] == EventType.SALES_ORDER_SUBMITTED
    # 키워드 인자: event_data
    assert call_args[1]["event_data"] == {"doc_id": "SO-001"}


@patch("oneerp_selling_app.routes.sales_orders._get_repo")
def test_판매주문_제출_비초안_거부(mock_repo: MagicMock) -> None:
    """POST /api/v1/sales-orders/{doc_id}/submit -- 초안이 아닌 문서는 400을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "SO-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/sales-orders/SO-001/submit")
    assert response.status_code == 400


@patch("oneerp_selling_app.routes.sales_orders._get_delivery_note_repo")
@patch("oneerp_selling_app.routes.sales_orders._get_repo")
@patch("oneerp_selling_app.routes.sales_orders.generate_name", return_value="DN-2026-00001")
def test_판매주문에서_납품서_초안_생성시_downstream_refs를_갱신(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_delivery_repo: MagicMock,
) -> None:
    """POST /api/v1/sales-orders/{doc_id}/delivery-note -- 후속 문서 추적 정보를 저장한다."""
    so_repo = MagicMock()
    so_repo.find_by_id.return_value = {
        "_id": "SO-001",
        "docstatus": 1,
        "customer_id": "CUST-001",
        "customer_name": "테스트 고객",
        "transaction_date": "2026-03-24",
        "delivery_date": "2026-03-24",
        "downstream_refs": {
            "delivery_note_ids": [],
            "sales_invoice_ids": [],
        },
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "품목A",
                "qty": 5,
                "rate": 2000,
                "amount": 10000,
            },
        ],
    }
    dn_repo = MagicMock()
    mock_repo.return_value = so_repo
    mock_delivery_repo.return_value = dn_repo

    response = client.post(
        "/api/v1/sales-orders/SO-001/delivery-note",
        json={"warehouse": "WH-001"},
    )

    assert response.status_code == 201
    assert response.json()["downstream_summary"] == {
        "delivery_note_count": 1,
        "sales_invoice_count": 0,
        "has_downstream_documents": True,
    }
    so_repo.update_by_id.assert_called_once_with(
        "SO-001",
        {
            "downstream_refs": {
                "delivery_note_ids": ["DN-2026-00001"],
                "sales_invoice_ids": [],
            }
        },
    )


@patch("oneerp_selling_app.routes.sales_orders._get_sales_invoice_repo")
@patch("oneerp_selling_app.routes.sales_orders._get_repo")
@patch("oneerp_selling_app.routes.sales_orders.generate_name", return_value="SINV-2026-00001")
def test_판매주문에서_송장_초안_생성시_downstream_refs를_갱신(
    mock_name: MagicMock,
    mock_repo: MagicMock,
    mock_invoice_repo: MagicMock,
) -> None:
    """POST /api/v1/sales-orders/{doc_id}/sales-invoice -- 후속 문서 추적 정보를 저장한다."""
    so_repo = MagicMock()
    so_repo.find_by_id.return_value = {
        "_id": "SO-001",
        "docstatus": 1,
        "customer_id": "CUST-001",
        "customer_name": "테스트 고객",
        "sales_partner_id": "SPAR-001",
        "sales_partner_name": "총판A",
        "sales_partner_commission_rate": 7.5,
        "transaction_date": "2026-03-24",
        "delivery_date": "2026-03-24",
        "downstream_refs": {
            "delivery_note_ids": ["DN-001"],
            "sales_invoice_ids": [],
        },
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "품목A",
                "qty": 5,
                "rate": 2000,
                "amount": 10000,
            },
        ],
    }
    invoice_repo = MagicMock()
    mock_repo.return_value = so_repo
    mock_invoice_repo.return_value = invoice_repo

    response = client.post(
        "/api/v1/sales-orders/SO-001/sales-invoice",
        json={
            "posting_date": "2026-03-24",
            "due_date": "2026-04-24",
            "taxes": [{"tax_type": "VAT", "rate": 10, "amount": 1000}],
        },
    )

    assert response.status_code == 201
    assert response.json()["downstream_summary"] == {
        "delivery_note_count": 1,
        "sales_invoice_count": 1,
        "has_downstream_documents": True,
    }
    insert_doc = invoice_repo.insert.call_args.args[0]
    assert insert_doc.sales_partner_id == "SPAR-001"
    assert insert_doc.sales_partner_name == "총판A"
    assert insert_doc.sales_partner_commission_rate == 7.5
    so_repo.update_by_id.assert_called_once_with(
        "SO-001",
        {
            "downstream_refs": {
                "delivery_note_ids": ["DN-001"],
                "sales_invoice_ids": ["SINV-2026-00001"],
            }
        },
    )
