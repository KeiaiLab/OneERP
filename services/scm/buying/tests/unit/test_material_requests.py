"""자재요청(MaterialRequest) 사용자 흐름 테스트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_buying_app.main import app
from oneerp_core.document import DocStatus

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


@patch("oneerp_buying_app.routes.material_requests._get_repo")
@patch("oneerp_buying_app.routes.material_requests.generate_name", return_value="MR-2026-00001")
@patch("oneerp_buying_app.routes.material_requests._suggest_supplier_for_item")
def test_자재요청_생성_정상(
    mock_suggest_supplier: MagicMock,
    mock_name: MagicMock,
    mock_repo: MagicMock,
) -> None:
    """예상금액/예산/추천 공급업체를 계산해 저장한다."""
    repo = MagicMock()
    mock_repo.return_value = repo
    mock_suggest_supplier.return_value = {
        "supplier_id": "SUP-001",
        "supplier_name": "추천공급업체",
        "source": "pricing_rule",
    }

    response = client.post(
        "/api/v1/material-requests",
        json={
            "request_type": "purchase",
            "required_date": "2026-03-20",
            "budget_limit": 200000,
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "원자재A",
                    "qty": 10,
                    "warehouse": "WH-001",
                    "item_group": "원자재",
                    "estimated_unit_cost": 12000,
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "MR-2026-00001"
    inserted_doc = repo.insert.call_args[0][0]
    assert inserted_doc.estimated_total_amount == 120000
    assert inserted_doc.budget_status == "within_budget"
    assert inserted_doc.suggested_supplier_id == "SUP-001"
    assert inserted_doc.items[0].estimated_amount == 120000


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_목록_조회(mock_repo: MagicMock) -> None:
    """페이지네이션 목록 응답 구조를 유지한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "MR-001", "request_type": "purchase"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo

    response = client.get("/api/v1/material-requests?page=1&page_size=10")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """없는 자재요청은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.get("/api/v1/material-requests/NOT-EXIST")

    assert response.status_code == 404


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_제출_정상(mock_repo: MagicMock) -> None:
    """승인 불필요한 구매요청은 제출 즉시 이벤트를 발행한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.DRAFT,
        "request_type": "purchase",
        "estimated_total_amount": 0,
        "budget_limit": 0,
        "items": [{"item_code": "ITEM-001"}],
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/material-requests/MR-001/submit")

    assert response.status_code == 200
    repo.update_with_event.assert_called_once()


@patch("oneerp_buying_app.routes.material_requests.BuyerApprovalService")
@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_제출_시_승인요청으로_보류된다(
    mock_repo: MagicMock,
    mock_approval_service_cls: MagicMock,
) -> None:
    """예산/품목 그룹이 있으면 승인 대기로 전환되고 PO 생성 이벤트를 미룬다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.DRAFT,
        "request_type": "purchase",
        "estimated_total_amount": 2500000,
        "budget_limit": 3000000,
        "items": [{"item_code": "ITEM-001", "item_group": "원자재", "estimated_amount": 2500000}],
    }
    mock_repo.return_value = repo
    approval_service = MagicMock()
    approval_service.get_approver.return_value = {
        "approver": "manager-001",
        "matrix_id": "BAM-001",
    }
    mock_approval_service_cls.return_value = approval_service

    response = client.post("/api/v1/material-requests/MR-001/submit")

    assert response.status_code == 200
    assert response.json()["approval_status"] == "pending"
    repo.update_by_id.assert_called_once()
    update_payload = repo.update_by_id.call_args[0][1]
    assert update_payload["docstatus"] == DocStatus.SUBMITTED
    assert update_payload["required_approver"] == "manager-001"
    repo.update_with_event.assert_not_called()


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_제출_시_예산초과는_거부된다(mock_repo: MagicMock) -> None:
    """예산 초과 구매요청은 submit 단계에서 차단한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.DRAFT,
        "request_type": "purchase",
        "estimated_total_amount": 1500000,
        "budget_limit": 1000000,
        "items": [{"item_code": "ITEM-001", "item_group": "원자재", "estimated_amount": 1500000}],
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/material-requests/MR-001/submit")

    assert response.status_code == 422
    repo.update_by_id.assert_not_called()
    repo.update_with_event.assert_not_called()


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_승인_시_구매주문_생성_이벤트를_발행한다(mock_repo: MagicMock) -> None:
    """지정된 결재자가 승인하면 approved로 전환되고 후속 이벤트를 발행한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.SUBMITTED,
        "approval_status": "pending",
        "required_approver": "test-user",
    }
    mock_repo.return_value = repo

    response = client.post("/api/v1/material-requests/MR-001/approve")

    assert response.status_code == 200
    assert response.json()["approval_status"] == "approved"
    repo.update_with_event.assert_called_once()
    update_payload = repo.update_with_event.call_args[0][1]
    assert update_payload["approval_status"] == "approved"
    assert update_payload["approved_by"] == "test-user"
    assert isinstance(update_payload["approved_at"], datetime)
    assert update_payload["approved_at"].tzinfo == UTC


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_반려_시_승인상태를_거절로_변경한다(mock_repo: MagicMock) -> None:
    """지정된 결재자는 자재요청을 반려할 수 있고 후속 이벤트는 발행되지 않는다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.SUBMITTED,
        "approval_status": "pending",
        "required_approver": "test-user",
    }
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/material-requests/MR-001/reject",
        params={"reason": "예산 조정 필요"},
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "rejected"
    repo.update_by_id.assert_called_once()
    update_payload = repo.update_by_id.call_args[0][1]
    assert update_payload["approval_status"] == "rejected"
    assert update_payload["rejected_by"] == "test-user"
    repo.update_with_event.assert_not_called()


