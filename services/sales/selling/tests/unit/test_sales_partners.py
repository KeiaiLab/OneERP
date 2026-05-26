"""판매 파트너(SalesPartner) 커스텀 라우터 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

_BASE_URL = "/api/v1/sales-partners"


def test_판매파트너_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/sales-partners -- 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="SPAR-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "partner_name": "테스트 파트너",
            "commission_rate": 5.0,
            "territory": "서울",
            "partner_type": "reseller",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data


def test_판매파트너_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """GET /api/v1/sales-partners -- 페이지네이션 응답 구조를 확인한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter([{"_id": "SPAR-001", "partner_name": "파트너A"}]),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


@patch("oneerp_selling_app.routes.sales_partners._get_invoice_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_판매파트너_목록과_상세는_워크벤치_요약을_반환한다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """목록/상세 응답이 상태 배지, 요약, 권장 액션을 포함해야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    invoice_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    mock_invoice_repo.return_value = invoice_repo

    partner_doc = {
        "_id": "SPAR-001",
        "partner_name": "총판A",
        "commission_rate": 7.5,
        "territory": "서울",
        "partner_type": "distributor",
        "is_active": True,
    }
    partner_repo.find_many.return_value = [partner_doc]
    partner_repo.find_by_id.return_value = partner_doc
    customer_repo.find_many.return_value = [
        {
            "_id": "CUST-001",
            "customer_name": "고객A",
            "sales_partner_id": "SPAR-001",
        }
    ]
    invoice_repo.find_many.return_value = [
        {
            "_id": "SINV-001",
            "customer_id": "CUST-001",
            "docstatus": 1,
            "grand_total": 110000,
            "outstanding_amount": 30000,
            "sales_partner_id": "SPAR-001",
            "sales_partner_name": "총판A",
            "sales_partner_commission_rate": 7.5,
            "posting_date": "2026-04-10",
        }
    ]

    list_response = test_client.get(f"{_BASE_URL}?status_badge=active_collection_risk")

    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    partner = payload["data"][0]
    assert partner["status_badge"] == "active_collection_risk"
    assert partner["recommended_action"] == "review_receivables"
    assert partner["summary"] == {
        "linked_customer_count": 1,
        "historical_customer_count": 1,
        "submitted_invoice_count": 1,
        "submitted_sales_amount": 110000.0,
        "outstanding_amount": 30000.0,
        "expected_commission_amount": 8250.0,
        "last_invoice_posting_date": "2026-04-10",
    }
    assert partner["available_actions"] == [
        "assign_customer",
        "view_sales_history",
        "review_receivables",
        "edit",
    ]

    detail_response = test_client.get(f"{_BASE_URL}/SPAR-001")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status_badge"] == "active_collection_risk"
    assert detail["summary"]["submitted_invoice_count"] == 1
    assert detail["summary"]["expected_commission_amount"] == 8250.0


def test_판매파트너_상세_조회_미존재_404(
    mock_collection: MagicMock, test_client: MagicMock
) -> None:
    """GET /api/v1/sales-partners/{doc_id} -- 없는 파트너는 404를 반환한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404


def test_판매파트너_수정_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """PUT /api/v1/sales-partners/{doc_id} -- 정상 수정 시 200을 반환한다."""
    mock_collection.find_one.return_value = {"_id": "SPAR-001", "partner_name": "파트너A"}
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = test_client.put(
        f"{_BASE_URL}/SPAR-001",
        json={"partner_name": "파트너B"},
    )
    assert response.status_code == 200


@patch("oneerp_selling_app.routes.sales_partners._get_invoice_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_판매파트너에_고객을_배정하고_매출요약을_조회한다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """고객을 판매파트너에 배정하면 파트너별 매출/미수/예상 수수료 요약을 볼 수 있어야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    invoice_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    mock_invoice_repo.return_value = invoice_repo

    partner_repo.find_by_id.return_value = {
        "_id": "SPAR-001",
        "partner_name": "총판A",
        "commission_rate": 5.0,
        "territory": "서울",
        "partner_type": "distributor",
        "is_active": True,
    }
    customer_repo.find_by_id.return_value = {
        "_id": "CUST-001",
        "customer_name": "고객A",
    }
    customer_repo.find_many.return_value = [
        {
            "_id": "CUST-001",
            "customer_name": "고객A",
            "sales_partner_id": "SPAR-001",
            "sales_partner_name": "총판A",
        }
    ]
    invoice_repo.find_many.return_value = [
        {
            "_id": "SINV-001",
            "customer_id": "CUST-001",
            "docstatus": 1,
            "grand_total": 110000,
            "outstanding_amount": 50000,
        },
        {
            "_id": "SINV-002",
            "customer_id": "CUST-001",
            "docstatus": 0,
            "grand_total": 44000,
            "outstanding_amount": 44000,
        },
    ]

    assign_response = test_client.post(f"{_BASE_URL}/SPAR-001/customers/CUST-001")
    assert assign_response.status_code == 200
    assert assign_response.json()["partner_id"] == "SPAR-001"
    customer_repo.update_by_id.assert_called_once_with(
        "CUST-001",
        {
            "sales_partner_id": "SPAR-001",
            "sales_partner_name": "총판A",
        },
    )

    summary_response = test_client.get(f"{_BASE_URL}/SPAR-001/summary")
    assert summary_response.status_code == 200
    payload = summary_response.json()
    assert payload["partner"]["partner_name"] == "총판A"
    assert payload["summary"]["linked_customer_count"] == 1
    assert payload["summary"]["historical_customer_count"] == 1
    assert payload["summary"]["submitted_invoice_count"] == 1
    assert payload["summary"]["submitted_sales_amount"] == 110000.0
    assert payload["summary"]["outstanding_amount"] == 50000.0
    assert payload["summary"]["expected_commission_amount"] == 5500.0


@patch("oneerp_selling_app.routes.sales_partners._get_invoice_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_고객_재배정후에도_판매파트너_실적요약은_거래스냅샷으로_유지된다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """거래 문서에 남긴 파트너 스냅샷으로 historical 요약을 유지해야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    invoice_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    mock_invoice_repo.return_value = invoice_repo

    partner_repo.find_by_id.return_value = {
        "_id": "SPAR-LEGACY",
        "partner_name": "구총판",
        "commission_rate": 5.0,
        "is_active": True,
    }
    customer_repo.find_many.return_value = []
    invoice_repo.find_many.return_value = [
        {
            "_id": "SINV-LEGACY",
            "customer_id": "CUST-OLD",
            "docstatus": 1,
            "grand_total": 220000,
            "outstanding_amount": 0,
            "sales_partner_id": "SPAR-LEGACY",
            "sales_partner_name": "구총판",
            "sales_partner_commission_rate": 5.0,
            "posting_date": "2026-04-01",
        }
    ]

    response = test_client.get(f"{_BASE_URL}/SPAR-LEGACY/summary")

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["linked_customer_count"] == 0
    assert summary["historical_customer_count"] == 1
    assert summary["submitted_invoice_count"] == 1
    assert summary["expected_commission_amount"] == 11000.0


@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_비활성_판매파트너에는_고객을_배정할_수_없다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """비활성 파트너는 고객 배정을 받을 수 없어야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    partner_repo.find_by_id.return_value = {
        "_id": "SPAR-002",
        "partner_name": "중단 파트너",
        "is_active": False,
    }
    customer_repo.find_by_id.return_value = {
        "_id": "CUST-001",
        "customer_name": "고객A",
    }

    response = test_client.post(f"{_BASE_URL}/SPAR-002/customers/CUST-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-SELL-041"


@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_연결된_고객이_있는_판매파트너는_삭제할_수_없다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """고객이 연결된 판매 파트너는 삭제를 차단해야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    partner_repo.find_by_id.return_value = {
        "_id": "SPAR-001",
        "partner_name": "총판A",
        "docstatus": 0,
    }
    customer_repo.find_many.return_value = [
        {
            "_id": "CUST-001",
            "customer_name": "고객A",
            "sales_partner_id": "SPAR-001",
        }
    ]

    response = test_client.delete(f"{_BASE_URL}/SPAR-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-SELL-042"


@patch("oneerp_selling_app.routes.sales_partners._get_invoice_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_customer_repo")
@patch("oneerp_selling_app.routes.sales_partners._get_partner_repo")
def test_거래이력이_있는_판매파트너는_삭제할_수_없다(
    mock_partner_repo: MagicMock,
    mock_customer_repo: MagicMock,
    mock_invoice_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """현재 연결 고객이 없어도 제출된 송장 이력이 있으면 삭제를 차단해야 한다."""
    partner_repo = MagicMock()
    customer_repo = MagicMock()
    invoice_repo = MagicMock()
    mock_partner_repo.return_value = partner_repo
    mock_customer_repo.return_value = customer_repo
    mock_invoice_repo.return_value = invoice_repo

    partner_repo.find_by_id.return_value = {
        "_id": "SPAR-001",
        "partner_name": "총판A",
        "docstatus": 0,
    }
    customer_repo.find_many.return_value = []
    invoice_repo.find_many.return_value = [
        {
            "_id": "SINV-001",
            "docstatus": 1,
            "sales_partner_id": "SPAR-001",
            "grand_total": 110000,
            "outstanding_amount": 0,
        }
    ]

    response = test_client.delete(f"{_BASE_URL}/SPAR-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-SELL-044"
