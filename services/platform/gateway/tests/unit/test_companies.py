"""회사(Company) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.companies import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)
client_no_raise = TestClient(_app, raise_server_exceptions=False)

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.companies._get_repo")
@patch("oneerp_gateway_app.routes.companies.generate_name", return_value="COMP-2026-00001")
def test_회사_생성은_프로필필드와_기본회사설정을_저장한다(
    mock_name: MagicMock, mock_repo: MagicMock
) -> None:
    """회사 생성 시 프로필 필드와 기본 회사 여부를 함께 저장해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/companies",
        json={
            "company_name": "알파 주식회사",
            "abbr": "ALP",
            "company_code": "alpha hq",
            "business_registration_number": "123-45-67890",
            "representative_name": "김대표",
            "address": "서울시 강남구 테헤란로 1",
            "default_currency": "KRW",
            "country": "KR",
            "fiscal_year_start": "01-01",
            "is_default": True,
        },
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 201
    inserted = repo.insert.call_args.args[0]
    assert inserted.company_code == "ALPHA-HQ"
    assert inserted.business_registration_number == "123-45-67890"
    assert inserted.representative_name == "김대표"
    assert inserted.address == "서울시 강남구 테헤란로 1"
    assert inserted.is_default is True


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_회사_목록은_워크벤치_요약과_상태배지를_반환한다(mock_repo: MagicMock) -> None:
    """회사 목록은 멀티컴퍼니 운영 요약과 상태 배지를 제공해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "COMP-001",
            "company_name": "알파 홀딩스",
            "company_code": "ALPHA-HQ",
            "abbr": "ALP",
            "parent_company_id": "",
            "is_default": True,
            "is_active": True,
            "default_currency": "KRW",
        },
        {
            "_id": "COMP-002",
            "company_name": "알파 부산사업장",
            "company_code": "ALPHA-BSN",
            "abbr": "ABS",
            "parent_company_id": "COMP-001",
            "is_default": False,
            "is_active": True,
            "default_currency": "KRW",
        },
        {
            "_id": "COMP-003",
            "company_name": "알파 휴면법인",
            "company_code": "ALPHA-OLD",
            "abbr": "AOL",
            "parent_company_id": "",
            "is_default": False,
            "is_active": False,
            "default_currency": "USD",
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/companies", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["summary"] == {
        "total_company_count": 3,
        "active_company_count": 2,
        "inactive_company_count": 1,
        "default_company_count": 1,
        "root_company_count": 2,
        "branch_company_count": 1,
    }
    assert payload["data"][0]["status_badge"] == "default_company"
    assert payload["data"][0]["recommended_action"] == "review_company_tree"
    assert "create_branch_company" in payload["data"][0]["available_actions"]
    assert payload["data"][1]["status_badge"] == "branch_company"
    assert payload["data"][2]["status_badge"] == "inactive"


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_회사_상세는_계층요약과_권장액션을_반환한다(mock_repo: MagicMock) -> None:
    """회사 상세는 기본/상위/하위 구조 요약과 권장 액션을 제공해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "COMP-001",
        "company_name": "알파 홀딩스",
        "company_code": "ALPHA-HQ",
        "abbr": "ALP",
        "parent_company_id": "",
        "is_default": True,
        "is_active": True,
        "default_currency": "KRW",
    }
    repo.find_many.return_value = [
        repo.find_by_id.return_value,
        {
            "_id": "COMP-002",
            "company_name": "알파 부산사업장",
            "company_code": "ALPHA-BSN",
            "abbr": "ABS",
            "parent_company_id": "COMP-001",
            "is_default": False,
            "is_active": True,
            "default_currency": "KRW",
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/companies/COMP-001", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "default_company"
    assert payload["hierarchy_summary"] == {
        "is_default": True,
        "is_active": True,
        "is_root": True,
        "parent_company_id": "",
        "child_company_count": 1,
        "child_company_ids": ["COMP-002"],
        "default_currency": "KRW",
    }
    assert payload["recommended_action"] == "review_company_tree"
    assert "delete" not in payload["available_actions"]


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_회사_트리는_상하위_법인구조와_기본회사를_반환한다(mock_repo: MagicMock) -> None:
    """멀티컴퍼니 화면은 회사 계층과 기본 회사를 한 번에 조회해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "COMP-001",
            "company_name": "알파 홀딩스",
            "company_code": "ALPHA-HQ",
            "abbr": "ALP",
            "parent_company_id": "",
            "is_default": True,
            "is_active": True,
            "default_currency": "KRW",
        },
        {
            "_id": "COMP-002",
            "company_name": "알파 부산사업장",
            "company_code": "ALPHA-BSN",
            "abbr": "ABS",
            "parent_company_id": "COMP-001",
            "is_default": False,
            "is_active": True,
            "default_currency": "KRW",
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/companies/tree", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["default_company_id"] == "COMP-001"
    assert payload["summary"]["branch_company_count"] == 1
    assert payload["data"][0]["company_code"] == "ALPHA-HQ"
    assert payload["data"][0]["children"][0]["company_code"] == "ALPHA-BSN"


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_기본회사_전환은_기존_기본회사를_해제한다(mock_repo: MagicMock) -> None:
    """기본 회사 전환 시 기존 기본 회사를 해제해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "COMP-002",
        "company_name": "알파 부산사업장",
        "company_code": "ALPHA-BSN",
        "is_default": False,
    }
    repo.find_many.return_value = [
        {
            "_id": "COMP-001",
            "company_name": "알파 홀딩스",
            "company_code": "ALPHA-HQ",
            "is_default": True,
        }
    ]
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/companies/COMP-002/set-default",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    repo.update_by_id.assert_any_call(
        "COMP-001", {"is_default": False, "updated_by": "tenant-admin"}
    )
    repo.update_by_id.assert_any_call(
        "COMP-002", {"is_default": True, "updated_by": "tenant-admin"}
    )


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_하위법인이_있는_회사는_삭제할_수_없다(mock_repo: MagicMock) -> None:
    """상위 회사 삭제는 하위 법인이 모두 정리된 뒤에만 허용해야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "COMP-001",
        "company_name": "알파 홀딩스",
        "company_code": "ALPHA-HQ",
        "is_default": False,
    }
    repo.count.return_value = 1
    mock_repo.return_value = repo

    response = client_no_raise.delete(
        "/api/v1/companies/COMP-001",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "하위 회사가 연결된 회사는 삭제할 수 없습니다"
    repo.delete_by_id.assert_not_called()


@patch("oneerp_gateway_app.routes.companies._get_repo")
def test_기본회사는_다른_회사를_기본값으로_전환한_뒤에만_삭제할_수_있다(
    mock_repo: MagicMock,
) -> None:
    """기본 회사는 대체 기본값 없이 삭제할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "COMP-001",
        "company_name": "알파 홀딩스",
        "company_code": "ALPHA-HQ",
        "is_default": True,
    }
    repo.count.return_value = 0
    repo.find_many.return_value = [
        {"_id": "COMP-001", "is_default": True},
        {"_id": "COMP-002", "is_default": False},
    ]
    mock_repo.return_value = repo

    response = client_no_raise.delete(
        "/api/v1/companies/COMP-001",
        headers=TENANT_ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "기본 회사는 다른 회사를 기본값으로 전환한 뒤 삭제할 수 있습니다"
    )
    repo.delete_by_id.assert_not_called()