@patch("oneerp_buying_app.routes.material_requests.PurchaseProcessService")
@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청에서_RFQ를_직접_생성한다(
    mock_repo: MagicMock,
    mock_process_service_cls: MagicMock,
) -> None:
    """구매 자재요청에서 RFQ를 바로 생성한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.DRAFT,
        "request_type": "purchase",
        "items": [{"item_code": "ITEM-001", "qty": 3}],
    }
    mock_repo.return_value = repo
    process_service = MagicMock()
    process_service.create_rfq_from_mr.return_value = {
        "rfq_id": "RFQ-001",
        "supplier_count": 2,
        "item_count": 1,
    }
    mock_process_service_cls.return_value = process_service

    response = client.post(
        "/api/v1/material-requests/MR-001/create-rfq",
        json={
            "suppliers": ["SUP-001", "SUP-002"],
            "transaction_date": "2026-03-18",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "RFQ-001"
    process_service.create_rfq_from_mr.assert_called_once_with(
        "MR-001",
        suppliers=["SUP-001", "SUP-002"],
        transaction_date=date(2026, 3, 18),
    )


@patch("oneerp_buying_app.routes.material_requests.PurchaseProcessService")
@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_구매유형이_아닌_자재요청은_RFQ를_직접_생성할_수_없다(
    mock_repo: MagicMock,
    mock_process_service_cls: MagicMock,
) -> None:
    """Transfer/Manufacture 요청은 RFQ 전환을 허용하지 않는다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "MR-001",
        "docstatus": DocStatus.DRAFT,
        "request_type": "transfer",
        "items": [{"item_code": "ITEM-001", "qty": 3}],
    }
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/material-requests/MR-001/create-rfq",
        json={"suppliers": ["SUP-001"]},
    )

    assert response.status_code == 422
    mock_process_service_cls.assert_not_called()


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_자재요청_취소_정상(mock_repo: MagicMock) -> None:
    """제출된 문서는 취소할 수 있다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "MR-001", "docstatus": DocStatus.SUBMITTED}
    mock_repo.return_value = repo

    response = client.post("/api/v1/material-requests/MR-001/cancel")

    assert response.status_code == 200
    repo.cancel.assert_called_once_with("MR-001")


@patch("oneerp_buying_app.routes.material_requests._get_repo")
def test_제출된_자재요청_삭제는_거부된다(mock_repo: MagicMock) -> None:
    """제출 문서는 삭제할 수 없다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "MR-001", "docstatus": DocStatus.SUBMITTED}
    mock_repo.return_value = repo

    response = client.delete("/api/v1/material-requests/MR-001")

    assert response.status_code == 400
    repo.delete_by_id.assert_not_called()
