"""출장신청(TravelRequest) API 엔드포인트 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.auth import CurrentUser, get_current_user
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_expenses_app.routes.travel_requests import router
from pydantic import ValidationError

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


@patch("oneerp_expenses_app.routes.travel_requests._get_service")
@patch("oneerp_expenses_app.routes.travel_requests.generate_name", return_value="TR-2026-00001")
def test_출장신청_생성_정상(mock_name: MagicMock, mock_service: MagicMock) -> None:
    """출장신청 생성 API가 정상 동작하는지 검증한다."""
    mock_service.return_value = MagicMock()
    response = client.post("/api/v1/travel-requests/", json={"employee_id": "EMP-001"})
    assert response.status_code == 201
    assert response.json()["travel_request_id"] == "TR-2026-00001"


@patch("oneerp_expenses_app.routes.travel_requests._get_service")
def test_출장신청_목록_조회(mock_service: MagicMock) -> None:
    """출장신청 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    service = MagicMock()
    service.list_page.return_value = {
        "data": [{"_id": "TR-001"}],
        "total": 1,
        "page": 1,
        "page_size": 10,
    }
    mock_service.return_value = service
    response = client.get("/api/v1/travel-requests/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_expenses_app.routes.travel_requests._get_service")
def test_출장신청_조회_미존재_404(mock_service: MagicMock) -> None:
    """존재하지 않는 출장신청 조회 시 404를 반환하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.side_effect = OneERPError(
        status_code=404, error="not_found", detail="출장신청을 찾을 수 없습니다"
    )
    mock_service.return_value = service
    response = client.get("/api/v1/travel-requests/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_expenses_app.routes.travel_requests._get_service")
def test_출장신청_제출_정상(mock_service: MagicMock) -> None:
    """초안 상태 출장신청 제출이 정상 동작하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "TR-001", "docstatus": 0}
    mock_service.return_value = service
    response = client.post("/api/v1/travel-requests/TR-001/submit")
    assert response.status_code == 200


@patch("oneerp_expenses_app.routes.travel_requests._get_service")
def test_출장신청_취소_정상(mock_service: MagicMock) -> None:
    """제출된 출장신청 취소가 정상 동작하는지 검증한다."""
    service = MagicMock()
    service.get_or_raise.return_value = {"_id": "TR-001", "docstatus": 1}
    mock_service.return_value = service
    response = client.post("/api/v1/travel-requests/TR-001/cancel")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 갭 1: POST /{doc_id}/settle 엔드포인트 테스트
# ---------------------------------------------------------------------------


