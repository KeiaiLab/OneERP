"""급여세신고(PayrollTaxReturn) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_payroll_app.routes.payroll_tax_returns import router

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


@patch("oneerp_payroll_app.routes.payroll_tax_returns._get_repo")
@patch("oneerp_payroll_app.routes.payroll_tax_returns.generate_name", return_value="PTR-2026-00001")
def test_급여세신고_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """급여세신고 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/payroll-tax-returns/",
        json={"period": "2026-03", "tax_type": "소득세"},
    )
    assert response.status_code == 201
    assert response.json()["payroll_tax_return_id"] == "PTR-2026-00001"


@patch("oneerp_payroll_app.routes.payroll_tax_returns._get_repo")
def test_급여세신고_목록_조회(mock_repo: MagicMock) -> None:
    """급여세신고 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "PTR-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/payroll-tax-returns/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_payroll_app.routes.payroll_tax_returns._get_repo")
def test_급여세신고_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 급여세신고 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/payroll-tax-returns/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_payroll_app.routes.payroll_tax_returns._get_repo")
def test_급여세신고_제출_정상(mock_repo: MagicMock) -> None:
    """초안 상태 급여세신고 제출이 정상 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PTR-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/payroll-tax-returns/PTR-001/submit")
    assert response.status_code == 200


@patch("oneerp_payroll_app.routes.payroll_tax_returns._get_repo")
def test_급여세신고_취소_정상(mock_repo: MagicMock) -> None:
    """제출된 급여세신고 취소가 정상 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PTR-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/payroll-tax-returns/PTR-001/cancel")
    assert response.status_code == 200
