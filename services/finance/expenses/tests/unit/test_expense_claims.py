"""경비청구(ExpenseClaim) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_expenses_app.routes.expense_claims import router

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


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
@patch("oneerp_expenses_app.routes.expense_claims.generate_name", return_value="EXP-2026-00001")
def test_경비청구_생성_정상(mock_name: MagicMock, mock_service: MagicMock) -> None:
    """경비청구 생성 API가 정상 동작하는지 검증한다."""
    mock_service.return_value = MagicMock()
    response = client.post("/api/v1/expense-claims/", json={"employee_id": "EMP-001"})
    assert response.status_code == 201
    assert response.json()["id"] == "EXP-2026-00001"


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_목록_조회(mock_service: MagicMock) -> None:
    """경비청구 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    service = MagicMock()
    service.list_page.return_value = {
        "data": [{"_id": "EXP-001"}],
        "total": 1,
        "page": 1,
        "page_size": 10,
    }
    mock_service.return_value = service
    response = client.get("/api/v1/expense-claims/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_조회_미존재_404(mock_service: MagicMock) -> None:
    """존재하지 않는 경비청구 조회 시 404를 반환하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.side_effect = OneERPError(
        status_code=404, error="not_found", detail="경비청구를 찾을 수 없습니다"
    )
    mock_service.return_value = service
    response = client.get("/api/v1/expense-claims/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_수정_초안만_허용(mock_service: MagicMock) -> None:
    """BR-EXP-008: 제출된(docstatus=1) 경비청구를 PUT으로 수정하면 400 에러."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "EXP-001", "docstatus": 1}
    mock_service.return_value = service
    response = client.put("/api/v1/expense-claims/EXP-001", json={"employee_id": "EMP-002"})
    assert response.status_code == 400


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_수정_취소상태_불가(mock_service: MagicMock) -> None:
    """BR-EXP-008: 취소된(docstatus=2) 경비청구를 PUT으로 수정하면 400 에러."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "EXP-002", "docstatus": 2}
    mock_service.return_value = service
    response = client.put("/api/v1/expense-claims/EXP-002", json={"employee_id": "EMP-003"})
    assert response.status_code == 400


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_수정_초안_정상(mock_service: MagicMock) -> None:
    """BR-EXP-008: 초안(docstatus=0) 경비청구는 PUT 수정이 정상 동작한다."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "EXP-003", "docstatus": 0}
    mock_service.return_value = service
    response = client.put("/api/v1/expense-claims/EXP-003", json={"employee_id": "EMP-004"})
    assert response.status_code == 200


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_제출_정상(mock_service: MagicMock) -> None:
    """초안 상태 경비청구 제출이 정상 동작하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "EXP-001", "docstatus": 0}
    mock_service.return_value = service
    response = client.post("/api/v1/expense-claims/EXP-001/submit")
    assert response.status_code == 200


@patch("oneerp_expenses_app.routes.expense_claims._get_service")
def test_경비청구_취소_정상(mock_service: MagicMock) -> None:
    """제출된 경비청구 취소가 정상 동작하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "EXP-001", "docstatus": 1}
    mock_service.return_value = service
    response = client.post("/api/v1/expense-claims/EXP-001/cancel")
    assert response.status_code == 200
