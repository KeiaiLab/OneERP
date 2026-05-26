"""통화(Currency) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.currencies import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 — currencies 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.currencies._get_repo")
@patch("oneerp_gateway_app.routes.currencies.generate_name", return_value="CUR-2026-00001")
def test_통화_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 통화를 생성하면 201을 반환하고 코드를 정규화한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/currencies/",
        json={"currency_code": " usd ", "currency_name": "미국 달러"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["currency_id"] == "CUR-2026-00001"
    inserted_doc = repo.insert.call_args.args[0]
    assert inserted_doc.currency_code == "USD"


@patch("oneerp_gateway_app.routes.currencies._get_repo")
def test_통화_목록_조회(mock_repo: MagicMock) -> None:
    """통화 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "CUR-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/currencies/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.currencies._get_repo")
def test_통화_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 통화 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/currencies/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.currencies._get_repo")
def test_통화_카탈로그는_활성통화만_정렬하고_요약을_반환한다(mock_repo: MagicMock) -> None:
    """활성 통화만 코드순으로 반환하고 요약 정보를 포함해야 한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "CUR-USD",
            "currency_code": "USD",
            "currency_name": "US Dollar",
            "is_enabled": True,
        },
        {"_id": "CUR-EUR", "currency_code": "EUR", "currency_name": "Euro", "is_enabled": False},
        {
            "_id": "CUR-KRW",
            "currency_code": "KRW",
            "currency_name": "Korean Won",
            "is_enabled": True,
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/currencies/catalog", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert [item["currency_code"] for item in payload["data"]] == ["KRW", "USD"]
    assert payload["summary"] == {
        "default_currency_code": "KRW",
        "enabled_count": 2,
        "disabled_count": 1,
    }


@patch("oneerp_gateway_app.routes.currencies._get_repo")
def test_KRW_기본통화는_비활성화와_삭제가_차단된다(mock_repo: MagicMock) -> None:
    """기본 통화 KRW는 비활성화하거나 삭제할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "CUR-KRW",
        "currency_code": "KRW",
        "currency_name": "한국 원",
        "is_enabled": True,
    }
    mock_repo.return_value = repo

    disable_response = client.put(
        "/api/v1/currencies/CUR-KRW",
        json={"is_enabled": False},
        headers=TENANT_ADMIN_HEADERS,
    )
    delete_response = client.delete("/api/v1/currencies/CUR-KRW", headers=TENANT_ADMIN_HEADERS)

    assert disable_response.status_code == 422
    assert delete_response.status_code == 422


@patch("oneerp_gateway_app.routes.currencies._get_system_settings_repo")
@patch("oneerp_gateway_app.routes.currencies._get_company_repo")
@patch("oneerp_gateway_app.routes.currencies._get_repo")
def test_사용중인_통화는_삭제할_수없다(
    mock_repo: MagicMock,
    mock_company_repo: MagicMock,
    mock_system_settings_repo: MagicMock,
) -> None:
    """회사나 시스템 설정에서 참조 중인 통화는 삭제할 수 없어야 한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "CUR-USD",
        "currency_code": "USD",
        "currency_name": "US Dollar",
        "is_enabled": True,
    }
    mock_repo.return_value = repo
    mock_company_repo.return_value.count.return_value = 1
    mock_system_settings_repo.return_value.count.return_value = 0

    response = client.delete("/api/v1/currencies/CUR-USD", headers=TENANT_ADMIN_HEADERS)

    assert response.status_code == 422
    assert (
        response.json()["detail"] == "회사 또는 시스템 설정에서 사용 중인 통화는 삭제할 수 없습니다"
    )
