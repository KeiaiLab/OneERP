"""법인카드거래(CorporateCardTransaction) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_expenses_app.routes.corporate_card_transactions import router

_FAKE_USER = CurrentUser(
    sub="test-user",
    tenant_id="test-tenant",
    roles=("admin",),
    permissions=("*:*",),
)

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
client = TestClient(_app)


@patch("oneerp_expenses_app.routes.corporate_card_transactions._get_service")
@patch(
    "oneerp_expenses_app.routes.corporate_card_transactions.generate_name",
    return_value="CCT-2026-00001",
)
def test_법인카드거래_생성_정상(mock_name: MagicMock, mock_service: MagicMock) -> None:
    """법인카드거래 생성 API가 정상 동작하는지 검증한다."""
    mock_service.return_value = MagicMock()
    response = client.post(
        "/api/v1/corporate-card-transactions/",
        json={"card_number": "1234-5678"},
    )
    assert response.status_code == 201
    assert response.json()["corporate_card_transaction_id"] == "CCT-2026-00001"


@patch("oneerp_expenses_app.routes.corporate_card_transactions._get_service")
def test_법인카드거래_목록_조회(mock_service: MagicMock) -> None:
    """법인카드거래 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    service = MagicMock()
    service.list_page.return_value = {
        "data": [{"_id": "CCT-001"}],
        "total": 1,
        "page": 1,
        "page_size": 10,
    }
    mock_service.return_value = service
    response = client.get("/api/v1/corporate-card-transactions/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_expenses_app.routes.corporate_card_transactions._get_service")
def test_법인카드거래_조회_미존재_404(mock_service: MagicMock) -> None:
    """존재하지 않는 법인카드거래 조회 시 404를 반환하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.side_effect = OneERPError(
        status_code=404, error="not_found", detail="법인카드거래를 찾을 수 없습니다"
    )
    mock_service.return_value = service
    response = client.get("/api/v1/corporate-card-transactions/NOT-EXIST")
    assert response.status_code == 404
