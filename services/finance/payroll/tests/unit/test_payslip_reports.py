"""급여명세서 PDF 리포트 엔드포인트 테스트.

`GET /api/v1/payroll/payslips/{id}` - FE PDF 라우트 연동용.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_payroll_app.routes.payslip_reports import router

_FAKE_USER = CurrentUser(
    sub="test-user",
    tenant_id="tenant-a",
    roles=("admin",),
    permissions=("*:*",),
)

_OTHER_TENANT_USER = CurrentUser(
    sub="other-user",
    tenant_id="tenant-b",
    roles=("admin",),
    permissions=("*:*",),
)

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
_app.dependency_overrides[get_current_user] = lambda: _FAKE_USER
client = TestClient(_app)


def _make_salary_slip_doc() -> dict:
    """테스트용 SalarySlip 도큐먼트 스텁."""
    return {
        "_id": "SLIP-2026-00001",
        "tenant_id": "tenant-a",
        "employee_id": "EMP-0001",
        "employee_name": "김직원",
        "department": "기술본부",
        "designation": "선임연구원",
        "posting_date": date(2026, 3, 15),
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "earnings": [
            {"name": "기본급", "amount": Decimal(4000000)},
            {"name": "직책수당", "amount": Decimal(300000)},
        ],
        "deductions": [
            {"name": "국민연금", "amount": Decimal(180000)},
            {"name": "건강보험", "amount": Decimal(142000)},
            {"name": "근로소득세", "amount": Decimal(250000)},
        ],
        "gross_pay": Decimal(4300000),
        "total_deduction": Decimal(572000),
        "net_pay": Decimal(3728000),
    }


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_급여명세서_조회_정상_매핑(mock_repo: MagicMock) -> None:
    """SalarySlip 존재 시 정규화된 PayslipResponse 를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = _make_salary_slip_doc()
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/SLIP-2026-00001")
    assert response.status_code == 200

    body = response.json()
    assert body["employee"]["employee_id"] == "EMP-0001"
    assert body["employee"]["name"] == "김직원"
    assert body["employee"]["department"] == "기술본부"
    assert body["employee"]["position"] == "선임연구원"
    assert body["period"] == {"year": 2026, "month": 3}
    assert len(body["earnings"]) == 2
    assert body["earnings"][0]["label"] == "기본급"
    assert Decimal(body["earnings"][0]["amount"]) == Decimal(4000000)
    assert len(body["deductions"]) == 3
    assert Decimal(body["net_pay"]) == Decimal(3728000)
    # 회사 정보는 FE CompanyInfo 와 일치하는 camelCase 유지
    assert "businessNumber" in body["company"]


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_급여명세서_미존재_시_fallback(mock_repo: MagicMock) -> None:
    """미존재 ID 에 대해 Wave 5 fallback mock 을 반환한다(404 아님)."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/NOT-EXIST")
    assert response.status_code == 200

    body = response.json()
    # fallback 은 요청 ID 를 그대로 employee_id 로 복사한다
    assert body["employee"]["employee_id"] == "NOT-EXIST"
    assert len(body["earnings"]) >= 1
    assert len(body["deductions"]) >= 1
    # net_pay 는 fallback 상수
    assert Decimal(body["net_pay"]) > 0


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_테넌트_격리_Repository_호출(mock_repo: MagicMock) -> None:
    """Repository 가 현재 사용자의 tenant_id 로 바인딩되는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = _make_salary_slip_doc()
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/SLIP-001")
    assert response.status_code == 200
    # _get_repo 가 올바른 tenant_id 로 호출되었는지 확인
    mock_repo.assert_called_with("tenant-a")


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_다른_테넌트_사용자는_별도_Repository(mock_repo: MagicMock) -> None:
    """다른 테넌트 사용자로 호출 시 해당 테넌트 Repository 가 사용된다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None  # tenant-b 에는 데이터 없음
    mock_repo.return_value = repo

    other_app = FastAPI()
    other_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
    other_app.include_router(router)
    other_app.dependency_overrides[get_current_user] = lambda: _OTHER_TENANT_USER
    other_client = TestClient(other_app)

    response = other_client.get("/api/v1/payroll/payslips/SLIP-001")
    assert response.status_code == 200
    mock_repo.assert_called_with("tenant-b")


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_net_pay_누락_시_자동_계산(mock_repo: MagicMock) -> None:
    """doc.net_pay 가 0/누락이면 earnings - deductions 로 재계산한다."""
    doc = _make_salary_slip_doc()
    doc["net_pay"] = Decimal(0)  # 누락 시뮬레이션
    repo = MagicMock()
    repo.find_by_id.return_value = doc
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/SLIP-001")
    assert response.status_code == 200

    body = response.json()
    # 4_300_000 - 572_000 = 3_728_000
    assert Decimal(body["net_pay"]) == Decimal(3728000)


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_earnings_deductions_빈_배열_처리(mock_repo: MagicMock) -> None:
    """earnings/deductions 가 비어있어도 응답이 정상 생성된다."""
    doc = _make_salary_slip_doc()
    doc["earnings"] = []
    doc["deductions"] = []
    doc["net_pay"] = Decimal(0)
    repo = MagicMock()
    repo.find_by_id.return_value = doc
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/SLIP-001")
    assert response.status_code == 200

    body = response.json()
    assert body["earnings"] == []
    assert body["deductions"] == []
    assert Decimal(body["net_pay"]) == Decimal(0)


@patch("oneerp_payroll_app.routes.payslip_reports._get_repo")
def test_posting_date_문자열_파싱(mock_repo: MagicMock) -> None:
    """posting_date 가 ISO 문자열 형태여도 period 가 올바르게 추출된다."""
    doc = _make_salary_slip_doc()
    doc["posting_date"] = "2026-07-15"
    repo = MagicMock()
    repo.find_by_id.return_value = doc
    mock_repo.return_value = repo

    response = client.get("/api/v1/payroll/payslips/SLIP-001")
    assert response.status_code == 200

    body = response.json()
    assert body["period"] == {"year": 2026, "month": 7}


def test_응답_스키마_검증() -> None:
    """PayslipResponse 스키마가 FE PayslipProps 와 정합한지 직접 검증."""
    from oneerp_payroll_app.schemas.payslip_schemas import PayslipResponse

    fields = set(PayslipResponse.model_fields.keys())
    # FE PayslipProps 의 필수 키
    assert {"employee", "period", "earnings", "deductions", "net_pay", "company"} <= fields
