"""구매입고(PurchaseReceipt) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_buying_app.main import app
from oneerp_core.events.schemas import EventType

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


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
@patch("oneerp_buying_app.routes.purchase_receipts.generate_name", return_value="PRCP-2026-00001")
def test_구매입고_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-receipts -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/purchase-receipts",
        json={
            "supplier": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "posting_date": "2026-03-18",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "rate": 5000,
                    "warehouse": "WH-001",
                },
            ],
            "warehouse": "WH-001",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "PRCP-2026-00001"


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
@patch("oneerp_buying_app.routes.purchase_receipts.generate_name", return_value="PRCP-2026-00002")
def test_구매입고_생성시_계산금액과_품질검사상태를_저장(
    mock_name: MagicMock, mock_repo: MagicMock
) -> None:
    """구매입고 생성 시 라인 금액 계산과 품질검사 플래그를 정규화해 저장한다."""
    repo = MagicMock()
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/purchase-receipts",
        json={
            "supplier": "SUP-QUALITY-001",
            "supplier_name": "검수 공급업체",
            "posting_date": "2026-03-19",
            "items": [
                {
                    "item_code": "ITEM-QI-001",
                    "item_name": "검수 품목",
                    "qty": 5,
                    "rate": 10000,
                    "warehouse": "WH-001",
                    "inspection_required": True,
                }
            ],
            "warehouse": "WH-001",
        },
    )

    assert response.status_code == 201
    inserted = repo.insert.call_args[0][0]
    assert isinstance(inserted, dict)
    assert inserted["items"][0]["amount"] == 50000
    assert inserted["items"][0]["inspection_required"] is True
    assert inserted["items"][0]["inspection_status"] == "pending"
    assert inserted["inspection_status"] == "pending"
    assert inserted["quality_inspection_ids"] == []


@patch("oneerp_buying_app.routes.purchase_receipts._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_목록_조회(
    mock_repo: MagicMock,
    mock_get_purchase_invoice_repo: MagicMock,
) -> None:
    """GET /api/v1/purchase-receipts -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "PRCP-001",
            "supplier_name": "업체",
            "docstatus": 1,
            "inspection_status": "pending",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "qty": 4,
                    "rate": 1000,
                    "warehouse": "WH-001",
                    "inspection_required": True,
                    "inspection_status": "pending",
                    "quality_inspection_id": "QI-001",
                }
            ],
            "quality_inspection_ids": ["QI-001"],
        }
    ]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    invoice_repo = MagicMock()
    invoice_repo.count.side_effect = [1, 0]
    mock_get_purchase_invoice_repo.return_value = invoice_repo
    response = client.get("/api/v1/purchase-receipts?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["data"][0]["status_badge"] == "inspection_pending"
    assert data["data"][0]["downstream_summary"] == {
        "purchase_invoice_draft_count": 1,
        "purchase_invoice_submitted_count": 0,
        "has_downstream_documents": True,
    }
    assert data["data"][0]["available_actions"] == [
        "create_purchase_invoice",
        "cancel",
        "view_quality_inspections",
    ]
    assert data["data"][0]["inspection_summary"] == {
        "required_item_count": 1,
        "pending_item_count": 1,
        "completed_item_count": 0,
    }


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-receipts/{doc_id} -- 없는 구매입고는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/purchase-receipts/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출_이벤트_발행(mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-receipts/{doc_id}/submit -- submit_with_event 호출을 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PRCP-001", "docstatus": 0}
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo
    response = client.post("/api/v1/purchase-receipts/PRCP-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()
    call_args = repo.submit_with_event.call_args
    # 위치 인자: doc_id
    assert call_args[0][0] == "PRCP-001"
    # 키워드 인자: event_type
    assert call_args[1]["event_type"] == EventType.PURCHASE_RECEIPT_SUBMITTED
    # 키워드 인자: event_data
    assert call_args[1]["event_data"] == {
        "doc_id": "PRCP-001",
        "inspection_status": "not_required",
        "quality_inspection_ids": [],
    }


@patch("oneerp_buying_app.routes.purchase_receipts.Repository")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출시_PO_received_qty_누적(
    mock_repo: MagicMock, mock_po_repo_cls: MagicMock
) -> None:
    """BR-BUY-011: 구매입고 제출 시 PO의 received_qty가 입고 수량만큼 누적된다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PRCP-001",
        "docstatus": 0,
        "items": [
            {"item_code": "ITEM-001", "qty": 10, "purchase_order": "PO-001"},
            {"item_code": "ITEM-002", "qty": 5, "purchase_order": "PO-001"},
        ],
    }
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo

    po_repo = MagicMock()
    po_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [
            {"item_code": "ITEM-001", "qty": 20, "received_qty": 0},
            {"item_code": "ITEM-002", "qty": 20, "received_qty": 0},
        ],
    }
    mock_po_repo_cls.return_value = po_repo

    response = client.post("/api/v1/purchase-receipts/PRCP-001/submit")
    assert response.status_code == 200

    # PO 업데이트가 호출되었는지 확인
    po_repo.update_by_id.assert_called_once()
    call_args = po_repo.update_by_id.call_args
    assert call_args[0][0] == "PO-001"
    updated_items = call_args[0][1]["items"]
    from decimal import Decimal

    assert updated_items[0]["received_qty"] == Decimal(10)
    assert updated_items[1]["received_qty"] == Decimal(5)


@patch("oneerp_buying_app.routes.purchase_receipts.Repository")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출시_PO참조_없으면_스킵(
    mock_repo: MagicMock, mock_po_repo_cls: MagicMock
) -> None:
    """BR-BUY-011: purchase_order 참조가 없는 입고 아이템은 PO 업데이트를 건너뛴다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PRCP-002",
        "docstatus": 0,
        "items": [
            {"item_code": "ITEM-001", "qty": 10, "purchase_order": ""},
        ],
    }
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo

    response = client.post("/api/v1/purchase-receipts/PRCP-002/submit")
    assert response.status_code == 200
    # PO Repository가 생성되지 않았으므로 update가 호출되지 않아야 함
    mock_po_repo_cls.return_value.update_by_id.assert_not_called()


@patch("oneerp_buying_app.routes.purchase_receipts.Repository")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출시_기존_received_qty에_누적(
    mock_repo: MagicMock, mock_po_repo_cls: MagicMock
) -> None:
    """BR-BUY-011: 이전 입고분이 있는 경우 received_qty에 누적한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PRCP-003",
        "docstatus": 0,
        "items": [
            {"item_code": "ITEM-001", "qty": 5, "purchase_order": "PO-002"},
        ],
    }
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo

    po_repo = MagicMock()
    po_repo.find_by_id.return_value = {
        "_id": "PO-002",
        "items": [
            {"item_code": "ITEM-001", "qty": 20, "received_qty": 10},  # 이전 입고분 10
        ],
    }
    mock_po_repo_cls.return_value = po_repo

    response = client.post("/api/v1/purchase-receipts/PRCP-003/submit")
    assert response.status_code == 200

    call_args = po_repo.update_by_id.call_args
    updated_items = call_args[0][1]["items"]
    from decimal import Decimal

    # 기존 10 + 신규 5 = 15
    assert updated_items[0]["received_qty"] == Decimal(15)


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_취소_정상(mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-receipts/{doc_id}/cancel -- 제출된 문서 취소 성공."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PRCP-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/purchase-receipts/PRCP-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("PRCP-001")


@patch("oneerp_buying_app.routes.purchase_receipts.generate_name", return_value="QI-2026-00001")
@patch("oneerp_buying_app.routes.purchase_receipts.Repository")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출시_품질검사_초안이_자동생성된다(
    mock_repo: MagicMock, mock_repo_cls: MagicMock, mock_name: MagicMock
) -> None:
    """inspection_required 품목이 있으면 제출 시 incoming 품질검사를 자동 생성한다."""
    receipt_repo = MagicMock()
    receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-QUALITY-001",
        "docstatus": 0,
        "supplier": "SUP-001",
        "supplier_name": "검수 공급업체",
        "items": [
            {
                "item_code": "ITEM-QI-001",
                "item_name": "검수 품목",
                "qty": 5,
                "rate": 10000,
                "amount": 50000,
                "warehouse": "WH-001",
                "purchase_order": "PO-001",
                "inspection_required": True,
                "inspection_status": "pending",
            }
        ],
        "quality_inspection_ids": [],
        "inspection_status": "pending",
    }
    receipt_repo.submit_with_event.return_value = True
    mock_repo.return_value = receipt_repo

    po_repo = MagicMock()
    po_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [
            {"item_code": "ITEM-QI-001", "qty": 5, "received_qty": 0},
        ],
    }
    quality_repo = MagicMock()

    def _repo_factory(collection: str, tenant_id: str | None = None) -> MagicMock:
        if collection == "purchase_orders":
            return po_repo
        if collection == "quality_inspections":
            return quality_repo
        return MagicMock()

    mock_repo_cls.side_effect = _repo_factory

    response = client.post("/api/v1/purchase-receipts/PRCP-QUALITY-001/submit")
    assert response.status_code == 200

    quality_repo.insert.assert_called_once()
    inserted_inspection = quality_repo.insert.call_args[0][0]
    assert inserted_inspection["reference_type"] == "purchase_receipt"
    assert inserted_inspection["reference_no"] == "PRCP-QUALITY-001"
    assert inserted_inspection["inspection_type"] == "incoming"
    assert inserted_inspection["item_code"] == "ITEM-QI-001"

    receipt_repo.update_by_id.assert_called_once()
    update_payload = receipt_repo.update_by_id.call_args[0][1]
    assert update_payload["quality_inspection_ids"] == ["QI-2026-00001"]
    assert update_payload["items"][0]["quality_inspection_id"] == "QI-2026-00001"
    assert update_payload["inspection_status"] == "pending"


@patch("oneerp_buying_app.routes.purchase_receipts.Repository")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_구매입고_제출시_발주잔량을_초과하면_거부된다(
    mock_repo: MagicMock, mock_repo_cls: MagicMock
) -> None:
    """구매입고 제출 시 참조 구매주문의 남은 수량을 초과하면 차단한다."""
    receipt_repo = MagicMock()
    receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-OVER-001",
        "docstatus": 0,
        "items": [
            {
                "item_code": "ITEM-001",
                "qty": 6,
                "rate": 1200,
                "warehouse": "WH-001",
                "purchase_order": "PO-001",
            }
        ],
    }
    mock_repo.return_value = receipt_repo

    po_repo = MagicMock()
    po_repo.find_by_id.return_value = {
        "_id": "PO-001",
        "items": [
            {"item_code": "ITEM-001", "qty": 10, "received_qty": 5},
        ],
    }
    mock_repo_cls.return_value = po_repo

    response = client.post("/api/v1/purchase-receipts/PRCP-OVER-001/submit")

    assert response.status_code == 400
    assert "ERR-BUY-048" in response.text
    receipt_repo.submit_with_event.assert_not_called()


@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_제출된_구매입고는_삭제할_수_없다(mock_repo: MagicMock) -> None:
    """제출된 구매입고는 삭제할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PRCP-001", "docstatus": 1}
    mock_repo.return_value = repo

    response = client.delete("/api/v1/purchase-receipts/PRCP-001")

    assert response.status_code == 400
    repo.delete_by_id.assert_not_called()


@patch("oneerp_buying_app.routes.purchase_receipts.generate_name", return_value="PI-2026-00001")
@patch("oneerp_buying_app.routes.purchase_receipts._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_receipts._get_repo")
def test_제출된_구매입고에서_구매송장_초안을_생성한다(
    mock_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    mock_name: MagicMock,
) -> None:
    """제출된 구매입고는 실제 수령 수량 기준의 구매송장 초안을 바로 생성한다."""
    receipt_repo = MagicMock()
    receipt_repo.find_by_id.return_value = {
        "_id": "PRCP-001",
        "docstatus": 1,
        "purchase_order_id": "PO-001",
        "supplier": "SUP-001",
        "supplier_name": "테스트 공급업체",
        "posting_date": "2026-04-09",
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "원자재A",
                "qty": 3,
                "rate": 5000,
                "warehouse": "WH-001",
            }
        ],
    }
    mock_repo.return_value = receipt_repo
    invoice_repo = MagicMock()
    mock_invoice_repo.return_value = invoice_repo

    response = client.post("/api/v1/purchase-receipts/PRCP-001/purchase-invoice")

    assert response.status_code == 201
    assert response.json()["id"] == "PI-2026-00001"
    inserted = invoice_repo.insert.call_args[0][0]
    assert inserted["purchase_receipt_id"] == "PRCP-001"
    assert inserted["purchase_order_id"] == "PO-001"
    assert inserted["grand_total"] == 15000
    assert inserted["items"][0]["qty"] == 3
