"""견적서(Quotation) CRUD API 테스트."""

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


@patch("oneerp_selling_app.routes.quotations._get_repo")
@patch("oneerp_selling_app.routes.quotations.generate_name", return_value="QTN-2026-00001")
def test_견적서_생성(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": "CUST-001",
            "customer_name": "테스트 고객",
            "transaction_date": "2026-03-17",
            "items": [
                {"item_code": "A", "item_name": "상품", "qty": 10, "rate": 1000, "amount": 10000},
            ],
        },
    )
    assert response.status_code == 201


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_목록_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "QTN-001", "customer_name": "고객"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/quotations?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_상세_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "customer_name": "고객"}
    mock_repo.return_value = repo
    response = client.get("/api/v1/quotations/QTN-001")
    assert response.status_code == 200


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/quotations/NONE")
    assert response.status_code == 404


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_수정(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 0}
    repo.update_by_id.return_value = True
    mock_get_repo.return_value = repo
    response = client.put(
        "/api/v1/quotations/QTN-001",
        json={"customer_name": "수정된 고객"},
    )
    assert response.status_code == 200
    repo.update_by_id.assert_called_once()


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_수정_제출상태_거부(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 1}
    mock_get_repo.return_value = repo
    response = client.put(
        "/api/v1/quotations/QTN-001",
        json={"customer_name": "변경"},
    )
    assert response.status_code == 400


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_제출(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 0}
    repo.submit.return_value = True
    mock_repo.return_value = repo
    response = client.post("/api/v1/quotations/QTN-001/submit")
    assert response.status_code == 200


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_취소(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 1}
    repo.cancel.return_value = True
    mock_get_repo.return_value = repo
    response = client.post("/api/v1/quotations/QTN-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("QTN-001")


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_삭제(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 0}
    repo.delete_by_id.return_value = True
    mock_get_repo.return_value = repo
    response = client.delete("/api/v1/quotations/QTN-001")
    assert response.status_code == 204


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_취소_초안상태_거부(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 0}
    mock_get_repo.return_value = repo
    response = client.post("/api/v1/quotations/QTN-001/cancel")
    assert response.status_code == 400


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_삭제_제출상태_거부(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QTN-001", "docstatus": 1}
    mock_get_repo.return_value = repo

    response = client.delete("/api/v1/quotations/QTN-001")

    assert response.status_code == 400
    repo.delete_by_id.assert_not_called()


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_메일발송(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "QTN-001",
        "docstatus": 1,
        "customer_name": "고객",
        "grand_total": 15000,
        "items": [{"item_name": "상품", "qty": 1, "rate": 15000, "amount": 15000}],
    }
    mock_get_repo.return_value = repo

    response = client.post(
        "/api/v1/quotations/QTN-001/send-email",
        json={
            "recipient_email": "customer@example.com",
            "subject": "견적서 안내",
            "message": "첨부된 견적서를 확인해 주세요.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pdf_download_url"].endswith("/api/v1/quotations/QTN-001/pdf")
    assert "portal/quotations/QTN-001/sign" in body["portal_sign_url"]


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_PDF_다운로드(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "QTN-001",
        "docstatus": 1,
        "customer_name": "고객",
        "transaction_date": "2026-04-08T00:00:00+00:00",
        "items": [{"item_name": "상품", "qty": 2, "rate": 5000, "amount": 10000}],
        "total": 10000,
        "grand_total": 10000,
    }
    mock_get_repo.return_value = repo

    response = client.get("/api/v1/quotations/QTN-001/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"].endswith('QTN-001.pdf"')


@patch("oneerp_selling_app.routes.quotations._get_repo")
def test_견적서_포털_전자서명(mock_get_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "QTN-001",
        "docstatus": 1,
        "portal_access_token": "quote-token",
        "customer_name": "고객",
        "items": [{"item_name": "상품", "qty": 1, "rate": 10000, "amount": 10000}],
        "grand_total": 10000,
    }
    mock_get_repo.return_value = repo

    response = client.post(
        "/api/v1/portal/quotations/QTN-001/sign",
        json={
            "token": "quote-token",
            "signer_name": "김고객",
            "signer_email": "customer@example.com",
            "signature_text": "김고객",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["signature_status"] == "signed"
    assert body["id"] == "QTN-001"
