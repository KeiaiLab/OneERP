"""공급업체(Supplier) 커스텀 라우트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

_BASE_URL = "/api/v1/suppliers"


@patch("oneerp_buying_app.routes.suppliers._get_repo")
@patch("oneerp_buying_app.routes.suppliers.generate_name", return_value="SUP-2026-00001")
def test_공급업체_생성은_세부_마스터필드를_저장한다(
    mock_name: MagicMock,
    mock_get_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """POST /api/v1/suppliers -- 그룹/연락처/은행/공급품목 등 상세 필드를 저장한다."""
    repo = MagicMock()
    mock_get_repo.return_value = repo

    response = test_client.post(
        _BASE_URL,
        json={
            "supplier_name": "테스트 공급업체",
            "supplier_group": "원자재",
            "supplier_type": "Company",
            "tax_id": "123-45-67890",
            "country": "KR",
            "representative_name": "홍길동",
            "payment_terms": "30일",
            "delivery_terms": "납기 7일",
            "bank_name": "국민은행",
            "bank_account_no": "110-1234-5678",
            "supplied_items": ["CHEM-001", "PACK-002", "CHEM-001"],
            "contact": {
                "contact_name": "김담당",
                "email": "vendor@example.com",
                "phone": "010-1234-5678",
            },
            "address": {
                "address_line1": "서울시 금천구 가산동 1-1",
                "country": "KR",
            },
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["_id"] == "SUP-2026-00001"
    assert data["id"] == "SUP-2026-00001"
    assert data["supplied_items"] == ["CHEM-001", "PACK-002"]

    inserted = repo.insert.call_args.args[0]
    assert inserted.supplier_group == "원자재"
    assert inserted.contact.email == "vendor@example.com"
    assert inserted.address.country == "KR"
    assert inserted.bank_name == "국민은행"


@patch("oneerp_buying_app.routes.suppliers._get_scorecard_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.suppliers._get_repo")
def test_공급업체_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_get_repo: MagicMock,
    mock_get_order_repo: MagicMock,
    mock_get_receipt_repo: MagicMock,
    mock_get_invoice_repo: MagicMock,
    mock_get_scorecard_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """GET /api/v1/suppliers -- 거래 요약, 상태 배지, 권장 액션으로 운영 워크벤치를 구성한다."""
    supplier_repo = MagicMock()
    supplier_repo.find_many.return_value = [
        {
            "_id": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "supplier_group": "원자재",
            "supplier_type": "Company",
            "is_active": True,
        }
    ]
    mock_get_repo.return_value = supplier_repo

    order_repo = MagicMock()
    order_repo.find_many.return_value = [
        {"_id": "PO-001", "docstatus": 1, "total": 500000},
    ]
    receipt_repo = MagicMock()
    receipt_repo.find_many.return_value = [
        {"_id": "PRCP-001", "docstatus": 1, "total_amount": 480000},
    ]
    invoice_repo = MagicMock()
    invoice_repo.find_many.return_value = [
        {"_id": "PI-001", "docstatus": 1, "grand_total": 550000, "outstanding_amount": 300000},
    ]
    scorecard_repo = MagicMock()
    scorecard_repo.find_many.return_value = [
        {"_id": "SSC-001", "evaluation_period": "2026-04", "total_score": 72.5},
    ]
    mock_get_order_repo.return_value = order_repo
    mock_get_receipt_repo.return_value = receipt_repo
    mock_get_invoice_repo.return_value = invoice_repo
    mock_get_scorecard_repo.return_value = scorecard_repo

    response = test_client.get(
        f"{_BASE_URL}?supplier_group=원자재&status_badge=payment_due&page=1&page_size=20",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    row = payload["data"][0]
    assert row["status_badge"] == "payment_due"
    assert row["recommended_action"] == "review_payables"
    assert row["summary"] == {
        "submitted_purchase_order_count": 1,
        "submitted_purchase_receipt_count": 1,
        "submitted_purchase_invoice_count": 1,
        "submitted_order_amount": 500000.0,
        "submitted_invoice_amount": 550000.0,
        "outstanding_amount": 300000.0,
        "scorecard_count": 1,
        "latest_scorecard": {
            "_id": "SSC-001",
            "id": "SSC-001",
            "evaluation_period": "2026-04",
            "total_score": 72.5,
        },
    }
    assert row["available_actions"] == [
        "edit",
        "create_purchase_order",
        "open_purchase_history",
        "open_accounts_payable",
        "view_scorecards",
    ]


@patch("oneerp_buying_app.routes.suppliers._get_scorecard_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.suppliers._get_repo")
def test_공급업체_요약은_거래요약과_권장액션을_반환한다(
    mock_get_repo: MagicMock,
    mock_get_order_repo: MagicMock,
    mock_get_receipt_repo: MagicMock,
    mock_get_invoice_repo: MagicMock,
    mock_get_scorecard_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """GET /api/v1/suppliers/{id}/summary -- 상세 카드에 필요한 요약/배지/액션을 반환한다."""
    supplier_repo = MagicMock()
    supplier_repo.find_by_id.return_value = {
        "_id": "SUP-001",
        "supplier_name": "테스트 공급업체",
        "supplier_group": "원자재",
        "supplier_type": "Company",
        "is_active": True,
    }
    mock_get_repo.return_value = supplier_repo

    mock_get_order_repo.return_value.find_many.return_value = [
        {"_id": "PO-001", "docstatus": 1, "total": 500000},
    ]
    mock_get_receipt_repo.return_value.find_many.return_value = []
    mock_get_invoice_repo.return_value.find_many.return_value = []
    mock_get_scorecard_repo.return_value.find_many.return_value = [
        {"_id": "SSC-002", "evaluation_period": "2026-05", "total_score": 68.0},
    ]

    response = test_client.get(f"{_BASE_URL}/SUP-001/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["supplier"]["supplier_name"] == "테스트 공급업체"
    assert payload["status_badge"] == "performance_watch"
    assert payload["recommended_action"] == "review_scorecard"
    assert payload["available_actions"] == [
        "edit",
        "create_purchase_order",
        "open_purchase_history",
        "view_scorecards",
    ]
    assert payload["summary"]["latest_scorecard"]["total_score"] == 68.0


@patch("oneerp_buying_app.routes.suppliers._get_scorecard_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.suppliers._get_purchase_order_repo")
@patch("oneerp_buying_app.routes.suppliers._get_repo")
def test_거래이력이_있는_공급업체는_삭제할_수_없다(
    mock_get_repo: MagicMock,
    mock_get_order_repo: MagicMock,
    mock_get_receipt_repo: MagicMock,
    mock_get_invoice_repo: MagicMock,
    mock_get_scorecard_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """DELETE /api/v1/suppliers/{id} -- 발주/입고/송장/평가 이력이 있으면 삭제를 차단한다."""
    supplier_repo = MagicMock()
    supplier_repo.find_by_id.return_value = {
        "_id": "SUP-001",
        "supplier_name": "삭제차단 공급업체",
    }
    mock_get_repo.return_value = supplier_repo
    mock_get_order_repo.return_value.count.return_value = 1
    mock_get_receipt_repo.return_value.count.return_value = 0
    mock_get_invoice_repo.return_value.count.return_value = 0
    mock_get_scorecard_repo.return_value.count.return_value = 0

    response = test_client.delete(f"{_BASE_URL}/SUP-001")

    assert response.status_code == 422
    assert "ERR-BUY-046" in response.text
    supplier_repo.delete_by_id.assert_not_called()


@patch("oneerp_buying_app.routes.suppliers._get_repo")
def test_공급업체_상세_조회_미존재_404(
    mock_get_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """GET /api/v1/suppliers/{doc_id} -- 없는 공급업체는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_get_repo.return_value = repo

    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")

    assert response.status_code == 404
