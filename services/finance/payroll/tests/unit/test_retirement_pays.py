"""퇴직금(RetirementPay) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_payroll_app.routes.retirement_pays import router

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


@patch("oneerp_payroll_app.routes.retirement_pays._get_repo")
@patch("oneerp_payroll_app.routes.retirement_pays.generate_name", return_value="RTP-2026-00001")
def test_퇴직금_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """퇴직금 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post("/api/v1/retirement-pays/", json={"employee_id": "EMP-001"})
    assert response.status_code == 201
    assert response.json()["retirement_pay_id"] == "RTP-2026-00001"


@patch("oneerp_payroll_app.routes.retirement_pays._get_repo")
def test_퇴직금_목록_조회(mock_repo: MagicMock) -> None:
    """퇴직금 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "RTP-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/retirement-pays/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_payroll_app.routes.retirement_pays._get_repo")
def test_퇴직금_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 퇴직금 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/retirement-pays/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_payroll_app.routes.retirement_pays._get_repo")
def test_퇴직금_제출_정상(mock_repo: MagicMock) -> None:
    """초안 상태 퇴직금 제출이 정상 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "RTP-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/retirement-pays/RTP-001/submit")
    assert response.status_code == 200


@patch("oneerp_payroll_app.routes.retirement_pays._get_repo")
def test_퇴직금_취소_정상(mock_repo: MagicMock) -> None:
    """제출된 퇴직금 취소가 정상 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "RTP-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/retirement-pays/RTP-001/cancel")
    assert response.status_code == 200
