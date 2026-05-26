"""공급업체견적(SupplierQuotation) 워크벤치 라우트 테스트."""

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


@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
@patch("oneerp_buying_app.routes.supplier_quotations.generate_name", return_value="SQ-2026-00001")
def test_공급업체견적_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/supplier-quotations -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/supplier-quotations",
        json={
            "supplier": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "transaction_date": "2026-03-18",
            "valid_till": "2026-04-18",
            "items": [
                {"item_code": "ITEM-001", "item_name": "원자재A", "qty": 10, "rate": 5000},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "SQ-2026-00001"


@patch("oneerp_buying_app.routes.supplier_quotations._get_purchase_order_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_rfq_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_목록은_비교요약과_상태배지를_반환한다(
    mock_get_repo: MagicMock,
    mock_get_rfq_repo: MagicMock,
    mock_get_purchase_order_repo: MagicMock,
) -> None:
    """GET /api/v1/supplier-quotations -- 비교 순위와 선정 상태를 보여준다."""
    quotation_repo = MagicMock()

    def _find_many(*args, **kwargs):
        query = {}
        query = args[0] or {} if args else kwargs.get("query", {}) or {}
        if query == {"rfq_reference": "RFQ-001", "docstatus": 1}:
            return [
                {
                    "_id": "SQ-002",
                    "rfq_reference": "RFQ-001",
                    "supplier": "SUP-002",
                    "supplier_name": "최저가 공급업체",
                    "docstatus": 1,
                    "transaction_date": "2026-04-10",
                    "valid_till": "2026-04-20",
                    "grand_total": 48000,
                    "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 48000}],
                },
                {
                    "_id": "SQ-001",
                    "rfq_reference": "RFQ-001",
                    "supplier": "SUP-001",
                    "supplier_name": "테스트 공급업체",
                    "docstatus": 1,
                    "transaction_date": "2026-04-10",
                    "valid_till": "2026-04-20",
                    "grand_total": 50000,
                    "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 50000}],
                },
            ]
        return [
            {
                "_id": "SQ-002",
                "rfq_reference": "RFQ-001",
                "supplier": "SUP-002",
                "supplier_name": "최저가 공급업체",
                "docstatus": 1,
                "transaction_date": "2026-04-10",
                "valid_till": "2026-04-20",
                "grand_total": 48000,
                "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 48000}],
            }
        ]

    quotation_repo.find_many.side_effect = _find_many
    quotation_repo.count.return_value = 1
    mock_get_repo.return_value = quotation_repo

    rfq_repo = MagicMock()
    rfq_repo.find_by_id.return_value = {
        "_id": "RFQ-001",
        "suppliers": ["SUP-001", "SUP-002"],
    }
    mock_get_rfq_repo.return_value = rfq_repo

    po_repo = MagicMock()
    po_repo.find_many.return_value = []
    mock_get_purchase_order_repo.return_value = po_repo

    response = client.get(
        "/api/v1/supplier-quotations",
        params={"status_badge": "best_offer", "page": 1, "page_size": 20},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    row = payload["data"][0]
    assert row["status_badge"] == "best_offer"
    assert row["recommended_action"] == "create_purchase_order"
    assert row["summary"] == {
        "item_count": 1,
        "total_qty": 10.0,
        "submitted_quote_count": 2,
        "rfq_supplier_count": 2,
        "comparison_rank": 1,
        "linked_purchase_order_count": 0,
        "is_lowest_quote": True,
    }
    assert row["available_actions"] == [
        "compare_quotations",
        "create_purchase_order",
        "view_rfq",
        "cancel",
    ]


@patch("oneerp_buying_app.routes.supplier_quotations.PurchaseProcessService")
def test_RFQ별_공급업체견적_비교_조회(mock_service_cls: MagicMock) -> None:
    """GET /api/v1/supplier-quotations/compare/{rfq_id} -- 비교표와 추천 결과를 반환한다."""
    mock_service = MagicMock()
    mock_service.compare_quotations.return_value = {
        "rfq_id": "RFQ-001",
        "quotation_count": 2,
        "quotations": [
            {
                "quotation_id": "SQ-001",
                "supplier": "SUP-001",
                "supplier_name": "공급A",
                "grand_total": 500000.0,
            },
            {
                "quotation_id": "SQ-002",
                "supplier": "SUP-002",
                "supplier_name": "공급B",
                "grand_total": 480000.0,
            },
        ],
        "recommendations": [
            {
                "item_code": "ITEM-001",
                "recommended_supplier": "SUP-002",
                "best_rate": 4800.0,
                "quotation_id": "SQ-002",
                "alternatives": 1,
                "alternative_quotes": [
                    {
                        "supplier": "SUP-001",
                        "rate": 5000.0,
                    }
                ],
            }
        ],
    }
    mock_service_cls.return_value = mock_service

    response = client.get("/api/v1/supplier-quotations/compare/RFQ-001")

    assert response.status_code == 200
    data = response.json()
    assert data["quotation_count"] == 2
    assert data["recommendations"][0]["recommended_supplier"] == "SUP-002"
    mock_service.compare_quotations.assert_called_once_with("RFQ-001")


@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/supplier-quotations/{doc_id} -- 없는 공급업체견적은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/supplier-quotations/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_buying_app.routes.supplier_quotations._get_purchase_order_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_rfq_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_상세는_RFQ비교와_PO연계를_노출한다(
    mock_get_repo: MagicMock,
    mock_get_rfq_repo: MagicMock,
    mock_get_purchase_order_repo: MagicMock,
) -> None:
    """GET /api/v1/supplier-quotations/{doc_id} -- 선정 상태와 후속 액션을 함께 보여준다."""
    quotation_repo = MagicMock()
    quotation_repo.find_by_id.return_value = {
        "_id": "SQ-002",
        "rfq_reference": "RFQ-001",
        "supplier": "SUP-002",
        "supplier_name": "최저가 공급업체",
        "docstatus": 1,
        "transaction_date": "2026-04-10",
        "valid_till": "2026-04-20",
        "grand_total": 48000,
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 48000}],
    }
    quotation_repo.find_many.return_value = [
        {
            "_id": "SQ-002",
            "rfq_reference": "RFQ-001",
            "supplier": "SUP-002",
            "supplier_name": "최저가 공급업체",
            "docstatus": 1,
            "transaction_date": "2026-04-10",
            "valid_till": "2026-04-20",
            "grand_total": 48000,
            "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 48000}],
        },
        {
            "_id": "SQ-001",
            "rfq_reference": "RFQ-001",
            "supplier": "SUP-001",
            "supplier_name": "비교 공급업체",
            "docstatus": 1,
            "transaction_date": "2026-04-10",
            "valid_till": "2026-04-20",
            "grand_total": 50000,
            "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 50000}],
        },
    ]
    mock_get_repo.return_value = quotation_repo

    rfq_repo = MagicMock()
    rfq_repo.find_by_id.return_value = {
        "_id": "RFQ-001",
        "suppliers": ["SUP-001", "SUP-002"],
    }
    mock_get_rfq_repo.return_value = rfq_repo

    po_repo = MagicMock()
    po_repo.find_many.return_value = [{"_id": "PO-001", "quotation_reference": "SQ-002"}]
    mock_get_purchase_order_repo.return_value = po_repo

    response = client.get("/api/v1/supplier-quotations/SQ-002")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "selected_for_order"
    assert payload["recommended_action"] == "review_purchase_order"
    assert payload["summary"] == {
        "item_count": 1,
        "total_qty": 10.0,
        "submitted_quote_count": 2,
        "rfq_supplier_count": 2,
        "comparison_rank": 1,
        "linked_purchase_order_count": 1,
        "is_lowest_quote": True,
    }
    assert payload["available_actions"] == [
        "compare_quotations",
        "open_purchase_order",
        "view_rfq",
        "cancel",
    ]


@patch("oneerp_buying_app.routes.supplier_quotations._get_purchase_order_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_rfq_repo", create=True)
@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_요약카드는_추천액션과_비교맥락을_반환한다(
    mock_get_repo: MagicMock,
    mock_get_rfq_repo: MagicMock,
    mock_get_purchase_order_repo: MagicMock,
) -> None:
    """GET /api/v1/supplier-quotations/{doc_id}/summary -- 카드용 요약을 반환한다."""
    quotation_repo = MagicMock()
    quotation_repo.find_by_id.return_value = {
        "_id": "SQ-001",
        "rfq_reference": "RFQ-001",
        "supplier": "SUP-001",
        "supplier_name": "테스트 공급업체",
        "docstatus": 0,
        "transaction_date": "2026-04-10",
        "valid_till": "2026-04-20",
        "grand_total": 50000,
        "items": [{"item_code": "ITEM-001", "qty": 10, "amount": 50000}],
    }
    quotation_repo.find_many.return_value = []
    mock_get_repo.return_value = quotation_repo

    rfq_repo = MagicMock()
    rfq_repo.find_by_id.return_value = {"_id": "RFQ-001", "suppliers": ["SUP-001", "SUP-002"]}
    mock_get_rfq_repo.return_value = rfq_repo

    po_repo = MagicMock()
    po_repo.find_many.return_value = []
    mock_get_purchase_order_repo.return_value = po_repo

    response = client.get("/api/v1/supplier-quotations/SQ-001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["supplier_quotation"]["supplier_name"] == "테스트 공급업체"
    assert payload["status_badge"] == "draft"
    assert payload["recommended_action"] == "submit"
    assert payload["summary"]["rfq_supplier_count"] == 2
    assert payload["available_actions"] == ["edit", "submit", "delete", "view_rfq"]


@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_제출_정상(mock_repo: MagicMock) -> None:
    """POST /api/v1/supplier-quotations/{doc_id}/submit -- 초안 상태에서 제출 성공."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "SQ-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/supplier-quotations/SQ-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_공급업체견적_취소_정상(mock_repo: MagicMock) -> None:
    """POST /api/v1/supplier-quotations/{doc_id}/cancel -- 제출된 문서 취소 성공."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "SQ-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/supplier-quotations/SQ-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("SQ-001")


@patch("oneerp_buying_app.routes.supplier_quotations._get_repo")
def test_제출된_공급업체견적은_삭제할_수_없다(mock_repo: MagicMock) -> None:
    """DELETE /api/v1/supplier-quotations/{doc_id} -- 제출된 문서는 삭제할 수 없다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "SQ-001", "docstatus": 1}
    mock_repo.return_value = repo

    response = client.delete("/api/v1/supplier-quotations/SQ-001")

    assert response.status_code == 422
    assert "ERR-BUY-030" in response.text
    repo.delete_by_id.assert_not_called()