@patch("oneerp_expenses_app.routes.travel_requests.ExpenseService")
def test_출장정산_엔드포인트_정상(mock_svc_cls: MagicMock) -> None:
    """settle 엔드포인트가 ExpenseService.settle_travel을 호출하고 결과를 반환한다."""
    mock_svc = MagicMock()
    mock_svc.settle_travel.return_value = {
        "travel_request_id": "TR-001",
        "claim_id": "EC-001",
        "estimated_cost": 500000,
        "actual_cost": 350000,
        "difference": -150000.0,
    }
    mock_svc_cls.return_value = mock_svc

    response = client.post(
        "/api/v1/travel-requests/TR-001/settle",
        json={
            "actual_expenses": [
                {"expense_type": "숙박", "amount": 200000, "description": "호텔"},
                {"expense_type": "교통", "amount": 150000, "description": "KTX"},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["estimated_cost"] == 500000
    assert data["actual_cost"] == 350000
    assert data["difference"] == -150000.0
    assert data["claim_id"] == "EC-001"
    mock_svc.settle_travel.assert_called_once()


@patch("oneerp_expenses_app.routes.travel_requests.ExpenseService")
def test_출장정산_미존재_출장_404(mock_svc_cls: MagicMock) -> None:
    """존재하지 않는 출장 ID로 정산 시 404를 반환한다."""
    mock_svc = MagicMock()
    mock_svc.settle_travel.side_effect = OneERPError(
        status_code=404, error="not_found", detail="출장 신청을 찾을 수 없습니다"
    )
    mock_svc_cls.return_value = mock_svc

    response = client.post(
        "/api/v1/travel-requests/TR-999/settle",
        json={"actual_expenses": []},
    )

    assert response.status_code == 404


@patch("oneerp_expenses_app.routes.travel_requests.ExpenseService")
def test_출장정산_빈_경비목록(mock_svc_cls: MagicMock) -> None:
    """빈 경비 목록으로도 정산이 가능하다 (actual_cost = 0)."""
    mock_svc = MagicMock()
    mock_svc.settle_travel.return_value = {
        "travel_request_id": "TR-001",
        "claim_id": "EC-002",
        "estimated_cost": 100000,
        "actual_cost": 0,
        "difference": -100000.0,
    }
    mock_svc_cls.return_value = mock_svc

    response = client.post(
        "/api/v1/travel-requests/TR-001/settle",
        json={"actual_expenses": []},
    )

    assert response.status_code == 200
    assert response.json()["actual_cost"] == 0


# ---------------------------------------------------------------------------
# 갭 2: BR-EXP-011 출장 기간 검증 (departure_date <= return_date)
# ---------------------------------------------------------------------------


class TestBR_EXP_011_출장기간검증:
    """TravelRequestCreate 모델의 departure/return 날짜 검증 테스트."""

    def test_출발일_귀환일_역전_에러(self) -> None:
        """출발일이 귀환일보다 뒤면 ValidationError가 발생한다."""
        from oneerp_expenses_app.models.travel_request import TravelRequestCreate

        with pytest.raises(ValidationError, match="출발일은 귀환일 이전이어야 합니다"):
            TravelRequestCreate(
                employee_id="EMP-001",
                departure_date=date(2026, 4, 10),
                return_date=date(2026, 4, 5),
            )

    def test_출발일_귀환일_같은날_정상(self) -> None:
        """당일 출장(출발일 == 귀환일)은 허용된다."""
        from oneerp_expenses_app.models.travel_request import TravelRequestCreate

        req = TravelRequestCreate(
            employee_id="EMP-001",
            departure_date=date(2026, 4, 10),
            return_date=date(2026, 4, 10),
        )
        assert req.departure_date == req.return_date

    def test_출발일만_있고_귀환일_없으면_정상(self) -> None:
        """귀환일이 없으면 검증을 건너뛴다."""
        from oneerp_expenses_app.models.travel_request import TravelRequestCreate

        req = TravelRequestCreate(
            employee_id="EMP-001",
            departure_date=date(2026, 4, 10),
        )
        assert req.return_date is None

    def test_귀환일만_있고_출발일_없으면_정상(self) -> None:
        """출발일이 없으면 검증을 건너뛴다."""
        from oneerp_expenses_app.models.travel_request import TravelRequestCreate

        req = TravelRequestCreate(
            employee_id="EMP-001",
            return_date=date(2026, 4, 10),
        )
        assert req.departure_date is None

    def test_정상_출장기간(self) -> None:
        """출발일 < 귀환일인 정상 케이스."""
        from oneerp_expenses_app.models.travel_request import TravelRequestCreate

        req = TravelRequestCreate(
            employee_id="EMP-001",
            departure_date=date(2026, 4, 1),
            return_date=date(2026, 4, 5),
        )
        assert req.departure_date is not None
        assert req.return_date is not None
        assert req.departure_date < req.return_date

    def test_생성_API에서_날짜역전_422(self) -> None:
        """API 레벨에서도 날짜 역전 시 422를 반환한다."""
        response = client.post(
            "/api/v1/travel-requests/",
            json={
                "employee_id": "EMP-001",
                "departure_date": "2026-04-10",
                "return_date": "2026-04-05",
            },
        )
        assert response.status_code == 422
